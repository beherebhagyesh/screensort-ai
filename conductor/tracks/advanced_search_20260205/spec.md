# Specification: Advanced Search & Filtering

## 1. Overview
The current search functionality is a simple full-text search on the extracted text and category name. This feature adds structured filtering capabilities, allowing users to narrow down results by specific criteria like date, amount, and category.

## 2. Requirements
- **Filter UI:**
    - A toggleable "Filter" panel in the search overlay.
    - Inputs for:
        - **Category:** Dropdown list (populated dynamically).
        - **Date Range:** Start Date and End Date pickers.
        - **Amount:** Min and Max numeric inputs.
- **Backend Search Logic:**
    - Update the search query to support optional filters.
    - Logic: `WHERE (text LIKE %q%) AND (category = ?) AND (created_at BETWEEN ? AND ?) AND (amount BETWEEN ? AND ?)`
- **API Update:**
    - `GET /api/search` should accept new query parameters: `category`, `startDate`, `endDate`, `minAmount`, `maxAmount`.

## 3. Technical Implementation
### `db_bridge.py`
- Update `search(query, filters)` function.
- Parse a JSON filter string or separate arguments.
- Build the SQL `WHERE` clause dynamically based on provided filters.
- **Note:** `created_at` in DB is in milliseconds. Frontend sends `YYYY-MM-DD`. Conversion needed.

### `server.js`
- Update `/api/search` to extract query params.
- Pass them to `db_bridge.py`.
    - *Decision:* Pass filters as a JSON string argument to keep the bridge signature clean.

### `index.html`
- Add a filter button next to the search bar.
- Create a `div` for the filter panel (hidden by default).
- Update the `input` event listener (or change to a "Search" button to avoid spamming complex queries) to gather filter values.
    - *UX Decision:* Keep "type to search" but maybe debounce it, or only trigger when filters change or Enter is pressed. Let's stick to debounce/input for text, but trigger search immediately on filter change.

## 4. Acceptance Criteria
- [ ] User can open a filter panel in the search view.
- [ ] User can select a specific category (e.g., "Finance").
- [ ] User can specify a date range (e.g., "2023-01-01" to "2023-12-31").
- [ ] User can specify an amount range (e.g., "$100" to "$500").
- [ ] Search results accurately reflect the combination of text query AND active filters.
