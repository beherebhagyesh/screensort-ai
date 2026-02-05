# Specification: Duplicate Image Detection

## 1. Overview
Screenshots often accumulate duplicates (accidental double-taps, same content captured twice). This feature uses **Difference Hash (dHash)** to identify perceptually similar images and provides a UI to review and delete them.

## 2. Requirements
- **Hashing:**
    - Implement `dHash` (Difference Hash) using `Pillow`.
    - 64-bit hash stored as a hex string.
    - Compute hash during `sort_screenshots.py` processing.
- **Database:**
    - Add `phash` column to `screenshots` table.
- **Detection API:**
    - `GET /api/duplicates`
    - Returns groups of images that are similar (Hamming distance <= 5).
- **UI:**
    - New "Duplicates" view (access via Settings or Dashboard).
    - Show side-by-side comparison.
    - "Delete" button for each image.

## 3. Technical Implementation
### `sort_screenshots.py`
- Function `compute_dhash(image_path)`.
    - Resize to 9x8, Grayscale.
    - Compare pixels: `row[x] > row[x+1]`.
    - Return hex string.
- Update `init_db` to add `phash` column.
- Update `process_files` to compute and save hash.
- Add `process_phash_backfill` for existing images.

### `db_bridge.py`
- Update `find_duplicates` command.
    - Fetch all hashes.
    - Compute Hamming distances (bitwise XOR of int(hash, 16)).
    - Group similar images.
    - Optimization: Only compare images with hashes that are "close" numerically? No, dHash locality isn't guaranteed that way. Brute force or "BK-Tree" (if time permits).
    - *Decision:* Python-side brute force is acceptable for < 5000 images. For larger sets, we might limit checks to same `category` or `date` window (e.g., within 7 days). **Constraint: Check images within 7 days of each other.** Duplicates usually happen close in time.

### `index.html`
- Add "Clean Up" button in Settings.
- Render "Duplicate Sets".

## 4. Acceptance Criteria
- [ ] dHash is computed for new and existing images.
- [ ] Database stores hashes.
- [ ] UI lists potential duplicates.
- [ ] User can delete duplicates via UI.
