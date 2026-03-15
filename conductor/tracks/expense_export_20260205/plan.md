# Plan: Smart Expense Export

## Phase 1: Backend Implementation

- [ ] **Step 1: Update `db_bridge.py`**
    - [ ] Import `csv`.
    - [ ] Add `export_expenses(year_month)` function.
    - [ ] Logic to calculate timestamps and fetch data.
    - [ ] Logic to write CSV to `Exports/`.
    - [ ] Update `main` dispatcher.

- [ ] **Step 2: Update `server.js`**
    - [ ] Add `POST /api/export` endpoint.

## Phase 2: Frontend Implementation

- [ ] **Step 3: Update `index.html`**
    - [ ] Add "Export" button near the "Finance" chart or stats.
    - [ ] Create a simple "Export Modal" or use `prompt` (Modal is better style).
        - Input: `<input type="month">`.
        - Button: "Download".
    - [ ] Javascript function `exportExpenses()`.
        - Call API.
        - Show success alert with file path.

## Phase 3: Verification

- [ ] **Step 4: Test**
    - [ ] Mock DB with finance data.
    - [ ] Run export.
    - [ ] Verify CSV content.
