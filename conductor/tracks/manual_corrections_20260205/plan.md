# Plan: Manual Categorization & Corrections (UI)

## Phase 1: Backend Implementation (Bridge & Server)

- [ ] **Step 1: Update `db_bridge.py`**
    - [ ] Add `move_file(filename, new_category)` function.
    - [ ] Implement physical move logic with `shutil`.
    - [ ] Implement DB update logic.
    - [ ] Handle naming collisions in destination.

- [ ] **Step 2: Update `server.js`**
    - [ ] Add `express.json()` middleware if not present.
    - [ ] Create `POST /api/move-file` endpoint.
    - [ ] Integrate with `runBridge('move_file', ...)`.

## Phase 2: Frontend Implementation

- [ ] **Step 3: Update `index.html` UI**
    - [ ] Add a `<select>` element to the `image-viewer` modal.
    - [ ] Populate it with the categories from `dashboardData`.
    - [ ] Add a "Move" button.

- [ ] **Step 4: Implement Frontend Logic**
    - [ ] Create `updateCategory()` JS function.
    - [ ] Show a loading state/spinner during the move.
    - [ ] Refresh the view on success and close the viewer.

## Phase 3: Testing & Verification

- [ ] **Step 5: Verification**
    - [ ] Manually test moving a file from "Unsorted" to "Finance".
    - [ ] Verify file exists in the new directory.
    - [ ] Verify DB reflects the change.
    - [ ] Test moving to a category that doesn't have a folder yet (should create it).
