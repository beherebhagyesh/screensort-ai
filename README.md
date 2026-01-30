# ScreenSort AI

**ScreenSort AI** is an intelligent, privacy-first mobile application that transforms your chaotic screenshot folder into an organized, searchable vault. Running locally on your device (via Termux/Android), it uses OCR and AI categorization to sort images, extract data, and provide insights without your data ever leaving your phone.

![Status](https://img.shields.io/badge/Status-Beta-blue?style=for-the-badge)
![Tech](https://img.shields.io/badge/Tech-Python%20%7C%20Moondream2%20%7C%20SQLite-green?style=for-the-badge)

## Features

### 1. Smart Auto-Organization
Automatically moves screenshots from your main folder into context-aware categories:
- **Finance:** Banks, receipts, transactions
- **Shopping:** Amazon, orders, carts
- **Chats:** WhatsApp, Telegram, DMs
- **Code:** Snippets, errors, terminal logs
- **Social:** Instagram, Twitter/X posts
- **System, Events, Food, Travel** and more

### 2. AI Visual Intelligence
Go beyond text matching with a local **Vision-Language Model (VLM)**.
- **Moondream2 Integration:** Uses a lightweight LLM (~3GB) to "see" images and categorize them based on visual context
- **Smart Narratives:** Generates natural language descriptions of your screenshots
- **AI-Powered OCR:** Replace buggy pytesseract with accurate AI text extraction

### 3. Full-Text Search (Enhanced OCR)
- **Intelligent Pipeline:** Grayscale -> 2x Upscaling -> Contrast Boost -> Sharpening
- **AI OCR Fallback:** When pytesseract fails, AI reads the text accurately
- **Deep Indexing:** Text indexed in SQLite for instant search

### 4. Video Analysis
Analyze screen recordings and video files frame-by-frame.
- **Frame Extraction:** Captures frames at configurable intervals (default: 5s)
- **Object Detection:** Identifies people, objects, and activities in each frame
- **Smart Categorization:** Aggregates frame analysis to categorize videos

### 5. Auto-Translation
Automatically detect and translate text from screenshots.
- **Language Detection:** Identifies Tamil, Hindi, Spanish, and 50+ languages
- **Auto-Translate:** Converts foreign text to English (or any target language)
- **Preserved Original:** Keeps original OCR text alongside translation

### 6. Insights & Analytics
- **Spending Tracker:** Detects amounts ($, Rs, EUR, GBP) from receipts
- **Visual Dashboard:** Storage usage, category breakdowns, recent activity

### 7. Web UI
- **Dark Mode** by default
- **Glassmorphism** aesthetic with neon accents
- **Responsive Web Viewer** accessible from any browser on your local network

---

## CLI Reference

```bash
python sort_screenshots.py [OPTIONS]
```

| Flag | Description |
|------|-------------|
| `--ai` | Enable Moondream2 AI for visual categorization |
| `--ai-ocr` | Use AI for text extraction (better than pytesseract) |
| `--video` | Enable video frame-by-frame analysis |
| `--translate` | Enable auto-translation of OCR text |
| `--target-lang XX` | Target language code (default: `en`) |
| `--interval N` | Scan interval in seconds (default: `60`) |

### Examples

```bash
# Basic OCR-only mode
python sort_screenshots.py

# AI visual analysis + categorization
python sort_screenshots.py --ai

# Full features: AI + better OCR + Video + Translation
python sort_screenshots.py --ai --ai-ocr --video --translate

# Translate to Hindi instead of English
python sort_screenshots.py --ai --translate --target-lang hi

# Fast scanning (every 30 seconds)
python sort_screenshots.py --ai --interval 30
```

---

## Architecture

```
Screenshot Folder --> [Python Service] --> Sorted Folders
                           |
                           v
                    [SQLite Database]
                           |
                           v
                    [Web Interface]
```

### Directory Structure
```
/home
├── sort_screenshots.py      # Main processor (OCR + AI + Video + Translation)
├── screenshots.db           # SQLite database with all metadata
├── smart_processor.py       # [DEPRECATED] Standalone AI processor
├── download_model.py        # Downloads Moondream2 model files
├── models/                  # AI model files (GGUF format)
└── screenshot-viewer/       # Web application
    ├── server.js            # Express backend
    ├── db_bridge.py         # Python-SQLite bridge
    └── public/              # Frontend (HTML/Tailwind)
```

### Database Schema
```sql
screenshots (
    id, filename, path, category, text, amount,
    created_at, processed_at,
    ai_category, ai_summary, ai_processed_at,
    detected_language, translated_text,
    is_video, video_frames_analyzed, video_objects,
    ocr_method, ai_extracted_text
)
```

---

## Getting Started

### Prerequisites
- Android Device with **Termux**
- **Python 3.10+**
- **Tesseract OCR** (`pkg install tesseract`)
- **Node.js** (for web viewer)

### Installation

1. **Clone the Repo**
   ```bash
   git clone https://github.com/beherebhagyesh/screensort-ai.git
   cd screensort-ai
   ```

2. **Install Core Dependencies**
   ```bash
   pip install pytesseract Pillow
   ```

3. **Install Optional Features**
   ```bash
   # AI Analysis (Moondream2)
   pip install llama-cpp-python
   python download_model.py

   # Video Frame Analysis
   pip install opencv-python

   # Translation
   pip install langdetect googletrans==4.0.0-rc1
   ```

4. **Start the Service**
   ```bash
   # Recommended: Full features
   nohup python sort_screenshots.py --ai --ai-ocr --translate &
   ```

5. **Launch Web Viewer** (Optional)
   ```bash
   cd screenshot-viewer
   npm install
   node server.js
   # Open http://localhost:4000
   ```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCREENSORT_AI` | `0` | Enable AI (`1` to enable) |
| `SCREENSORT_AI_OCR` | `0` | Enable AI-based OCR |
| `SCREENSORT_VIDEO` | `0` | Enable video analysis |
| `SCREENSORT_TRANSLATE` | `0` | Enable translation |

---

## Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

MIT

## Author

**beherebhagyesh**
