# XPanda ERP-Lite — Claude Code Guide

## What This Is
Desktop ERP system for XPanda Foam, an EPS foam manufacturing facility. Built with PyQt6 + SQLAlchemy + PostgreSQL. Runs on Windows.

## How to Run
```bash
cd erp-lite
python main.py
```
Requires PostgreSQL running locally (db: `xpanda_erp`, user: `postgres`). Config is in `config.py` and `.env`.

## Project Structure
```
erp-lite/
├── main.py                     # App entry point
├── config.py                   # DatabaseConfig, AppConfig, GoogleDriveConfig
├── database/
│   ├── connection.py           # DatabaseManager, Base, session management
│   ├── models/                 # SQLAlchemy models (inventory, orders, production, quality, shop_floor)
│   └── migrations/versions/    # Alembic migrations (001–005)
├── modules/
│   ├── inventory/              # Materials, receiving, stock tracking
│   ├── production/             # Dashboards, BOM editor, work orders
│   ├── orders/                 # Order management, customers, processing
│   ├── quality/                # Inspections, NCR tracking, CAPAs
│   └── shop_floor/             # Job clock, production recording, batch tracking, stations
├── ui/
│   ├── main_window.py          # MainWindow — sidebar + content stack + status bar
│   ├── components/             # Reusable: DataTable, FormDialog, Sidebar, StatusBar, MessageBox
│   └── themes/style_manager.py # Centralized dark theme (StyleManager)
├── integrations/google_drive/  # Google Drive connector (stubbed)
├── utils/                      # db_manager.py, logger.py
└── reports/                    # Report generation (stubbed)
```

## Architecture Pattern
Every module follows: **View → Controller → Service → DatabaseManager → PostgreSQL**

- **Views** (`modules/*/views/`): PyQt6 widgets. Handle UI layout, user interaction, signal/slot connections. Should NOT contain business logic or direct DB calls.
- **Controllers** (`modules/*/controllers/`): Coordinate between views and services. Validate input, manage callbacks for UI refresh. Register `data_changed` and `status_message` callbacks from views.
- **Services** (`modules/*/services/`): All database operations. Use `with self.db_manager.get_session() as session:` context manager pattern. Handle queries, creates, updates, deletes.
- **Models** (`database/models/`): SQLAlchemy ORM models inheriting from `Base` (defined in `connection.py`).

## Critical Patterns — Follow These

### Database Sessions
```python
# CORRECT — always use context manager
with self.db_manager.get_session() as session:
    result = session.query(Model).filter(...).all()
    session.commit()

# WRONG — never do this
session = self.db_manager.session_factory()
```

### Controller Callbacks
```python
# Controllers notify views of data changes via registered callbacks
controller.register_data_changed_callback(self.refresh_table)
controller.register_status_message_callback(self.on_status_message)
```

### View Conventions
- Use `setProperty("class", "...")` and `setObjectName("...")` for styling hooks
- Never write inline `setStyleSheet()` in views — all styling lives in `style_manager.py`
- Touch-friendly targets: minimum 48px height for shop floor views
- Use `DataTableWithFilter` from `ui/components/data_table.py` for all tables
- Use `FormDialog` from `ui/components/form_dialog.py` for create/edit forms
- Use `show_info()`, `show_error()`, `confirm_delete()` from `ui/components/message_box.py`

### Module Loading
New modules must be:
1. Imported in `ui/main_window.py`
2. Added to `create_module_widget()` with a unique module key
3. Added to `sidebar.py` module list with section grouping
4. Added to `get_module_section()` mapping

## Styling Rules
- All styles centralized in `ui/themes/style_manager.py`
- Dark theme is default (GitHub Dark inspired)
- Color palette:
  - Backgrounds: `#0F1117` (app), `#0A0C10` (sidebar), `#161B22` (content), `#1C2128` (cards)
  - Text: `#E6EDF3` (primary), `#8B949E` (secondary), `#484F58` (muted)
  - Accent: `#58A6FF`, Success: `#3FB950`, Warning: `#D29922`, Danger: `#F85149`
  - Borders: `#2D333B` (cards), `#21262D` (dividers), `#30363D` (inputs)
- Font: Segoe UI (Windows), SF Pro Display (Mac), 13px base
- No inline `setStyleSheet()` in view files

## Tech Stack
- Python 3.14, PyQt6 6.6.1, SQLAlchemy 2.0.23, PostgreSQL (psycopg2-binary)
- Alembic for migrations, reportlab for PDF generation, pyqtgraph for charts
- Platform: Windows (primary), should remain cross-platform compatible

## Current State
- Inventory, Production, Orders, Quality modules: scaffolded, partially functional
- Shop Floor module (job clock, production recording, batch tracking, stations): scaffolded, mostly non-functional — buttons exist but many don't connect to actual DB operations
- UI theme: dark mode applied but sidebar icons are broken (Unicode encoding issue), some inline styles remain
- See TASKS.md for specific work items
