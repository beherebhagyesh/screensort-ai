# Specification: Thumbnail Generation

## 1. Overview
Loading full-resolution screenshots in the gallery grid is slow and consumes bandwidth. This feature introduces automatic thumbnail generation to speed up the UI.

## 2. Requirements
- **Generation:** Create a compressed JPEG thumbnail (max 300px dimension) for each screenshot.
- **Storage:** Store thumbnails in a parallel directory structure: `SOURCE_DIR/.thumbs/Category/filename`.
- **Serving:** Expose the `.thumbs` directory via the web server at `/thumbnails`.
- **UI:** The gallery view should load images from `/thumbnails/...` instead of `/images/...`.
- **Backfill:** Automatically generate thumbnails for existing images.

## 3. Technical Implementation
### `sort_screenshots.py`
- Function `generate_thumbnail(src_path, category)`.
    - Dest: `SOURCE_DIR/.thumbs/{category}/{filename}`.
    - Resize to 300x300 (contain).
    - Save as JPEG (quality 70).
- Update `process_files`: Call generation after move.
- Update `process_phash_backfill` or add specific `process_thumbnail_backfill`. *Decision: Add specific backfill.*

### `server.js`
- Add `app.use('/thumbnails', express.static(path.join(SCREENSHOTS_DIR, '.thumbs')));`

### `index.html`
- Update `renderDashboard` (Recent files) and `openCategory` (Gallery grid).
- Construct thumbnail URL: `/thumbnails/{Category}/{filename}`.
- Fallback: If thumbnail fails to load, load original? (img `onerror` handler).

## 4. Acceptance Criteria
- [ ] Thumbnails are generated for new screenshots.
- [ ] Thumbnails are generated for existing screenshots (backfill).
- [ ] Web UI loads thumbnails in the grid.
- [ ] Full image loads when clicking the thumbnail.
