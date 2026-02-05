# Specification: Image Editing Tools

## 1. Overview
Users often need to redact sensitive information (blur) or highlight important parts of a screenshot before sharing. This feature adds a basic image editor to the Web Viewer.

## 2. Requirements
- **Editor UI:**
    - "Edit" button in Image Viewer.
    - Canvas-based editor modal.
    - Tools: Crop, Blur (Redact), Highlight (Yellow pen).
- **Backend:**
    - `POST /api/save-image`
    - Saves the edited image (overwriting the original).
    - Regenerates thumbnail.
- **Workflow:**
    1. Open Image -> Click Edit.
    2. Image loads into Canvas.
    3. User performs edits.
    4. Click Save -> Uploads base64 -> Overwrites file -> Reloads Viewer.

## 3. Technical Implementation
### `server.js`
- `POST /api/save-image`: Body `{ filename, image_data_base64 }`.
- Call `db_bridge.py save_image_data`.

### `db_bridge.py`
- `save_image_data`:
    - Decode base64.
    - Save to `SOURCE_DIR/Category/filename`.
    - `generate_thumbnail`.

### `index.html`
- Editor Modal HTML.
- Canvas logic:
    - `drawImage`.
    - Mouse events for drawing/selecting.
    - **Blur:** Pixelate/Blur canvas area under selection.
    - **Crop:** Resize canvas to selection.
    - **Highlight:** `globalCompositeOperation = 'multiply'` or semi-transparent stroke.

## 4. Acceptance Criteria
- [ ] User can open editor.
- [ ] User can crop the image.
- [ ] User can blur a region.
- [ ] User can save changes (file is updated on disk).
- [ ] Thumbnail is updated.
