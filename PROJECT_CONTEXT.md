# XPanda Foam — Project Context

## Company Overview
XPanda Foam is an EPS (Expanded Polystyrene) foam manufacturing facility. They produce foam in-house from raw polystyrene beads AND fabricate finished parts from the foam blocks they produce. This is important — they're not just a fabricator cutting pre-made foam, they run the full process from raw bead to finished product.

## Manufacturing Process Flow

### Stage 1: Pre-Expansion
Raw polystyrene beads are loaded into a pre-expander where steam is applied. The beads expand to ~40x their original size. The output is "pre-puff" — expanded beads at a target density.

**Key data to capture:** Bead lot number (from supplier), expansion batch number (auto-generated), target density, actual density, steam pressure, cycle time, operator, pre-expander station used.

### Stage 2: Aging / Conditioning
Pre-expanded beads are transferred to aging silos where they rest for 12–24+ hours. This allows moisture to escape and air to fill the bead cells, stabilizing the material.

**Key data to capture:** Which silo, aging start time, aging end time, source expansion batch, temperature/humidity if monitored.

### Stage 3: Block Molding
Aged beads are fed into a block mold where steam is applied again, fusing the beads into a solid block. Standard EPS block sizes vary but are typically large rectangular blocks.

**Key data to capture:** Mold ID, block dimensions (L×W×H in inches), block weight, density (lb/ft³), molding cycle time, steam pressure, source aging batch, operator, quality pass/fail.

### Stage 4: Cutting / Fabrication
Blocks are cut into sheets, shapes, or custom parts using hot wire cutters, CNC routers, or band saws. This is where raw blocks become sellable product.

**Key data to capture:** Source block/lot, cut dimensions, quantity produced, scrap quantity, work order reference, operator, station used.

### Stage 5: Packaging & Shipping
Finished parts are packaged per customer specs and shipped.

## Traceability Chain
This is critical for quality management. The system must support tracing:
```
Customer Complaint → Finished Part → Cut Operation → Source Block → Block Mold Run → Aging Silo → Expansion Batch → Raw Bead Lot (supplier)
```
Every `ProductionBatch` has an `input_batch_id` field that chains to the previous stage's batch. This is the backbone of lot traceability.

## Data Model Relationships
```
Raw Material (Inventory) ← lot_number
    ↓
ProductionBatch (type: expansion) ← raw_material_lot references inventory lot
    ↓
ProductionBatch (type: aging) ← input_batch_id → expansion batch
    ↓
ProductionBatch (type: molding) ← input_batch_id → aging batch
    ↓
ProductionOutput (type: foam_block) ← batch_id → molding batch
    ↓
ProductionOutput (type: fabricated_part) ← references source block via lot_number / expansion_batch
    ↓
WorkOrder → ties to customer Order
```

## Work Order Flow
1. Order comes in (eventually from QuickBooks integration — not built yet)
2. Work order is created referencing the order
3. Operators clock into the work order at their station
4. Production output is logged against the work order
5. Inventory is consumed (raw beads) and produced (blocks, finished parts)
6. Quality inspections are tied to work orders and batches

## Key Business Rules
- **Density matters:** EPS foam density (lb/ft³) determines its properties and price. Common densities range from 0.75 to 2.0 lb/ft³. The system needs to track target vs actual density.
- **Yield tracking:** Theoretical yield (how much finished product should come from a block) vs actual yield is a key quality metric. Scrap percentage matters.
- **Multiple active jobs:** Operators may monitor aging silos while also running a cutter. The time tracking system allows clocking into multiple operations simultaneously.
- **Batch numbering:** Auto-generated as `TYPE-YYYYMMDD-NNN` (e.g., `EXP-20260417-001`). Sequence number must be unique per type per day — query for the next available sequence, don't hardcode.

## Units of Measure
- Block dimensions: inches
- Density: lb/ft³ (pounds per cubic foot)
- Volume: ft³ (cubic feet). Convert from inches: `(L × W × H) / 1728`
- Weight: pounds
- Bead quantity: pounds (raw material is measured by weight)
- Finished parts: each (EA) or by customer-specified UOM

## Users
- **Shop floor operators:** Use the Job Clock and Production Recording views on tablets. UI must be touch-friendly with large buttons (min 48px, clock in/out buttons 80px).
- **Quality manager (Steve):** Uses quality module, reviews NCRs, manages inspections, runs reports.
- **Admin:** Full access to all modules including settings.

## Integration Points (Current & Planned)
- **Google Drive:** Connector exists for document storage (SOPs, reports). Partially built.
- **QuickBooks:** Planned for order sync. Not started — waiting on account access. Will likely be one-way (QB → ERP) initially for viewing/printing orders.
- **ClickUp:** Steve uses this externally for task management. No direct integration planned.
