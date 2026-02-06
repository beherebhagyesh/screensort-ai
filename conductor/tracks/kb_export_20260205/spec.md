# Specification: Knowledge Base Export

## 1. Overview
Users want to use their screenshots as a "Second Brain". This feature exports the enriched data (AI summaries, OCR text) into a structured Markdown format suitable for tools like Obsidian or simply for archival.

## 2. Requirements
- **Output:** A `knowledge_base` folder in the source directory.
- **Structure:** Folders by Category. Markdown files for each screenshot.
- **File Content:**
    - YAML Frontmatter (date, tags, amount).
    - Embedded Image.
    - AI Summary.
    - Full extracted text block.
- **Trigger:** "Generate Knowledge Base" button in Settings.

## 3. Technical Implementation
### `db_bridge.py`
- Command `generate_kb`.
- Fetch all items.
- For each item:
    - Create `knowledge_base/{Category}`.
    - Create MD file.
    - Write content.

### `server.js`
- `POST /api/generate-kb` -> Calls bridge.

### `index.html`
- Button in Settings.

## 4. Acceptance Criteria
- [ ] Button triggers generation.
- [ ] Folder structure is created.
- [ ] MD files contain correct info and image links.
