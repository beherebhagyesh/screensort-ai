# Scope & Roadmap: ScreenSort AI

## ✅ Achieved
1.  **Core Automation:** Background service (`sort_screenshots.py`) that monitors and sorts screenshots into folders based on keyword OCR.
2.  **User Interface:** A PWA-ready Web Viewer (Node.js/Express) to browse sorted images.
3.  **AI Integration (Beta):** `smart_processor.py` successfully utilizes **Moondream2** (local VLM) to visually categorize images and **Tesseract** to extract text.
4.  **Documentation:** Release notes, README with AI setup, and technical architecture.

## ✅ Recently Completed
1.  **Full Pipeline Integration:**
    *   AI analysis merged into `sort_screenshots.py` - run with `--ai` flag
    *   Automatic backfill for existing screenshots
    *   AI results stored in SQLite database (ai_category, ai_summary)
2.  **Bug Fixes:**
    *   Fixed amount extraction regex (now captures $, £, €, ₹, Rs)
    *   Normalized category names across OCR and AI systems

## 🚧 Discussed & Pending (To-Do)
1.  **Structured Knowledge Base:**
    *   *Current State:* AI summaries stored in database.
    *   *Goal:* Export to dedicated `knowledge_base/` folder with separate markdown files.

## 🔮 Ancillary Features (New Requests)
1.  **Multi-Source Scanning:**
    *   *Goal:* Extend scanning beyond `Screenshots` to include `Downloads`, `WhatsApp Images`, `Twitter`, and `Documents` (for image-based PDFs/scans).
    *   *Reasoning:* Important text often lives in downloaded receipts or saved memes, not just screenshots.
2.  **Video/Media Handling:**
    *   *Goal:* Better handling of video files (currently just moved to "Videos", but no content analysis).
3.  **Cross-Device Sync:**
    *   *Goal:* Sync the `knowledge_base` markdown files to a private git repo for backup.
