import fitz
import pytesseract
import io
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 改成你要測試的檔案路徑
PDF_PATH = r"C:\path\to\your\pdf"

doc = fitz.open(PDF_PATH)
pix = doc[0].get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
img = Image.open(io.BytesIO(pix.tobytes("png")))

text = pytesseract.image_to_string(img, lang="chi_tra+eng")
print("=== OCR 結果 ===")
print(text)
