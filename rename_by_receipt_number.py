"""
掃描PDF自動改檔名工具（依發文字號）
====================================
功能：
  1. 掃描資料夾內所有 PDF
  2. 對第一頁全頁做 OCR
  3. 抓「字第XXXXXX號」的數字當檔名
  4. 偵測到「臺南市政府」或「嘉義市政府」→ 移到對應子資料夾
  5. 無法辨識的移到 _待人工確認 資料夾
  6. 輸出 log

安裝需求：
  pip install pymupdf pytesseract pillow
  Tesseract OCR + Traditional Chinese 語言包
"""

import re
import shutil
import logging
from pathlib import Path
from datetime import datetime

# ── 請依你的環境修改 ─────────────────────────────────────────
PDF_FOLDER     = r"C:\path\to\your\pdf\folder"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ── 收文號格式設定 ────────────────────────────────────────────
MIN_DIGITS = 8
MAX_DIGITS = 13

# ── 年份過濾（開頭三碼範圍，民國年）────────────────────────
YEAR_MIN = 100
YEAR_MAX = 116

# ── 分類規則（關鍵字 → 子資料夾名稱）────────────────────────
# 可自行新增，例如 "嘉義縣政府": "_嘉義縣"
CATEGORY_RULES = {
    "臺南市政府": "_臺南市",
    "台南市政府": "_臺南市",
    "tainan.gov": "_臺南市",
    "嘉義市政府": "_嘉義市",
    "chiayi.gov": "_嘉義市",
    "嘉義縣政府": "_嘉義縣",
    "cyhg.gov": "_嘉義縣",
}

# ── 進階設定 ─────────────────────────────────────────────────
DPI  = 300
LANG = "chi_tra+eng"

# ─────────────────────────────────────────────────────────────

def setup():
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    log_path = Path(PDF_FOLDER) / f"rename_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.info("=== 開始處理 ===")


def pdf_to_image(pdf_path):
    import fitz
    from PIL import Image
    import io
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    mat = fitz.Matrix(DPI / 72, DPI / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    doc.close()
    return img


def ocr_image(img):
    import pytesseract
    return pytesseract.image_to_string(img, lang=LANG, config="--psm 6")


def clean_ocr_text(text):
    """清洗 OCR 常見誤辨字元"""
    return (text
        .replace("I", "1")   # 大寫I → 1
        .replace("l", "1")   # 小寫l → 1
        .replace("O", "0")   # 大寫O → 0
        .replace("o", "0")   # 小寫o → 0（數字區域）
        .replace("|", "1")   # 豎線  → 1
    )


def is_valid_number(n):
    """檢查數字是否符合位數與年份開頭條件"""
    if not (MIN_DIGITS <= len(n) <= MAX_DIGITS):
        return False
    if not n[:3].isdigit():
        return False
    return YEAR_MIN <= int(n[:3]) <= YEAR_MAX


def extract_receipt_number(text):
    """
    四階段擷取：
    1. 案號：XXXXXX
    2. 發文字號同行的「字第...號」
    3. 發文字號跨行的「字第...號」
    4. 純數字 fallback（移除括號內容後，符合年份開頭）
    """
    # 先清洗 OCR 常見誤辨字元
    text = clean_ocr_text(text)

    # 階段1：案號（有標籤但抓不到數字 → 直接回傳特殊值，丟人工確認）
    if re.search(r'案\s*[號号]\s*[:：]', text):
        m = re.search(r'案\s*[號号]\s*[:：]\s*(\d{8,13})', text)
        if m and is_valid_number(m.group(1)):
            return m.group(1)
        return "MANUAL"  # 有案號標籤但抓不到 → 丟人工確認

    # 階段2：發文字號同行
    m = re.search(r'發文字[號号].{0,40}字第\s*(\d{8,13})\s*號', text)
    if m and is_valid_number(m.group(1)):
        return m.group(1)

    # 階段3：發文字號跨行
    m = re.search(r'發文字[號号][\s\S]{0,60}字第\s*(\d{8,13})\s*號', text)
    if m and is_valid_number(m.group(1)):
        return m.group(1)

    # 階段4：純數字 fallback（先移除括號內容）
    text_clean = re.sub(r'\([^)]*\)', '', text)
    candidates = [n for n in re.findall(r'(?<!\d)(\d{8,13})(?!\d)', text_clean) if is_valid_number(n)]
    if candidates:
        return max(candidates, key=len)

    return None


def detect_category(text):
    for keyword, folder_name in CATEGORY_RULES.items():
        if keyword in text:
            return folder_name
    return None


def process_pdf(pdf_path, used_names, folder, manual_folder):
    try:
        img  = pdf_to_image(pdf_path)
        text = ocr_image(img)

        receipt_number = extract_receipt_number(text)
        logging.info(f"  OCR擷取結果：{repr(receipt_number)}")

        if not receipt_number or receipt_number == "MANUAL":
            reason = "有案號標籤但辨識失敗" if receipt_number == "MANUAL" else "找不到收文號"
            shutil.move(str(pdf_path), str(manual_folder / pdf_path.name))
            return False, f"{reason}，已移至 _待人工確認"

        category = detect_category(text)
        target_folder = (folder / category) if category else folder
        if category:
            target_folder.mkdir(exist_ok=True)

        # 處理重複檔名
        new_name = receipt_number
        counter  = 2
        while new_name in used_names:
            new_name = f"{receipt_number}({counter})"
            counter += 1
        used_names.add(new_name)

        new_path = target_folder / f"{new_name}.pdf"
        if target_folder == folder:
            pdf_path.rename(new_path)
        else:
            shutil.move(str(pdf_path), str(new_path))

        result = f"{new_name}.pdf" + (f"  → {category}/" if category else "")
        return True, result

    except Exception as e:
        try:
            shutil.move(str(pdf_path), str(manual_folder / pdf_path.name))
            return False, f"錯誤：{e}，已移至 _待人工確認"
        except Exception:
            return False, f"錯誤：{e}"


def main():
    setup()

    folder = Path(PDF_FOLDER)
    if not folder.exists():
        logging.error(f"資料夾不存在：{PDF_FOLDER}")
        return

    manual_folder = folder / "_待人工確認"
    manual_folder.mkdir(exist_ok=True)

    pdf_files = sorted(folder.glob("*.pdf"))
    total = len(pdf_files)
    logging.info(f"共找到 {total} 個 PDF 檔案")

    if total == 0:
        logging.warning("沒有找到任何 PDF，請確認資料夾路徑是否正確")
        return

    success_count = 0
    fail_count    = 0
    used_names    = set()

    for i, pdf_path in enumerate(pdf_files, 1):
        logging.info(f"[{i}/{total}] 處理中：{pdf_path.name}")
        ok, result = process_pdf(pdf_path, used_names, folder, manual_folder)
        if ok:
            logging.info(f"  ✓ {result}")
            success_count += 1
        else:
            logging.warning(f"  ✗ {result}")
            fail_count += 1

    logging.info("=" * 40)
    logging.info(f"完成！成功：{success_count} 件 / 失敗：{fail_count} 件")
    if fail_count > 0:
        logging.info(f"失敗檔案請至 [_待人工確認] 資料夾人工處理")


if __name__ == "__main__":
    main()
