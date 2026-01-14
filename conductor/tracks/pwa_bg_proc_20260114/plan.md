# Plan: PWA and Background Processing

## Phase 1: Background Processing Setup
Goal: Ensure the sorting script runs continuously and reliably in the background.

- [x] Task: Update `sort_screenshots.py` to support continuous monitoring (e.g., infinite loop with configurable delay). <!-- 713ea54 -->
- [x] Task: Implement a startup script or service configuration for Termux to ensure the background process starts on boot or environment entry. <!-- 7f5366b -->
- [ ] Task: Add logging to `sort_screenshots.py` to track processing activity.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Background Processing Setup' (Protocol in workflow.md)

## Phase 2: PWA Implementation
Goal: Enable PWA features for the Express-based viewer.

- [ ] Task: Create `public/manifest.json` with PWA metadata (icons, colors, display).
- [ ] Task: Implement `public/service-worker.js` for asset caching and offline support.
- [ ] Task: Register the Service Worker in the main HTML file.
- [ ] Task: Update the UI to include a "Install App" prompt or ensure the browser's native prompt is correctly triggered.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: PWA Implementation' (Protocol in workflow.md)

## Phase 3: Visual Polish (Dark Material Design)
Goal: Align the UI with the product guidelines.

- [ ] Task: Implement a dark Material Design theme using CSS.
- [ ] Task: Ensure the layout is fully responsive and optimized for mobile touch targets (44x44px).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Visual Polish (Dark Material Design)' (Protocol in workflow.md)
