# Scope & Roadmap: ScreenSort AI

## ✅ Achieved
1.  **Core Automation:** Background service (`sort_screenshots.py`) that monitors and sorts screenshots into folders based on keyword OCR.
2.  **User Interface:** A PWA-ready Web Viewer (Node.js/Express) to browse sorted images.
3.  **AI Integration (Beta):** `smart_processor.py` successfully utilizes **Moondream2** (local VLM) to visually categorize images and **Tesseract** to extract text.
4.  **Documentation:** Release notes, README with AI setup, and technical architecture.

## 🚧 Discussed & Pending (To-Do)
1.  **Full Pipeline Integration:** 
    *   *Current State:* `smart_processor.py` is a standalone script.
    *   *Goal:* Merge AI analysis into the main `sort_screenshots.py` loop so every *new* screenshot is automatically analyzed by Moondream2 without manual intervention.
2.  **Structured Knowledge Base:**
    *   *Current State:* Generates a single `smart_report.md`.
    *   *Goal:* Create a dedicated `knowledge_base/` folder with separate files (e.g., `Finance.md`, `Recipes.md`) effectively treating your screenshot collection as a personal wiki.

## 🔮 Ancillary Features (New Requests)
1.  **Multi-Source Scanning:**
    *   *Goal:* Extend scanning beyond `Screenshots` to include `Downloads`, `WhatsApp Images`, `Twitter`, and `Documents` (for image-based PDFs/scans).
    *   *Reasoning:* Important text often lives in downloaded receipts or saved memes, not just screenshots.
2.  **Video/Media Handling:**
    *   *Goal:* Better handling of video files (currently just moved to "Videos", but no content analysis).
3.  **Cross-Device Sync:**
    *   *Goal:* Sync the `knowledge_base` markdown files to a private git repo for backup.
