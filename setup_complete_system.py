#!/usr/bin/env python3
"""
Complete System Setup for XPanda ERP-Lite.
Sets up all database tables and verifies system integration.
"""

import os
import sys
import logging
from typing import List, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_setup_script(script_name: str, description: str) -> Tuple[bool, str]:
    """Run a setup script and return success status."""
    try:
        logger.info(f"Running {description}...")
        
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import and run the script
        if script_name == 'setup_database_tables.py':
            from setup_database_tables import setup_database_tables
            result = setup_database_tables()
        elif script_name == 'setup_production_tables.py':
            from setup_production_tables import setup_production_tables
            result = setup_production_tables()
        elif script_name == 'setup_orders_tables.py':
            from setup_orders_tables import setup_orders_tables
            result = setup_orders_tables()
        elif script_name == 'setup_quality_tables.py':
            from setup_quality_tables import setup_quality_tables
            result = setup_quality_tables()
        else:
            logger.error(f"Unknown setup script: {script_name}")
            return False, f"Unknown setup script: {script_name}"
        
        if result == 0:
            logger.info(f"Successfully completed {description}")
            return True, f"Successfully completed {description}"
        else:
            logger.error(f"Failed to complete {description} (exit code: {result})")
            return False, f"Failed to complete {description} (exit code: {result})"
            
    except Exception as e:
        logger.error(f"Error running {description}: {e}")
        return False, f"Error running {description}: {e}"


def verify_database_tables() -> Tuple[bool, List[str]]:
    """Verify that all database tables exist."""
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        from database.connection import DatabaseManager
        from config import config
        
        logger.info("Verifying database tables...")
        
        # Connect to database
        db_manager = DatabaseManager(config.database)
        if not db_manager.connect():
            return False, ["Failed to connect to database"]
        
        # Expected tables by module
        expected_tables = {
            'inventory': [
                'materials', 'material_categories', 'inventory_transactions',
                'material_suppliers', 'inventory_summary', 'stock_adjustments'
            ],
            'production': [
                'bill_of_materials', 'bom_lines', 'work_orders',
                'production_steps', 'material_consumptions', 'production_schedules'
            ],
            'orders': [
                'customers', 'sales_orders', 'order_lines',
                'shipments', 'shipment_lines'
            ],
            'quality': [
                'inspections', 'inspection_lines', 'non_conformance_reports',
                'capa_actions', 'quality_metrics'
            ]
        }
        
        missing_tables = []
        
        with db_manager.engine.connect() as conn:
            from sqlalchemy import text
            
            # Get all tables in the database
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"))
            existing_tables = [row[0] for row in result]
            
            logger.info(f"Found {len(existing_tables)} tables in database")
            
            # Check each module's tables
            for module, tables in expected_tables.items():
                logger.info(f"Checking {module} module tables...")
                
                for table in tables:
                    if table in existing_tables:
                        logger.info(f"  - {table}: EXISTS")
                    else:
                        logger.error(f"  - {table}: MISSING")
                        missing_tables.append(f"{module}.{table}")
        
        db_manager.disconnect()
        
        if missing_tables:
            logger.error(f"Missing {len(missing_tables)} tables: {', '.join(missing_tables)}")
            return False, missing_tables
        else:
            logger.info("All expected database tables exist!")
            return True, []
            
    except Exception as e:
        logger.error(f"Error verifying database tables: {e}")
        return False, [f"Error verifying database tables: {e}"]


def verify_module_imports() -> Tuple[bool, List[str]]:
    """Verify that all modules can be imported successfully."""
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        logger.info("Verifying module imports...")
        
        # Modules to verify
        modules_to_check = [
            # Database models
            ('database.models.inventory', 'Inventory models'),
            ('database.models.production', 'Production models'),
            ('database.models.orders', 'Orders models'),
            ('database.models.quality', 'Quality models'),
            
            # Services
            ('modules.inventory.services', 'Inventory services'),
            ('modules.production.services', 'Production services'),
            ('modules.orders.services', 'Orders services'),
            ('modules.quality.services', 'Quality services'),
            
            # Controllers
            ('modules.inventory.controllers', 'Inventory controllers'),
            ('modules.production.controllers', 'Production controllers'),
            ('modules.orders.controllers', 'Orders controllers'),
            ('modules.quality.controllers', 'Quality controllers'),
            
            # Views
            ('modules.inventory.views', 'Inventory views'),
            ('modules.production.views', 'Production views'),
            ('modules.orders.views', 'Orders views'),
            ('modules.quality.views', 'Quality views'),
        ]
        
        failed_imports = []
        
        for module_path, description in modules_to_check:
            try:
                __import__(module_path)
                logger.info(f"  - {description}: OK")
            except ImportError as e:
                logger.error(f"  - {description}: FAILED - {e}")
                failed_imports.append(f"{description}: {e}")
        
        if failed_imports:
            logger.error(f"Failed to import {len(failed_imports)} modules")
            return False, failed_imports
        else:
            logger.info("All modules imported successfully!")
            return True, []
            
    except Exception as e:
        logger.error(f"Error verifying module imports: {e}")
        return False, [f"Error verifying module imports: {e}"]


