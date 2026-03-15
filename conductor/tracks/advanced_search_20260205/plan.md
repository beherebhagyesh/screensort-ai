# Plan: Advanced Search & Filtering

## Phase 1: Backend Implementation

- [ ] **Step 1: Update `db_bridge.py`**
    - [ ] Update `search` command signature to accept a `filters` JSON string.
    - [ ] Implement dynamic SQL query construction.
    - [ ] Handle date conversion (YYYY-MM-DD string to Unix Timestamp MS).

- [ ] **Step 2: Update `server.js`**
    - [ ] Update `GET /api/search` to read `category`, `startDate`, `endDate`, `minAmount`, `maxAmount` from `req.query`.
    - [ ] Pack these into a JSON object.
    - [ ] Pass to `runBridge`.

## Phase 2: Frontend Implementation

- [ ] **Step 3: Update `index.html` UI**
    - [ ] Add "Tune" (Filter) icon button to search header.
    - [ ] Add Filter Panel HTML (hidden `div` with inputs).
    - [ ] Populate Category dropdown in filter panel from `dashboardData`.

- [ ] **Step 4: Implement Frontend Logic**
    - [ ] Add `toggleFilters()` function.
    - [ ] Update `performSearch()` logic (refactor existing event listener).
    - [ ] Collect values from inputs and append to API URL.
    - [ ] Trigger search on filter change.

## Phase 3: Verification

- [ ] **Step 5: Test**
    - [ ] Verify searching with just text works (backward compatibility).
    - [ ] Verify filtering by category "Finance".
    - [ ] Verify filtering by amount > 0.
