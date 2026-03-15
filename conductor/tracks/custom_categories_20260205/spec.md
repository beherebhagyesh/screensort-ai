# Specification: Custom User Categories

## 1. Overview
Currently, categories are hardcoded in `sort_screenshots.py`. This feature empowers users to define their own categories and keywords, allowing for personalized organization (e.g., "Work", "Recipes", "Gaming").

## 2. Requirements
- **Config Storage:** Store custom categories in `user_categories.json` in the root directory.
- **Sorting Logic:** The sorting script must load this file and merge it with the default categories. Custom categories should have higher priority or just be added to the list.
- **Management UI:**
    - View all active categories and their keywords.
    - Add a new category.
    - Add/Remove keywords from a category.
    - Delete a custom category.
- **API:**
    - `GET /api/config/categories`
    - `POST /api/config/categories` (Save full JSON)

## 3. Technical Implementation
### `sort_screenshots.py`
- Function `load_categories()`:
    - Initialize with hardcoded defaults.
    - Read `user_categories.json`.
    - Update/Override defaults.
- Call `load_categories()` at startup and potentially periodically (or just restart script). *Decision: Restarting script is hard from UI. We will reload categories on every `process_files` loop or check file mtime.* Reloading on loop is safer.

### `db_bridge.py`
- Command `get_config`: Return merged categories.
- Command `save_config`: Write to `user_categories.json`. Note: We should only write the *custom* ones, or maybe just write the whole merged set?
    - *Better approach:* The UI fetches defaults + custom. User edits. We save the *difference* or just save everything to JSON and let JSON override defaults completely.
    - *Decision:* `user_categories.json` stores *additions* and *overrides*.
    - `save_config` writes to `user_categories.json`.

### `index.html`
- Settings -> "Manage Categories".
- List view of categories.
- Click to expand and edit keywords (comma separated input).
- "Add Category" button.

## 4. Acceptance Criteria
- [ ] User can add a category "TestCat" with keyword "testkw".
- [ ] `user_categories.json` is created/updated.
- [ ] `sort_screenshots.py` picks up the new category.
- [ ] A screenshot containing "testkw" is sorted into "TestCat".