def test_application_startup() -> Tuple[bool, str]:
    """Test that the application can start up without errors."""
    try:
        logger.info("Testing application startup...")
        
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Test configuration
        from config import config
        
        config_issues = config.validate()
        if config_issues:
            return False, f"Configuration validation failed: {', '.join(config_issues)}"
        
        # Test database connection
        from database.connection import DatabaseManager
        
        db_manager = DatabaseManager(config.database)
        if not db_manager.connect():
            return False, "Failed to connect to database"
        
        db_manager.disconnect()
        
        # Test main window creation (without showing it)
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QSettings
        from ui.main_window import MainWindow
        
        # Create minimal QApplication for testing
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create settings
        settings = QSettings("XPanda Foam", "ERP-Lite")
        
        # Create main window (this will test all module imports)
        try:
            main_window = MainWindow(db_manager, settings)
            logger.info("Main window created successfully")
            
            # Clean up
            main_window.close()
            main_window.deleteLater()
            
        except Exception as e:
            return False, f"Failed to create main window: {e}"
        
        logger.info("Application startup test passed!")
        return True, "Application startup test passed"
        
    except Exception as e:
        logger.error(f"Error testing application startup: {e}")
        return False, f"Error testing application startup: {e}"


def main():
    """Main setup function."""
    print("=" * 80)
    print("XPanda ERP-Lite - Complete System Setup")
    print("=" * 80)
    
    # Setup scripts to run
    setup_scripts = [
        ('setup_database_tables.py', 'Inventory Database Setup'),
        ('setup_production_tables.py', 'Production Database Setup'),
        ('setup_orders_tables.py', 'Orders Database Setup'),
        ('setup_quality_tables.py', 'Quality Database Setup'),
    ]
    
    results = []
    
    # Run setup scripts
    print("\n1. Running Database Setup Scripts...")
    print("-" * 50)
    
    for script_name, description in setup_scripts:
        success, message = run_setup_script(script_name, description)
        results.append((script_name, success, message))
        print(f"  {description}: {'SUCCESS' if success else 'FAILED'}")
    
    # Verify database tables
    print("\n2. Verifying Database Tables...")
    print("-" * 50)
    
    tables_success, table_errors = verify_database_tables()
    results.append(('database_tables', tables_success, '; '.join(table_errors) if table_errors else 'All tables exist'))
    print(f"  Database Tables: {'SUCCESS' if tables_success else 'FAILED'}")
    
    # Verify module imports
    print("\n3. Verifying Module Imports...")
    print("-" * 50)
    
    imports_success, import_errors = verify_module_imports()
    results.append(('module_imports', imports_success, '; '.join(import_errors) if import_errors else 'All modules imported'))
    print(f"  Module Imports: {'SUCCESS' if imports_success else 'FAILED'}")
    
    # Test application startup
    print("\n4. Testing Application Startup...")
    print("-" * 50)
    
    app_success, app_message = test_application_startup()
    results.append(('application_startup', app_success, app_message))
    print(f"  Application Startup: {'SUCCESS' if app_success else 'FAILED'}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Setup Summary")
    print("=" * 80)
    
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    for script_name, success, message in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  {script_name}: {status}")
        if not success:
            print(f"    Error: {message}")
    
    print(f"\nOverall: {success_count}/{total_count} tasks completed successfully")
    
    if success_count == total_count:
        print("\n" + "!" * 80)
        print("!  XPanda ERP-Lite System Setup Completed Successfully!")
        print("!  The application is ready to use.")
        print("!" * 80)
        print("\nTo start the application, run:")
        print("  python main.py")
        return 0
    else:
        print("\n" + "x" * 80)
        print("x  SETUP INCOMPLETE")
        print("x  Please resolve the errors above and run setup again.")
        print("x" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
