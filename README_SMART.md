# Smart Screenshot Processor (Moondream2 + OCR)

This module uses a Visual Language Model (Moondream2) and OCR (Tesseract) to analyze, categorize, and document your screenshots automatically.

## Features
1.  **Visual Categorization:** Uses `moondream2` to "see" the image and determine if it's a Chat, Receipt, Code, etc.
2.  **Text Extraction:** Uses `pytesseract` to read all text from the image.
3.  **Reporting:** Generates a Markdown report (`smart_report.md`) acting as a searchable knowledge base.

## Setup
1.  **Models:** Ensure `models/moondream2-text-model-f16.gguf` and `models/moondream2-mmproj-f16.gguf` exist.
2.  **Dependencies:** `pip install llama-cpp-python pytesseract pillow`

## Usage
Run the processor:
```bash
python smart_processor.py
```

## Output
Check `smart_report.md` for the results.

## Configuration
Edit `smart_processor.py` to change:
-   `SOURCE_DIR`: Directory to scan.
-   `LIMIT`: Number of images to process per run.
