# XPanda Foam ERP-Lite Desktop Application

A comprehensive ERP-lite desktop application for XPanda Foam, an EPS (Expanded Polystyrene) foam manufacturing facility.

## Overview

This system serves as the operational backbone for inventory tracking, production scheduling, order management, and quality management. The application is designed for small-to-mid manufacturing environments where simplicity and reliability matter more than enterprise-scale features.

## Tech Stack

- **Language**: Python 3.11+
- **UI Framework**: PyQt6
- **Database**: PostgreSQL (local instance)
- **ORM**: SQLAlchemy 2.0+ with Alembic for migrations
- **Google Drive Integration**: Google Drive API v3
- **Reporting**: ReportLab for PDF generation
- **Charting**: PyQtGraph for embedded charts
- **Packaging**: PyInstaller for distribution

## Project Structure

```
xpanda-erp/
|
|-- main.py                    # Application entry point
|-- config.py                  # Configuration management
|-- alembic.ini                # Alembic configuration
|-- requirements.txt           # Python dependencies
|-- .env.example              # Environment variables template
|
|-- database/
|   |-- connection.py          # PostgreSQL connection management
|   |-- models/                # SQLAlchemy models
|   |   |-- inventory.py       # Inventory-related models
|   |   |-- production.py      # Production models (future)
|   |   |-- orders.py          # Order models (future)
|   |   |-- quality.py         # Quality models (future)
|   |   `-- __init__.py
|   `-- migrations/            # Alembic migrations
|       |-- env.py            # Migration environment
|       |-- script.py.mako    # Migration template
|       `-- versions/         # Migration files
|
|-- modules/
|   |-- inventory/             # Inventory module
|   |   |-- views/            # PyQt widgets/windows
|   |   |   |-- inventory_dashboard.py
|   |   |   |-- material_detail.py
|   |   |   `-- receiving_log.py
|   |   |-- controllers/       # Business logic (future)
|   |   |-- services/          # Data access layer (future)
|   |   `-- __init__.py
|   |-- production/            # Production module (future)
|   |-- orders/               # Orders module (future)
|   |-- quality/              # Quality module (future)
|   `-- __init__.py
|
|-- ui/
|   |-- main_window.py         # Main application window
|   |-- components/            # Reusable widgets
|   |   |-- sidebar.py        # Navigation sidebar
|   |   |-- status_bar.py     # Status bar
|   |   `-- settings_dialog.py # Settings configuration
|   `-- themes/                # Stylesheets
|       `-- style_manager.py  # Theme management
|
|-- integrations/
|   `-- google_drive/          # Drive API wrapper (future)
|
|-- utils/
|   |-- logger.py              # Logging configuration
|   `-- db_manager.py         # Database management utility
|
`-- tests/                     # Test suite (future)
```

## Installation and Setup

### Prerequisites

1. Python 3.11 or higher
2. PostgreSQL 12 or higher
3. Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd erp-lite
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Unix
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE xpanda_erp;
   CREATE USER erp_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE xpanda_erp TO erp_user;
   ```

6. **Initialize database**
   ```bash
   python utils/db_manager.py setup
   ```

7. **Run the application**
   ```bash
   python main.py
   ```

## Database Management

The application includes a database management utility for migrations and maintenance:

### Available Commands

```bash
# Set up database from scratch
python utils/db_manager.py setup

# Run pending migrations
python utils/db_manager.py migrate

# Create new migration
python utils/db_manager.py create-migration --message "Add new feature"

# Downgrade to previous revision
python utils/db_manager.py downgrade

# View migration history
python utils/db_manager.py history

# Check current revision
python utils/db_manager.py current

# Check database health
python utils/db_manager.py health

