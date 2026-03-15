# Plan: Thumbnail Generation

## Phase 1: Backend Generation

- [ ] **Step 1: Update `sort_screenshots.py`**
    - [ ] Add `generate_thumbnail` function.
    - [ ] Update `process_files` to generate thumbnail.
    - [ ] Add `process_thumbnail_backfill`.
    - [ ] Call backfill in loop.

- [ ] **Step 2: Update `server.js`**
    - [ ] Serve `.thumbs` directory at `/thumbnails`.

## Phase 2: Frontend Integration

- [ ] **Step 3: Update `index.html`**
    - [ ] Update image paths in Grid and Recent lists to point to `/thumbnails/...`.
    - [ ] Add error handling to fall back to full image if thumbnail missing.

## Phase 3: Verification

- [ ] **Step 4: Test**
    - [ ] Run backfill.
    - [ ] Verify files in `.thumbs`.
    - [ ] Check web UI network tab for thumbnail requests.
