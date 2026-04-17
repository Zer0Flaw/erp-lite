# XPanda ERP-Lite - System Integration Guide

## Overview

This document describes the complete system integration for XPanda ERP-Lite, including all modules, database setup, and usage instructions.

## System Architecture

XPanda ERP-Lite follows a modular layered architecture:

```
XPanda ERP-Lite
|
+-- Main Application (main.py)
|
+-- UI Layer (ui/)
|   +-- Main Window
|   +-- Sidebar Navigation
|   +-- Reusable Components
|
+-- Modules (modules/)
|   +-- Inventory Module
|   +-- Production Module
|   +-- Orders Module
|   +-- Quality Module
|
+-- Database Layer (database/)
|   +-- Models (SQLAlchemy ORM)
|   +-- Migrations (Alembic)
|   +-- Connection Management
|
+-- Configuration (config.py)
+-- Utilities (utils/)
```

## Module Structure

Each module follows the same architectural pattern:

```
modules/[module_name]/
|
+-- models/          # Database models (if additional to main models)
+-- services/        # Business logic layer
|   +-- __init__.py
|   +-- [module]_service.py
|   +-- [module]_service.py
|   +-- [module]_service.py (coordinator)
+-- controllers/     # UI integration layer
|   +-- __init__.py
|   +-- [module]_controller.py
+-- views/           # UI components
|   +-- __init__.py
|   +-- [module]_dashboard.py
|   +-- [module]_management.py
|   +-- [module]_processing.py
```

## Database Models

### Inventory Module
- **Material** - Material master data
- **MaterialCategory** - Material categories
- **InventoryTransaction** - Inventory movements
- **MaterialSupplier** - Supplier information
- **InventorySummary** - Current inventory levels
- **StockAdjustment** - Manual adjustments

### Production Module
- **BillOfMaterial** - BOM definitions
- **BillOfMaterialLine** - BOM components
- **WorkOrder** - Production orders
- **ProductionStep** - Work order steps
- **MaterialConsumption** - Material usage tracking
- **ProductionSchedule** - Production planning

### Orders Module
- **Customer** - Customer master data
- **SalesOrder** - Sales orders
- **OrderLine** - Order line items
- **Shipment** - Shipping information
- **ShipmentLine** - Shipment line items

### Quality Module
- **Inspection** - Quality inspections
- **InspectionLine** - Inspection criteria
- **NonConformanceReport** - NCR management
- **CAPAAction** - Corrective actions
- **QualityMetric** - Quality KPIs

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 12+
- PyQt6
- SQLAlchemy 2.0+
- Alembic

### 2. Database Setup

1. **Create PostgreSQL Database**
   ```sql
   CREATE DATABASE xpanda_erp_lite;
   CREATE USER xpanda_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE xpanda_erp_lite TO xpanda_user;
   ```

2. **Configure Database Connection**
   - Edit `.env` file with database credentials
   - Update `config.py` if needed

3. **Run Complete System Setup**
   ```bash
   python setup_complete_system.py
   ```

### 3. Run Integration Tests

```bash
python test_system_integration.py
```

### 4. Start the Application

```bash
   python main.py
```

## Module Navigation

The sidebar provides navigation to all modules and sub-modules:

### Inventory Module
- **Inventory Dashboard** - Overview and statistics
- **Material Detail** - Individual material management
- **Receiving Log** - Material receiving history

### Production Module
- **Production Dashboard** - Production overview
- **BOM Editor** - Bill of Materials management
- **Work Order Management** - Production order management

### Orders Module
- **Orders Dashboard** - Sales overview
- **Customer Management** - Customer master data
- **Order Processing** - Sales order management

### Quality Module
- **Quality Dashboard** - Quality overview
- **Inspection Management** - Inspection management
- **NCR Tracking** - Non-conformance tracking

## Key Features

### Inventory Management
- Material master data management
- Real-time inventory tracking
- Transaction history
- Stock adjustments
- Supplier management

### Production Management
- Bill of Materials (BOM) management
- Work order creation and tracking
- Production scheduling
- Material consumption tracking
- Production step management

### Order Management
- Customer management
- Sales order processing
- Order fulfillment tracking
- Payment status management
- Shipment tracking

### Quality Management
- Inspection management
- Non-conformance reporting (NCR)
- Corrective Action Plans (CAPA)
- Quality metrics and reporting
- Material quality history

## Data Flow

### Module Integration

1. **Inventory to Production**
   - Materials from inventory are consumed in production
   - BOMs reference inventory materials
   - Production updates inventory levels

2. **Production to Orders**
   - Production fulfills sales orders
   - Work orders can be created for specific orders
   - Production status affects order fulfillment

3. **Orders to Quality**
   - Failed inspections can create NCRs
   - NCRs can trigger CAPAs
   - Quality affects order fulfillment

4. **Quality to All Modules**
   - Quality issues can affect inventory, production, and orders
   - Quality metrics provide feedback for process improvement
   - CAPAs can address issues across all modules

## Configuration

### Application Settings

Settings are managed through the Settings dialog (accessible from sidebar):

- **Database Configuration** - Connection parameters
- **Google Drive Integration** - OAuth2 setup (future)
- **Theme Selection** - UI appearance
- **Auto-save Settings** - Automatic save intervals
- **Company Information** - Company details

### Module Configuration

Each module can be configured through:
- Module-specific settings in the UI
- Configuration files in `config.py`
- Database configuration tables

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **Module Import Errors**
   - Verify all dependencies are installed
   - Check Python path includes project root
   - Run `setup_complete_system.py` to verify setup

3. **UI Not Loading**
   - Check PyQt6 installation
   - Verify display environment
   - Run integration tests

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export XPANDA_DEBUG=1
python main.py
```

## Development

### Adding New Modules

To add a new module:

1. **Create Module Structure**
   ```
   modules/new_module/
   +-- services/
   +-- controllers/
   +-- views/
   ```

2. **Implement Services**
   - Create business logic classes
   - Follow existing service patterns

3. **Implement Controllers**
   - Create UI integration classes
   - Handle data flow between services and views

4. **Implement Views**
   - Create UI components
   - Follow existing view patterns

5. **Update Main Window**
   - Add module to `create_module_widget()`
   - Update sidebar navigation

6. **Add Database Models**
   - Create SQLAlchemy models
   - Add database migration
   - Update setup scripts

### Testing

Run the complete test suite:
```bash
python test_system_integration.py
```

## Performance Considerations

### Database Optimization
- Use appropriate indexes
- Monitor query performance
- Optimize large table operations

### UI Performance
- Use lazy loading for large datasets
- Implement pagination
- Optimize table rendering

### Memory Management
- Clean up database connections
- Dispose of UI components properly
- Monitor memory usage

## Security

### Database Security
- Use parameterized queries
- Implement proper authentication
- Regular database backups

### Application Security
- Validate user inputs
- Implement proper error handling
- Secure sensitive data

## Future Enhancements

### Planned Features
- Google Drive integration
- Advanced reporting
- Mobile interface
- API endpoints
- Multi-user support

### Extensibility
The system is designed to be extensible:
- Plugin architecture for modules
- Configurable workflows
- Custom fields support
- Integration APIs

## Support

For issues and support:
1. Check this documentation
2. Run integration tests
3. Review logs for error details
4. Check database connectivity
5. Verify module imports

## License

XPanda ERP-Lite is proprietary software of XPanda Foam Industries.
