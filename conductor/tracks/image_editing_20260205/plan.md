# Plan: Image Editing Tools

## Phase 1: Backend

- [ ] **Step 1: Update `db_bridge.py`**
    - [ ] Import `base64`.
    - [ ] Add `save_image_data(filename, b64_data)`.
    - [ ] Decode and write file.
    - [ ] Call `generate_thumbnail`.

- [ ] **Step 2: Update `server.js`**
    - [ ] Add `POST /api/save-image`. Increase body size limit if needed (default express JSON limit is small).

## Phase 2: Frontend

- [ ] **Step 3: Update `index.html`**
    - [ ] Add "Edit" button to Image Viewer.
    - [ ] Add Editor Modal (Canvas, Toolbar).
    - [ ] Implement Editor Logic (Crop, Blur, Save).

## Phase 3: Verification

- [ ] **Step 4: Test**
    - [ ] Edit an image via UI.
    - [ ] Verify file change on disk.
