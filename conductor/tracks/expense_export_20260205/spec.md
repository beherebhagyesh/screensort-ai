# Specification: Smart Expense Export

## 1. Overview
Users need a way to extract the financial data (amounts, dates, text) collected by the app to use in external tools like Excel or Google Sheets. This feature allows exporting the "Finance" category data to a CSV file.

## 2. Requirements
- **UI:**
    - "Export Expenses" button on the Dashboard (e.g., near the Finance chart).
    - Month selector (Default to current month).
- **Backend:**
    - New command `export_expenses` in `db_bridge.py`.
    - Logic: Fetch items from `Finance` category for the given `year` and `month`.
    - Output: Generate a CSV file with columns: `Date`, `Amount`, `Filename`, `AI Summary`, `Text Snippet`.
    - Storage: Save the CSV to `SCREENSHOTS_DIR/Exports/expenses_YYYY_MM.csv`.
- **API:**
    - `POST /api/export`
    - Body: `{ month: "2023-10" }`
    - Response: `{ success: true, path: "/path/to/file.csv", url: "/images/Exports/file.csv" }`

## 3. Technical Implementation
### `db_bridge.py`
- Import `csv`.
- Function `export_expenses(year, month)`.
- SQL: `SELECT * FROM screenshots WHERE category='Finance' AND created_at BETWEEN ? AND ?`
- Calculate start/end timestamps for the month.
- Write CSV.
- Ensure `Exports` directory exists.

### `server.js`
- `app.post('/api/export', ...)`
- Call bridge.

### `index.html`
- Add "Export" button in the Finance Chart area.
- Simple prompt or modal for month selection (or just export "Last 30 Days" / "Current Month" / "All Time").
    - *Decision:* Let's keep it simple: "Export" button opens a small prompt asking for Month (type="month" input).

## 4. Acceptance Criteria
- [ ] User can click "Export" and select a month.
- [ ] A CSV file is generated in the `Exports` folder.
- [ ] The CSV contains correct columns and data.
- [ ] The UI notifies the user of the success and location.
