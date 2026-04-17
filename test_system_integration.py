#!/usr/bin/env python3
"""
System Integration Test for XPanda ERP-Lite.
Tests the complete system integration including all modules.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Tuple
from uuid import uuid4

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SystemIntegrationTest:
    """Comprehensive system integration test suite."""
    
    def __init__(self):
        self.db_manager = None
        self.settings = None
        self.test_results: List[Tuple[str, bool, str]] = []
    
    def setup(self) -> bool:
        """Setup test environment."""
        try:
            # Add project root to path
            project_root = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, project_root)
            
            # Import required modules
            from database.connection import DatabaseManager
            from config import config
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QSettings
            
            # Setup database connection
            self.db_manager = DatabaseManager(config.database)
            if not self.db_manager.connect():
                logger.error("Failed to connect to database")
                return False
            
            # Setup settings
            self.settings = QSettings("XPanda Foam", "ERP-Lite")
            
            # Setup QApplication (minimal for testing)
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            logger.info("Test environment setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup test environment."""
        try:
            if self.db_manager:
                self.db_manager.disconnect()
            logger.info("Test environment cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def add_test_result(self, test_name: str, success: bool, message: str = "") -> None:
        """Add a test result."""
        self.test_results.append((test_name, success, message))
        status = "PASS" if success else "FAIL"
        logger.info(f"Test {test_name}: {status} {message}")
    
    def test_database_models(self) -> bool:
        """Test database models can be imported and used."""
        try:
            # Test model imports
            from database.models.inventory import Material, MaterialCategory
            from database.models.production import BillOfMaterial, WorkOrder
            from database.models.orders import Customer, SalesOrder
            from database.models.quality import Inspection, NonConformanceReport
            
            # Test model relationships
            material = Material(
                sku="TEST-MATERIAL",
                name="Test Material",
                description="Test Description",
                unit_of_measure="PCS",
                created_by="test"
            )
            
            self.add_test_result("Database Models Import", True)
            self.add_test_result("Database Model Creation", True)
            return True
            
        except Exception as e:
            self.add_test_result("Database Models Import", False, str(e))
            return False
    
    def test_services_layer(self) -> bool:
        """Test services layer functionality."""
        try:
            # Test service imports
            from modules.inventory.services.inventory_service import InventoryService
            from modules.production.services.production_service import ProductionService
            from modules.orders.services.orders_service import OrdersService
            from modules.quality.services.quality_service import QualityService
            
            # Test service instantiation
            inventory_service = InventoryService(self.db_manager)
            production_service = ProductionService(self.db_manager)
            orders_service = OrdersService(self.db_manager)
            quality_service = QualityService(self.db_manager)
            
            # Test service methods
            inventory_stats = inventory_service.get_inventory_statistics()
            production_stats = production_service.get_production_statistics()
            orders_stats = orders_service.get_orders_statistics()
            quality_stats = quality_service.get_quality_statistics()
            
            self.add_test_result("Services Layer Import", True)
            self.add_test_result("Services Layer Instantiation", True)
            self.add_test_result("Services Layer Methods", True)
            return True
            
        except Exception as e:
            self.add_test_result("Services Layer", False, str(e))
            return False
    
    def test_controllers_layer(self) -> bool:
        """Test controllers layer functionality."""
        try:
            # Test controller imports
            from modules.inventory.controllers.inventory_controller import InventoryController
            from modules.production.controllers.production_controller import ProductionController
            from modules.orders.controllers.orders_controller import OrdersController
            from modules.quality.controllers.quality_controller import QualityController
            
            # Test controller instantiation
            inventory_controller = InventoryController(self.db_manager)
            production_controller = ProductionController(self.db_manager)
            orders_controller = OrdersController(self.db_manager)
            quality_controller = QualityController(self.db_manager)
            
            # Test controller methods
            inventory_dashboard_data = inventory_controller.get_dashboard_data()
            production_dashboard_data = production_controller.get_dashboard_data()
            orders_dashboard_data = orders_controller.get_dashboard_data()
            quality_dashboard_data = quality_controller.get_dashboard_data()
            
            self.add_test_result("Controllers Layer Import", True)
            self.add_test_result("Controllers Layer Instantiation", True)
            self.add_test_result("Controllers Layer Methods", True)
            return True
            
        except Exception as e:
            self.add_test_result("Controllers Layer", False, str(e))
            return False
    
    def test_views_layer(self) -> bool:
        """Test views layer functionality."""
        try:
            # Test view imports
            from modules.inventory.views.inventory_dashboard import InventoryDashboard
            from modules.production.views.production_dashboard import ProductionDashboard
            from modules.orders.views.orders_dashboard import OrdersDashboard
            from modules.quality.views.quality_dashboard import QualityDashboard
            
            # Test view instantiation
            inventory_dashboard = InventoryDashboard(self.db_manager, self.settings)
            production_dashboard = ProductionDashboard(self.db_manager, self.settings)
            orders_dashboard = OrdersDashboard(self.db_manager, self.settings)
            quality_dashboard = QualityDashboard(self.db_manager, self.settings)
            
            # Test view methods
            inventory_dashboard.refresh_data()
            production_dashboard.refresh_data()
            orders_dashboard.refresh_data()
            quality_dashboard.refresh_data()
            
            self.add_test_result("Views Layer Import", True)
            self.add_test_result("Views Layer Instantiation", True)
            self.add_test_result("Views Layer Methods", True)
            return True
            
        except Exception as e:
            self.add_test_result("Views Layer", False, str(e))
            return False
    
    def test_main_window_integration(self) -> bool:
        """Test main window integration."""
        try:
            from ui.main_window import MainWindow
            
            # Create main window
            main_window = MainWindow(self.db_manager, self.settings)
            
            # Test module loading
            modules_to_test = [
                'inventory', 'production', 'orders', 'quality',
                'production_bom', 'production_work_orders',
                'orders_customers', 'orders_processing',
                'quality_inspections', 'quality_ncr'
            ]
            
            for module in modules_to_test:
                widget = main_window.create_module_widget(module)
                if widget is None:
                    self.add_test_result(f"Module {module}", False, "Failed to create widget")
                else:
                    self.add_test_result(f"Module {module}", True)
            
            # Test navigation
            main_window.load_module('inventory')
            main_window.load_module('production')
            main_window.load_module('orders')
            main_window.load_module('quality')
            
            self.add_test_result("Main Window Creation", True)
            self.add_test_result("Main Window Navigation", True)
            
            # Clean up
            main_window.close()
            main_window.deleteLater()
            
            return True
            
        except Exception as e:
            self.add_test_result("Main Window Integration", False, str(e))
            return False
    
    def test_database_crud_operations(self) -> bool:
        """Test basic CRUD operations."""
        try:
            from database.models.inventory import Material
            
            # Test Create
            with self.db_manager.get_session() as session:
                material = Material(
                    sku=f"TEST-{uuid4().hex[:8]}",
                    name="Test Material",
                    description="Test Description",
                    unit_of_measure="PCS",
                    created_by="test"
                )
                session.add(material)
                session.commit()
                material_id = material.id
            
            # Test Read
            with self.db_manager.get_session() as session:
                material = session.query(Material).filter(Material.id == material_id).first()
                if material is None:
                    raise Exception("Failed to read material")
            
            # Test Update
            with self.db_manager.get_session() as session:
                material = session.query(Material).filter(Material.id == material_id).first()
                material.description = "Updated Description"
                session.commit()
            
            # Test Delete
            with self.db_manager.get_session() as session:
                material = session.query(Material).filter(Material.id == material_id).first()
                session.delete(material)
                session.commit()
            
            self.add_test_result("Database CRUD Operations", True)
            return True
            
        except Exception as e:
            self.add_test_result("Database CRUD Operations", False, str(e))
            return False
    
    def test_cross_module_integration(self) -> bool:
        """Test cross-module integration."""
        try:
            # Test that services can work together
            from modules.inventory.services.inventory_service import InventoryService
            from modules.production.services.production_service import ProductionService
            from modules.orders.services.orders_service import OrdersService
            from modules.quality.services.quality_service import QualityService
            
            inventory_service = InventoryService(self.db_manager)
            production_service = ProductionService(self.db_manager)
            orders_service = OrdersService(self.db_manager)
            quality_service = QualityService(self.db_manager)
            
            # Test that all services can get statistics
            inventory_stats = inventory_service.get_inventory_statistics()
            production_stats = production_service.get_production_statistics()
            orders_stats = orders_service.get_orders_statistics()
            quality_stats = quality_service.get_quality_statistics()
            
            # Verify all stats are dictionaries
            assert isinstance(inventory_stats, dict), "Inventory stats should be a dictionary"
            assert isinstance(production_stats, dict), "Production stats should be a dictionary"
            assert isinstance(orders_stats, dict), "Orders stats should be a dictionary"
            assert isinstance(quality_stats, dict), "Quality stats should be a dictionary"
            
            self.add_test_result("Cross-Module Integration", True)
            return True
            
        except Exception as e:
            self.add_test_result("Cross-Module Integration", False, str(e))
            return False
    
    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        print("=" * 80)
        print("XPanda ERP-Lite - System Integration Tests")
        print("=" * 80)
        
        if not self.setup():
            print("Failed to setup test environment")
            return False
        
        try:
            # Run all tests
            print("\nRunning Integration Tests...")
            print("-" * 50)
            
            self.test_database_models()
            self.test_services_layer()
            self.test_controllers_layer()
            self.test_views_layer()
            self.test_main_window_integration()
            self.test_database_crud_operations()
            self.test_cross_module_integration()
            
            # Print results
            print("\n" + "=" * 80)
            print("Test Results")
            print("=" * 80)
            
            success_count = 0
            total_count = len(self.test_results)
            
            for test_name, success, message in self.test_results:
                status = "PASS" if success else "FAIL"
                print(f"  {test_name}: {status}")
                if not success and message:
                    print(f"    Error: {message}")
                if success:
                    success_count += 1
            
            print(f"\nOverall: {success_count}/{total_count} tests passed")
            
            if success_count == total_count:
                print("\n" + "!" * 80)
                print("!  ALL INTEGRATION TESTS PASSED!")
                print("!  System integration is working correctly.")
                print("!" * 80)
                return True
            else:
                print("\n" + "x" * 80)
                print("x  SOME TESTS FAILED")
                print("x  Please review the errors above.")
                print("x" * 80)
                return False
                
        finally:
            self.cleanup()


def main():
    """Main function."""
    test_suite = SystemIntegrationTest()
    success = test_suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
