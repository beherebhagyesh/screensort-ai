# Product Guide

## Initial Concept
A Screenshot Management System consisting of a Python-based OCR sorting script and a Node.js Express-based viewer. The goal is to automatically categorize screenshots using OCR and provide a web-based interface to view them.

## Vision
To create a seamless and automated solution for organizing and retrieving screenshots, turning a cluttered gallery into a structured, searchable knowledge base. The system aims to be "set-and-forget" for background processing while offering an accessible and installable (PWA) frontend for consumption.

## Goals
-   **Automated Organization:** Eliminate manual sorting by intelligently categorizing screenshots based on their text content using OCR.
-   **Web-Based Access:** Provide a responsive and intuitive web interface to browse and manage the organized collection.
-   **Background Processing:** Ensure the Python sorting script runs reliably in the background without user intervention.
-   **Installability:** The web interface should be a Progressive Web App (PWA) that prompts users to "Save to Home Screen" for native-like access.
-   **Scalability:** Initially designed for personal use, with a roadmap to support general users with varied needs.

## Target Audience
-   **Primary:** The Developer (Personal Use) - tailored to specific workflows and screenshot habits.
-   **Secondary:** General Public - anyone struggling with screenshot clutter, particularly power users, developers, and researchers.

## Core Features
1.  **Smart Sorting Engine:** Python script utilizing `pytesseract` and `PIL` to extract text and move files into predefined categories (Finance, Chats, Shopping, Code/Tech, etc.).
2.  **Web Viewer:** Node.js/Express application serving a frontend to display images by category.
3.  **Search:** (Future) Full-text search capability over the extracted text data.
4.  **PWA Support:** `manifest.json` and Service Worker implementation to enable "Add to Home Screen" functionality and offline capabilities.
5.  **Background Service:** Configuration (e.g., systemd, cron, or PM2) to keep the sorting script active.
