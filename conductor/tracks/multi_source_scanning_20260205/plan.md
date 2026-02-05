# Plan: Multi-Source Scanning Support

## Phase 1: Configuration & Core Logic Update

- [ ] **Step 1: Update Configuration Parsing**
    - [ ] Modify `sort_screenshots.py` to check for `SOURCE_DIRS` environment variable.
    - [ ] Parse `SOURCE_DIRS` (support JSON string or comma/semicolon separation) into a list `source_directories`.
    - [ ] Ensure backward compatibility: if `SOURCE_DIRS` is missing, use `SOURCE_DIR` as a single-item list.
    - [ ] Log the detected source directories at startup.

- [ ] **Step 2: Refactor Main Loop**
    - [ ] Identify the main scanning loop (where it lists files).
    - [ ] Refactor the file listing logic to iterate through each path in `source_directories`.
    - [ ] Ensure the file processing loop handles the absolute path of files correctly (since they now come from different roots).

## Phase 2: Testing & Verification

- [ ] **Step 3: Test with Multiple Sources**
    - [ ] Create two temporary test directories with sample images.
    - [ ] Run `sort_screenshots.py` with `SOURCE_DIRS` pointing to these test directories.
    - [ ] Verify images from both sources are processed and moved to the destination.

- [ ] **Step 4: Naming Collision Verification**
    - [ ] Place two different images with the same filename (e.g., `image.png`) in different source directories.
    - [ ] Run the sorter.
    - [ ] Verify that both are preserved (one should be renamed automatically by the existing collision logic).

## Phase 3: Documentation

- [ ] **Step 5: Update Documentation**
    - [ ] Update `README.md` to explain how to configure multiple source directories.
    - [ ] Update CLI help text if applicable.
