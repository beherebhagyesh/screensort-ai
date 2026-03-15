# Plan: Custom User Categories

## Phase 1: Backend Logic

- [ ] **Step 1: Update `sort_screenshots.py`**
    - [ ] Implement `load_categories` function.
    - [ ] Load `user_categories.json`.
    - [ ] Merge with `CATEGORIES`.
    - [ ] Call `load_categories` at start of each processing loop.

- [ ] **Step 2: Update `db_bridge.py`**
    - [ ] Add `get_categories` command (returns current effective categories).
    - [ ] Add `save_categories` command (writes to `user_categories.json`).

- [ ] **Step 3: Update `server.js`**
    - [ ] Add `GET /api/categories` and `POST /api/categories`.

## Phase 2: Frontend UI

- [ ] **Step 4: Update `index.html`**
    - [ ] Add "Manage Categories" button in Settings.
    - [ ] Create `view-manage-categories` section.
    - [ ] Render category list with editable inputs.
    - [ ] "Save Changes" button.

## Phase 3: Verification

- [ ] **Step 5: Test**
    - [ ] Add a custom category via UI.
    - [ ] Create a dummy image with text matching the new category.
    - [ ] Verify it gets sorted correctly.