# Reset database (WARNING: deletes all data)
python utils/db_manager.py reset
```

## Module Status

### Completed Foundation (Phase 1)

- [x] Project structure and configuration
- [x] Database connection management
- [x] Main window with sidebar navigation
- [x] Settings screen for database and Google Drive
- [x] Inventory database models with SQLAlchemy
- [x] Alembic migration setup
- [x] Basic inventory views (dashboard, material detail, receiving log)
- [x] UI components (sidebar, status bar, themes)

### In Progress (Phase 2)

- [ ] Inventory controllers and services layer
- [ ] Reusable UI components (forms, dialogs)
- [ ] Inventory CRUD operations (materials, receiving, adjustments)

### Planned (Phase 3+)

- [ ] Production & Manufacturing Scheduling
- [ ] Order Management
- [ ] Quality Management
- [ ] Google Drive Integration
- [ ] PDF Report Generation
- [ ] Advanced UI features and polish

## Key Features

### Inventory Management

- **Material Master**: Complete catalog of raw materials, finished goods, consumables, and packaging
- **Stock Tracking**: Real-time inventory levels with committed and available quantities
- **Receiving**: Log incoming materials with PO references and lot/batch tracking
- **Adjustments**: Manual stock adjustments with reason codes and audit trails
- **Low Stock Alerts**: Visual indicators when items fall below reorder points
- **Search & Filter**: Find materials by category, supplier, location, or stock status

### Database Schema

- **UUID Primary Keys**: All tables use UUID for primary keys
- **Audit Fields**: created_at, updated_at, created_by on all core records
- **Soft Delete**: deleted_at timestamp for data retention
- **ENUM Types**: Standardized status fields
- **Indexes**: Optimized for common query patterns

### UI/UX Features

- **Professional Design**: Industrial theme with meaningful color coding
- **Responsive Layout**: Collapsible sidebar and resizable panels
- **Keyboard Shortcuts**: Ctrl+N (new), Ctrl+S (save), Ctrl+F (search), Escape (cancel)
- **Status Bar**: Database connection, Google Drive sync, and system messages
- **Table Features**: Sorting, filtering, column visibility toggles

## Configuration

### Database Settings

Configure database connection through:
1. Settings dialog in the application
2. Environment variables (.env file)
3. Direct editing of config.py

### Google Drive Integration

Set up Google Drive API credentials:
1. Create a project in Google Cloud Console
2. Enable Google Drive API
3. Create OAuth2 credentials
4. Download client_secrets.json
5. Configure in settings dialog

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write comprehensive docstrings
- Keep functions focused and testable

### Database Changes

1. Never modify schema by hand
2. Always use Alembic migrations
3. Test migrations on development database first
4. Include both upgrade and downgrade logic

### UI Development

- Follow existing component patterns
- Use the style manager for consistent theming
- Implement keyboard shortcuts for common actions
- Ensure responsive design principles

## Testing

```bash
# Run tests (when implemented)
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=modules
```

## Deployment

### Creating Executable

```bash
# Build executable with PyInstaller
pyinstaller --onefile --windowed main.py
```

### Distribution

The application is designed for single-user deployment with local PostgreSQL instance.

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL service is running
   - Verify database credentials in .env file
   - Ensure database exists and user has permissions

2. **Migration Errors**
   - Check database connection
   - Verify models are properly imported
   - Check for syntax errors in migration files

3. **UI Not Loading**
   - Check PyQt6 installation
   - Verify all required modules are importable
   - Check for missing UI component files

### Logging

Application logs are stored in `logs/` directory with daily rotation:
- `logs/erp_lite_YYYYMMDD.log` - Detailed application logs
- Console output shows INFO level and above

## Contributing

1. Follow the existing code structure and patterns
2. Create migrations for any database changes
3. Add appropriate tests for new functionality
4. Update documentation for new features

## License

[License information to be added]

## Support

For technical support or questions:
- Check the troubleshooting section
- Review application logs for error details
- Contact the development team

---

**Current Development Status**: Phase 1 Foundation Complete  
**Next Milestone**: Inventory CRUD Operations and Controllers  
**Target Release**: Q2 2024
