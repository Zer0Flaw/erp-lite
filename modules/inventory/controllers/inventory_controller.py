"""
Inventory controller for XPanda ERP-Lite.
Bridges UI components with inventory services and handles business logic coordination.
"""

import logging
from typing import List, Optional, Dict, Any, Callable
from uuid import UUID

from database.connection import DatabaseManager
from .services.inventory_service import InventoryService
from .services.material_service import MaterialService
from .services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class InventoryController:
    """Controller class for inventory operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.inventory_service = InventoryService(db_manager)
        self.material_service = MaterialService(db_manager)
        self.transaction_service = TransactionService(db_manager)
        
        # Callbacks for UI updates
        self._data_changed_callbacks: List[Callable] = []
        self._status_message_callbacks: List[Callable[[str, int], None]] = []
    
    def register_data_changed_callback(self, callback: Callable) -> None:
        """Register a callback for data change notifications."""
        self._data_changed_callbacks.append(callback)
    
    def register_status_message_callback(self, callback: Callable[[str, int], None]) -> None:
        """Register a callback for status message notifications."""
        self._status_message_callbacks.append(callback)
    
    def _notify_data_changed(self) -> None:
        """Notify all registered callbacks that data has changed."""
        for callback in self._data_changed_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in data changed callback: {e}")
    
    def _show_status_message(self, message: str, timeout: int = 3000) -> None:
        """Show status message through registered callbacks."""
        for callback in self._status_message_callbacks:
            try:
                callback(message, timeout)
            except Exception as e:
                logger.error(f"Error in status message callback: {e}")
    
    # Material Management Methods
    
    def create_material(self, material_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a new material.
        
        Args:
            material_data: Dictionary containing material information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate required fields
            required_fields = ['sku', 'name', 'created_by']
            missing_fields = [field for field in required_fields if field not in material_data]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Create material
            material = self.material_service.create_material(material_data)
            
            if material:
                self._notify_data_changed()
                self._show_status_message(f"Material '{material.sku}' created successfully")
                return True, f"Material '{material.sku}' created successfully"
            else:
                return False, "Failed to create material"
                
        except Exception as e:
            logger.error(f"Error creating material: {e}")
            return False, f"Error creating material: {e}"
    
    def update_material(self, material_id: UUID, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing material.
        
        Args:
            material_id: UUID of the material to update
            update_data: Dictionary containing updated fields
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.material_service.update_material(material_id, update_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Material updated successfully")
                return True, "Material updated successfully"
            else:
                return False, "Failed to update material"
                
        except Exception as e:
            logger.error(f"Error updating material: {e}")
            return False, f"Error updating material: {e}"
    
    def delete_material(self, material_id: UUID, deleted_by: str) -> Tuple[bool, str]:
        """
        Delete a material (soft delete).
        
        Args:
            material_id: UUID of the material to delete
            deleted_by: User performing the deletion
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.material_service.delete_material(material_id, deleted_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Material deleted successfully")
                return True, "Material deleted successfully"
            else:
                return False, "Failed to delete material"
                
        except Exception as e:
            logger.error(f"Error deleting material: {e}")
            return False, f"Error deleting material: {e}"
    
    def get_material_by_id(self, material_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get material details by ID.
        
        Args:
            material_id: UUID of the material
            
        Returns:
            Material dictionary or None if not found
        """
        try:
            material = self.material_service.get_material_by_id(material_id)
            if material:
                return {
                    'id': str(material.id),
                    'sku': material.sku,
                    'name': material.name,
                    'description': material.description or '',
                    'category': material.category,
                    'unit_of_measure': material.unit_of_measure,
                    'weight_per_unit': float(material.weight_per_unit) if material.weight_per_unit else None,
                    'dimensions': material.dimensions,
                    'reorder_point': float(material.reorder_point) if material.reorder_point else 0,
                    'max_stock_level': float(material.max_stock_level) if material.max_stock_level else None,
                    'preferred_supplier': material.preferred_supplier,
                    'storage_location': material.storage_location,
                    'standard_cost': float(material.standard_cost) if material.standard_cost else None,
                    'average_cost': float(material.average_cost) if material.average_cost else None,
                    'last_cost': float(material.last_cost) if material.last_cost else None,
                    'expansion_ratio': float(material.expansion_ratio) if material.expansion_ratio else None,
                    'density_target': float(material.density_target) if material.density_target else None,
                    'mold_id': material.mold_id,
                    'active': material.active,
                    'notes': material.notes or ''
                }
            return None
        except Exception as e:
            logger.error(f"Error getting material {material_id}: {e}")
            return None
    
    def search_materials(self, search_term: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search materials.
        
        Args:
            search_term: Search term
            category: Optional category filter
            
        Returns:
            List of material dictionaries
        """
        try:
            materials = self.material_service.search_materials(search_term, category)
            
            return [
                {
                    'id': str(material.id),
                    'sku': material.sku,
                    'name': material.name,
                    'description': material.description or '',
                    'category': material.category,
                    'unit_of_measure': material.unit_of_measure,
                    'reorder_point': float(material.reorder_point) if material.reorder_point else 0,
                    'storage_location': material.storage_location or '',
                    'active': material.active
                }
                for material in materials
            ]
        except Exception as e:
            logger.error(f"Error searching materials: {e}")
            return []
    
    # Transaction Management Methods
    
    def create_receiving_transaction(self, transaction_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a receiving transaction.
        
        Args:
            transaction_data: Dictionary containing transaction information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate transaction
            is_valid, errors = self.inventory_service.validate_transaction(transaction_data)
            
            if not is_valid:
                return False, f"Validation errors: {', '.join(errors)}"
            
            # Create transaction
            transaction = self.transaction_service.create_receiving_transaction(transaction_data)
            
            if transaction:
                self._notify_data_changed()
                self._show_status_message(f"Receiving transaction created: {transaction.quantity} units")
                return True, f"Receiving transaction created: {transaction.quantity} units"
            else:
                return False, "Failed to create receiving transaction"
                
        except Exception as e:
            logger.error(f"Error creating receiving transaction: {e}")
            return False, f"Error creating receiving transaction: {e}"
    
    def create_adjustment_transaction(self, transaction_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create an adjustment transaction.
        
        Args:
            transaction_data: Dictionary containing transaction information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate transaction
            is_valid, errors = self.inventory_service.validate_transaction(transaction_data)
            
            if not is_valid:
                return False, f"Validation errors: {', '.join(errors)}"
            
            # Create transaction
            transaction = self.transaction_service.create_adjustment_transaction(transaction_data)
            
            if transaction:
                self._notify_data_changed()
                self._show_status_message(f"Adjustment transaction created: {transaction.quantity} units")
                return True, f"Adjustment transaction created: {transaction.quantity} units"
            else:
                return False, "Failed to create adjustment transaction"
                
        except Exception as e:
            logger.error(f"Error creating adjustment transaction: {e}")
            return False, f"Error creating adjustment transaction: {e}"
    
    # Dashboard and Reporting Methods
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data for inventory module.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            return self.inventory_service.get_dashboard_data()
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                'summary_cards': {
                    'total_skus': 0,
                    'low_stock_items': 0,
                    'total_value': "$0.00",
                    'recent_receiving': 0
                },
                'recent_activity': [],
                'low_stock_materials': [],
                'category_breakdown': {}
            }
    
    def get_inventory_summary(self, material_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get complete inventory summary for a material.
        
        Args:
            material_id: UUID of the material
            
        Returns:
            Dictionary with inventory information or None if not found
        """
        try:
            return self.inventory_service.get_inventory_summary(material_id)
        except Exception as e:
            logger.error(f"Error getting inventory summary: {e}")
            return None
    
    def get_recent_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent inventory transactions.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction dictionaries
        """
        try:
            return self.transaction_service.get_recent_transactions(limit)
        except Exception as e:
            logger.error(f"Error getting recent transactions: {e}")
            return []
    
    def get_material_options(self) -> List[Dict[str, str]]:
        """
        Get material options for dropdowns.
        
        Returns:
            List of material dictionaries with basic info
        """
        try:
            return self.inventory_service.get_material_options()
        except Exception as e:
            logger.error(f"Error getting material options: {e}")
            return []
    
    def get_material_categories(self) -> List[str]:
        """
        Get all material categories.
        
        Returns:
            List of category names
        """
        try:
            return self.material_service.get_material_categories()
        except Exception as e:
            logger.error(f"Error getting material categories: {e}")
            return []
    
    def get_low_stock_materials(self) -> List[Dict[str, Any]]:
        """
        Get materials that are below reorder point.
        
        Returns:
            List of material dictionaries
        """
        try:
            materials = self.material_service.get_low_stock_materials()
            
            return [
                {
                    'id': str(material.id),
                    'sku': material.sku,
                    'name': material.name,
                    'category': material.category,
                    'reorder_point': float(material.reorder_point) if material.reorder_point else 0,
                    'storage_location': material.storage_location or ''
                }
                for material in materials
            ]
        except Exception as e:
            logger.error(f"Error getting low stock materials: {e}")
            return []
