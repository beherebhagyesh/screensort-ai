# ScreenSort AI 🧠✨

**ScreenSort AI** is an intelligent, privacy-first mobile application that transforms your chaotic screenshot folder into an organized, searchable vault. Running locally on your device (via Termux/Android), it uses OCR and AI categorization to sort images, extract data, and provide insights without your data ever leaving your phone.

![Status](https://img.shields.io/badge/Status-Beta-blue?style=for-the-badge)
![Tech](https://img.shields.io/badge/Tech-Python%20%7C%20Node.js%20%7C%20SQLite-green?style=for-the-badge)

## 📱 Features

### 1. 📂 Smart Auto-Organization
Automatically moves screenshots from your main folder into context-aware categories:
*   **Finance:** Banks, receipts, transactions.
*   **Shopping:** Amazon, orders, carts.
*   **Chats:** WhatsApp, Telegram, DMs.
*   **Code:** Snippets, errors, terminal logs.
*   **Social:** Instagram, Twitter/X posts.

### 2. 🔍 Full-Text Search (OCR)
Don't just look at images—read them.
*   Type "wifi password" or "flight ticket" to find the exact image instantly.
*   Text is indexed locally in SQLite for sub-second search speeds.

### 3. 📊 Insights & Analytics
*   **Spending Tracker:** Automatically detects and sums up dollar/rupee amounts from receipt screenshots.
*   **Visual Dashboard:** View storage usage, category breakdowns, and recent activity.

### 4. 🎨 Futuristic UI
*   **Dark Mode** by default.
*   **Glassmorphism** aesthetic with neon accents.
*   **Responsive Web Viewer** accessible from any browser on your local network.

---

## 🛠️ Architecture

The system consists of two main components running in parallel:

```mermaid
graph TD
    A[Screenshot Folder] -->|Watch & OCR| B(Python Background Service)
    B -->|Categorize & Move| C[Sorted Folders]
    B -->|Index Text & Data| D[(SQLite Database)]
    E[Web Interface (React/Node)] -->|Query via Bridge| D
    E -->|Serve Images| C
    U[User] -->|View & Search| E
```

### Directory Structure
```bash
/home
├── sort_screenshots.py      # The "Brain": OCR & File Management
├── screenshots.db           # The "Memory": Search Index
├── screenshot-viewer/       # The "Face": Web Application
│   ├── server.js            # Backend API
│   ├── db_bridge.py         # Database Connector
│   └── public/              # Frontend (HTML/Tailwind)
```

---

## 🚀 Getting Started

### Prerequisites
*   Android Device with **Termux**.
*   **Python 3.x** (with `Pillow`, `pytesseract`).
*   **Node.js** (LTS).
*   **Tesseract OCR** binary installed (`pkg install tesseract`).

### Installation

1.  **Clone the Repo**
    ```bash
    git clone https://github.com/beherebhagyesh/screensort-ai.git
    cd screensort-ai
    ```

2.  **Start the Background Service**
    This will begin organizing your existing screenshots immediately.
    ```bash
    nohup python3 sort_screenshots.py &
    ```

3.  **Launch the Viewer**
    ```bash
    cd screenshot-viewer
    npm install
    node server.js
    ```

4.  **Access the App**
    Open your browser and go to: `http://localhost:4000`

---

## 🖼️ Visuals

### Dashboard
*Clean, data-rich home screen with storage stats.*

### Search
*Instant results with highlighted text matching.*

---

## 🤝 Contributing
1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

**License:** MIT
**Author:** beherebhagyesh
