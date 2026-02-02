# Plan: PWA and Background Processing

## Phase 1: Background Processing Setup [checkpoint: 453ad6c]
Goal: Ensure the sorting script runs continuously and reliably in the background.

- [x] Task: Update `sort_screenshots.py` to support continuous monitoring (e.g., infinite loop with configurable delay). <!-- 713ea54 -->
- [x] Task: Implement a startup script or service configuration for Termux to ensure the background process starts on boot or environment entry. <!-- 7f5366b -->
- [x] Task: Add logging to `sort_screenshots.py` to track processing activity. <!-- 76e42d9 -->
- [x] Task: Conductor - User Manual Verification 'Phase 1: Background Processing Setup' (Protocol in workflow.md) <!-- 453ad6c -->

## Phase 2: PWA Implementation
Goal: Enable PWA features for the Express-based viewer.

- [x] Task: Create `public/manifest.json` with PWA metadata (icons, colors, display). <!-- 33798f6 -->
- [x] Task: Implement `public/service-worker.js` for asset caching and offline support. <!-- 33798f6 -->
- [x] Task: Register the Service Worker in the main HTML file. <!-- 33798f6 -->
- [x] Task: Update the UI to include a "Install App" prompt or ensure the browser's native prompt is correctly triggered. <!-- 33798f6 -->
- [ ] Task: Conductor - User Manual Verification 'Phase 2: PWA Implementation' (Protocol in workflow.md)

## Phase 3: Visual Polish & Feature Completion (Material Design)
Goal: Align the UI with the product guidelines and ensure full functionality.

- [~] Task: Create `public/styles.css` with Material Design 3 variables (colors, typography, elevation) to reduce reliance on external CDNs.
- [ ] Task: Refactor `index.html` to implement client-side routing/tab switching (Dashboard, Gallery, Settings).
- [ ] Task: Implement the **Gallery View** to list all screenshot categories/folders.
- [ ] Task: Implement the **Category Grid View** to display thumbnails of images within a selected category.
- [ ] Task: Implement a **Full-Screen Image Viewer** with details (OCR text, date, metadata).
- [ ] Task: Ensure the layout is fully responsive and optimized for mobile touch targets (44x44px).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Visual Polish (Dark Material Design)' (Protocol in workflow.md)
