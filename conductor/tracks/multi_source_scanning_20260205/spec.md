# Specification: Multi-Source Scanning Support

## 1. Overview
Currently, `sort_screenshots.py` only monitors a single `SOURCE_DIR`. This feature will allow the application to monitor and process images from multiple user-defined directories simultaneously.

## 2. Requirements
- **Configuration:** Support a configurable list of source directories (e.g., via environment variable or JSON config).
- **Environment Variable:** Introduce `SOURCE_DIRS` (plural) to replace or augment `SOURCE_DIR`.
    - Format: JSON array string or semicolon-separated path list.
    - Example: `["/sdcard/Pictures/Screenshots", "/sdcard/Download", "/sdcard/WhatsApp Images"]`
- **Processing Logic:** 
    - Iterate through all configured directories.
    - Maintain the same processing logic (OCR, AI, Video) for all sources.
    - Ensure processed files are moved to the correct destination (either a centralized sorted folder or sorted relative to their source - *Decision: Centralized Sorted Folder per existing logic*).
- **CLI Support:** Update `sort_screenshots.py` arguments to potentially accept multiple `--source` flags or a config file path.
- **Backward Compatibility:** Fallback to `SOURCE_DIR` if `SOURCE_DIRS` is not set.

## 3. Technical Implementation
### `sort_screenshots.py`
- **Config Parsing:**
    - Parse `os.environ.get('SOURCE_DIRS')`.
    - Update the main loop to iterate over a list of directories instead of a single variable.
- **File Discovery:**
    - The file scanning logic (finding images/videos) needs to aggregate files from all sources.
    - **Caution:** Ensure no naming collisions if moving files to a single destination.
        - *Strategy:* Use the existing collision handling (appending timestamp/uuid) if a file with the same name exists in the destination.

### `README.md`
- Update configuration documentation to explain how to set multiple sources.

## 4. Acceptance Criteria
- [ ] User can define multiple source paths via environment variable `SOURCE_DIRS`.
- [ ] The script successfully detects and processes images from all defined paths.
- [ ] Files from "Downloads" and "Screenshots" are both sorted into the correct categories in the main destination folder.
- [ ] Existing `SOURCE_DIR` configuration still works as expected.
