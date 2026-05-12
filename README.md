# 📄 PDF Auto-Rename & Classification Tool

Automatically extracts document reference numbers from scanned government PDF files using OCR, renames them accordingly, and sorts them into categorized folders.

---

## 📌 Background

When handling large batches of scanned PDF documents, manually reading each file to find the reference number and renaming it is time-consuming and error-prone. This tool automates the entire process.

---

## ✨ Features

- **OCR Recognition**: Uses Tesseract to extract text from scanned Traditional Chinese documents
- **Multi-Stage Extraction**: Tries case number → document reference number → barcode fallback, in order
- **OCR Error Correction**: Automatically fixes common misreads such as `I→1`, `l→1`, `O→0`
- **Auto Classification**: Detects issuing authority from document text and moves files to corresponding subfolders
- **Duplicate Handling**: Appends suffix automatically, e.g. `1130012379(2).pdf`
- **Fail-Safe**: Files that cannot be recognized are moved to a `_待人工確認` (manual review) folder
- **Execution Log**: Generates a timestamped log file on every run

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3 | Core language |
| [pymupdf](https://pymupdf.readthedocs.io/) | PDF to image conversion (no poppler needed) |
| [pytesseract](https://github.com/madmaze/pytesseract) | OCR text extraction |
| [Pillow](https://pillow.readthedocs.io/) | Image processing |
| Tesseract OCR | Traditional Chinese recognition engine |
| `re` (Regex) | Multi-stage text pattern matching |

---

## 📋 Extraction Logic

```
Scan first page of PDF
    │
    ▼
OCR full page → clean misread characters (I→1, l→1, O→0)
    │
    ├─ 1️⃣  Found「案號：」label?
    │       ├─ digits found  → use case number
    │       └─ no digits     → send to manual review immediately
    │
    ├─ 2️⃣  Found「發文字號：...字第...號」on same line? → use it
    │
    ├─ 3️⃣  Same pattern but split across lines?         → use it
    │
    ├─ 4️⃣  Barcode fallback
    │       (strip parenthesized content, filter by ROC year prefix 100–115)
    │
    └─ ❌  All stages failed → move to manual review folder
```

---

## 🚀 Installation & Usage

### 1. Install Tesseract OCR

Download the Windows installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).  
During installation, make sure to check **Traditional Chinese** under additional language packs.

### 2. Install Python packages

```bash
pip install pymupdf pytesseract pillow
```

### 3. Configure the script

Open `rename_by_receipt_number.py` and update these two lines:

```python
PDF_FOLDER     = r"C:\path\to\your\pdf\folder"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### 4. Run

```bash
python rename_by_receipt_number.py
```

---

## 💻 Execution Example

```
=== Start Processing ===
Total: 56 PDF files found

[1/56]  Processing: 0003761_20260505.pdf
  ✓ Renamed to: 1130668223.pdf

[2/56]  Processing: 0003767_20260505.pdf
  ✓ Renamed to: 1130012379.pdf  →  _臺南市/

[3/56]  Processing: 0003799_20260505.pdf
  ✓ Renamed to: 1090230738.pdf  →  _嘉義縣/

[4/56]  Processing: 0004230_20260505.pdf
  ✗ No reference number found → moved to _待人工確認

========================================
Done!  Success: 53  /  Failed: 3
Failed files are in [_待人工確認] for manual review
```

---

## 📁 Output Structure

```
PDF Folder/
  ├── 1130668223.pdf            ← renamed file
  ├── 1130012379.pdf
  ├── 1130012379(2).pdf         ← duplicate, auto-suffixed
  ├── _臺南市/
  │     └── 1130656497.pdf
  ├── _嘉義市/
  │     └── 1130131153.pdf
  ├── _嘉義縣/
  │     └── 1090230738.pdf
  ├── _待人工確認/
  │     └── unrecognized.pdf
  └── rename_log_20260512_114500.txt
```

---

## ⚙️ Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MIN_DIGITS` | 8 | Minimum digits in reference number |
| `MAX_DIGITS` | 13 | Maximum digits (allows for OCR misreads) |
| `YEAR_MIN` | 100 | Minimum ROC year prefix |
| `YEAR_MAX` | 115 | Maximum ROC year prefix |
| `DPI` | 300 | OCR resolution (higher = more accurate but slower) |
| `CATEGORY_RULES` | see code | Authority name → folder mapping, add as needed |

---

## ⚠️ Notes

- **Back up your files** before running — renaming cannot be automatically undone
- OCR accuracy depends on scan quality; 300 DPI or higher is recommended
- Spot-check a few results after each run to verify accuracy

---

## 📜 License

MIT License
