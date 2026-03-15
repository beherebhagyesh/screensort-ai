# Specification: Manual Categorization & Corrections (UI)

## 1. Overview
Allow users to manually correct the category of any screenshot directly from the Web Viewer. This is essential for fixing OCR/AI misclassifications and organizing the vault accurately.

## 2. Requirements
- **UI Integration:** 
    - Add a "Category" dropdown in the Image Viewer modal.
    - Show the current category as the selected option.
    - Provide an "Update" or "Save" button (or auto-save on change).
- **Backend API:**
    - New endpoint: `POST /api/move-file`
    - Parameters: `filename` (unique ID), `new_category`.
- **File System Operations:**
    - Physically move the file from `SOURCE_DIR/OldCategory/filename` to `SOURCE_DIR/NewCategory/filename`.
    - Handle naming collisions in the destination folder.
- **Database Update:**
    - Update the `category` and `path` columns in the `screenshots` table for the given file.
- **Refresh Logic:**
    - After moving, the gallery/dashboard should reflect the change without a full page reload if possible (or trigger `fetchData()`).

## 3. Technical Implementation
### `db_bridge.py`
- Add a new command `move_file`.
- Logic:
    1. Fetch current path from DB.
    2. Construct new path based on `NewCategory`.
    3. Physically move the file using `shutil.move`.
    4. Update DB record.

### `server.js`
- Add `app.post('/api/move-file', ...)`
- Parse JSON body: `{ filename: string, newCategory: string }`.
- Call `db_bridge.py move_file`.

### `index.html`
- Update `openImage` to fetch and show categories in a select menu.
- Add `updateCategory(filename, newCategory)` function.

## 4. Acceptance Criteria
- [ ] User can see a category dropdown when viewing an image.
- [ ] Selecting a new category and clicking "Move" successfully moves the file on disk.
- [ ] The database is updated with the new path and category.
- [ ] The UI refreshes to show the image in its new category.
- [ ] Error handling for failed moves (e.g., permission denied, file missing).
