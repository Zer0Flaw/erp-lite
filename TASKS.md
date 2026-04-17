# XPanda ERP-Lite — Task Tracker

## Work Order (Priority Sequence)
Tackle in this order. Each phase builds on the previous.

---

## Phase 1: Inventory Module (Foundation)
Everything downstream depends on working inventory.

### Must Work
- [ ] Add new material (form opens, validates, saves to DB, refreshes table)
- [ ] Edit existing material (double-click row → form pre-populated → save updates)
- [ ] Delete material (confirm dialog → soft delete or hard delete)
- [ ] Search/filter inventory table (live filter by SKU, description, category)
- [ ] Summary cards pull real data (Total SKUs, Low Stock count, Total Value, Recent Receiving count)
- [ ] Receive materials (receiving log: select material, enter qty, lot number, supplier → updates on_hand)
- [ ] Material detail view shows full record with transaction history

### Known Issues
- [ ] Buttons may not be wired to controller methods
- [ ] Form dialog may not be configured with correct fields for materials
- [ ] Summary cards show hardcoded "0" — need to query DB on load and on data change

---

## Phase 2: Station Management
Stations must exist before job clock and production recording make sense.

### Must Work
- [ ] Add production station (station_id, name, type, location)
- [ ] Edit station details
- [ ] Set station status (Available, Running, Maintenance, Offline, Cleanup)
- [ ] Station list view with status indicators
- [ ] Pre-populate default XPanda stations: Pre-Expander, Block Mold 1, Block Mold 2, Aging Silo 1, Aging Silo 2, Hot Wire Cutter, CNC Router, Band Saw, Packaging, Inspection

### Known Issues
- [ ] View is scaffolded but buttons likely non-functional
- [ ] No seed data for default stations

---

## Phase 3: Job Clock (Shop Floor Time Tracking)
Operators' primary daily touchpoint.

### Must Work
- [ ] Clock in: select employee, operation, optional work order + station → creates TimeEntry
- [ ] Clock out: enter employee → finds active entries → closes with end_time and calculated hours
- [ ] Active jobs list updates in real-time with elapsed time (LiveTimerThread)
- [ ] Support multiple simultaneous clock-ins per employee (different operations)
- [ ] Recent activity table shows last 24h of completed time entries
- [ ] Large touch-friendly buttons (80px height) for tablet use

### Known Issues
- [ ] `load_recent_activity()` is stubbed — returns empty list
- [ ] Clock out with multiple active entries doesn't show selection dialog
- [ ] Employee name defaults to employee_id — no employee lookup yet
- [ ] Operation dropdown options come from `get_operation_options()` — verify this returns correct list

---

## Phase 4: Production Recording & Batch Tracking
Core manufacturing data capture. These two are tightly coupled.

### Production Recording Must Work
- [ ] Log foam block output: work order, block count, dimensions (L×W×H), density, bead lot, mold ID
- [ ] Log fabricated part output: work order, part count, scrap qty, source block/lot
- [ ] Auto-calculate yield percentage: `(produced - scrapped) / theoretical × 100`
- [ ] Auto-calculate block volume: `(L × W × H) / 1728` ft³
- [ ] Deduct raw material from inventory when recording production output
- [ ] Production output table with filters

### Batch Tracking Must Work
- [ ] Auto-generate batch numbers: `TYPE-YYYYMMDD-NNN` with proper sequence query
- [ ] Create expansion batch linked to raw material lot
- [ ] Create aging batch linked to expansion batch (input_batch_id)
- [ ] Create molding batch linked to aging batch
- [ ] View batch chain / traceability tree (follow input_batch_id chain)
- [ ] Store process parameters as JSON (temp, pressure, cycle time)
- [ ] Batch status tracking (active → completed)

### Known Issues
- [ ] Batch number generator hardcodes `-001` — needs to query for next sequence
- [ ] No inventory deduction logic exists yet
- [ ] Traceability tree view not built
- [ ] Process parameter JSON storage/display not implemented

---

## Phase 5: Production Module (Planning)
### Must Work
- [ ] Create work orders
- [ ] BOM editor — define materials needed per product
- [ ] Work order status flow: Draft → Released → In Progress → Complete
- [ ] Link work orders to orders (customer demand → production)

---

## Phase 6: Orders & Customers
### Must Work
- [ ] Add/edit customers
- [ ] Create orders with line items
- [ ] Order status tracking
- [ ] (Future) QuickBooks sync — blocked on account access

---

## Phase 7: Quality Module
### Must Work
- [ ] Create inspections tied to batches/work orders
- [ ] NCR tracking with root cause and corrective action
- [ ] CAPA management
- [ ] Link quality issues to traceability chain

---

## UI / Theme Fixes (Do Alongside Any Phase)
- [ ] Fix sidebar Unicode icons — showing `??` instead of emoji, likely encoding issue in sidebar.py
- [ ] Remove remaining inline `setStyleSheet()` calls from view files
- [ ] Sidebar: active button styling (left accent bar instead of full blue fill)
- [ ] Consistent spacing across all dashboard views (32px content padding, 16px card gap, 24px section gap)
- [ ] Summary cards: consistent height, colored left border accent, real data
- [ ] Table styling: 44px row height, subtle zebra striping, hover effect
- [ ] Form dialogs: 40px input height, proper label styling

---

## Completed
- [x] Project scaffolded (Windsurf)
- [x] Database models created for all modules including shop_floor
- [x] Dark theme applied via centralized StyleManager
- [x] Sidebar section grouping (SHOP FLOOR, PRODUCTION, ORDERS, QUALITY)
- [x] Shop floor module structure: controller, services, views, models
- [x] Migration 005 for shop_floor tables
- [x] Main window wired to load all shop floor views
- [x] Service import pattern fixed (DatabaseManager instead of get_db_session)
