# Specification: PWA and Background Processing

## Overview
This track aims to transform the screenshot viewer into a Progressive Web App (PWA) and ensure the screenshot sorting script runs continuously in the background.

## Requirements

### 1. Progressive Web App (PWA)
- **Manifest:** Create a `manifest.json` with appropriate icons, theme colors, and display properties.
- **Service Worker:** Implement a basic service worker to enable offline viewing and caching of assets.
- **Installability:** Ensure the app meets PWA installability criteria so users are prompted to "Add to Home Screen".
- **Visuals:** Implement a dark-mode Material Design theme as per `product-guidelines.md`.

### 2. Background Processing
- **Persistence:** Ensure `sort_screenshots.py` runs automatically and restarts if it fails.
- **Mechanism:** Use a robust background execution method suitable for the environment (e.g., a loop with sleep, or a system-level service like `systemd` or `cron` if appropriate for Termux).
- **Monitoring:** Implement basic logging or status reporting so the viewer can eventually show the processing status.

## Success Criteria
- The viewer can be installed to the Android home screen.
- Screenshots are automatically categorized without manual script execution.
- The web UI follows the dark Material Design theme.
