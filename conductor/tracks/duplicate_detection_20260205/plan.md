# Plan: Duplicate Image Detection

## Phase 1: Core Logic & Database

- [ ] **Step 1: Implement dHash & Update DB**
    - [ ] Modify `sort_screenshots.py`:
        - [ ] Add `compute_dhash`.
        - [ ] Update `init_db` (add `phash` column).
        - [ ] Update `process_files` to save hash.
        - [ ] Implement `process_phash_backfill`.

- [ ] **Step 2: Detection Logic**
    - [ ] Modify `db_bridge.py`:
        - [ ] Add `find_duplicates` command.
        - [ ] Logic: Fetch id, path, phash, created_at.
        - [ ] Compare hashes (Hamming distance <= 5).
        - [ ] Group results.

## Phase 2: API & UI

- [ ] **Step 3: Server API**
    - [ ] Add `GET /api/duplicates` to `server.js`.
    - [ ] Add `DELETE /api/delete-file` (if not exists) to handle cleanup.

- [ ] **Step 4: Frontend**
    - [ ] Add "Clean Up Duplicates" button in Settings.
    - [ ] Create `view-duplicates` section.
    - [ ] Render groups of duplicates.
    - [ ] Logic to delete selected file and refresh.

## Phase 3: Verification

- [ ] **Step 5: Test**
    - [ ] Create mock duplicates (copy file, slight resize/crop).
    - [ ] Verify detection.
    - [ ] Verify deletion.
