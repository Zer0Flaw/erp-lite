"""
Main inventory service for XPanda ERP-Lite.
Coordinates material and transaction operations for complete inventory management.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from database.models.inventory import Material, InventoryTransaction, InventorySummary
from database.connection import DatabaseManager
from .material_service import MaterialService
from .transaction_service import TransactionService

logger = logging.getLogger(__name__)


class InventoryService:
    """Main service class for inventory operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.material_service = MaterialService(db_manager)
        self.transaction_service = TransactionService(db_manager)
    
    def receive_materials(self, receiving_data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Process material receiving for multiple items.
        
        Args:
            receiving_data: List of dictionaries containing receiving information
            
        Returns:
            Tuple of (success: bool, messages: List[str])
        """
        messages = []
        success_count = 0
        
        try:
            with self.db_manager.get_session() as session:
                for item_data in receiving_data:
                    try:
                        # Create receiving transaction
                        transaction = self.transaction_service.create_receiving_transaction(item_data)
                        
                        if transaction:
                            success_count += 1
                            messages.append(f"Successfully received: {item_data.get('quantity')} units")
                        else:
                            messages.append(f"Failed to receive: {item_data.get('material_id')}")
                            
                    except Exception as e:
                        messages.append(f"Error receiving item: {e}")
                        logger.error(f"Error in receiving item: {e}")
                
                return success_count == len(receiving_data), messages
                
        except Exception as e:
            logger.error(f"Failed to process materials receiving: {e}")
            return False, [f"Receiving failed: {e}"]
    
    def adjust_stock(self, adjustment_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Process stock adjustment.
        
        Args:
            adjustment_data: Dictionary containing adjustment information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Create adjustment transaction
            transaction = self.transaction_service.create_adjustment_transaction(adjustment_data)
            
            if transaction:
                return True, f"Stock adjustment completed: {adjustment_data.get('quantity')} units"
            else:
                return False, "Failed to create adjustment transaction"
                
        except Exception as e:
            logger.error(f"Failed to adjust stock: {e}")
            return False, f"Stock adjustment failed: {e}"
    
    def consume_material(self, consumption_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Process material consumption for production.
        
        Args:
            consumption_data: Dictionary containing consumption information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if sufficient stock is available
            material = self.material_service.get_material_by_id(consumption_data['material_id'])
            if not material:
                return False, "Material not found"
            
            # Get current stock (placeholder - would use inventory summary)
            current_stock = 100  # This would come from inventory summary
            
            if current_stock < consumption_data['quantity']:
                return False, f"Insufficient stock. Available: {current_stock}, Required: {consumption_data['quantity']}"
            
            # Create consumption transaction
            transaction = self.transaction_service.create_consumption_transaction(consumption_data)
            
            if transaction:
                return True, f"Material consumed: {consumption_data.get('quantity')} units"
            else:
                return False, "Failed to create consumption transaction"
                
        except Exception as e:
            logger.error(f"Failed to consume material: {e}")
            return False, f"Material consumption failed: {e}"
    
    def get_inventory_summary(self, material_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get complete inventory summary for a material.
        
        Args:
            material_id: UUID of the material
            
        Returns:
            Dictionary with inventory information or None if not found
        """
        try:
            material = self.material_service.get_material_by_id(material_id)
            if not material:
                return None
            
            # Get recent transactions
            transactions = self.transaction_service.get_transactions_by_material(material_id, limit=10)
            
            # Get inventory summary (placeholder - would use actual summary table)
            summary_data = {
                'on_hand': 100,  # Placeholder
                'committed': 0,
                'available': 100,
                'on_order': 0,
                'total_value': 1000.00,  # Placeholder
                'average_cost': 10.00  # Placeholder
            }
            
            return {
                'material': {
                    'id': str(material.id),
                    'sku': material.sku,
                    'name': material.name,
                    'description': material.description,
                    'category': material.category,
                    'unit_of_measure': material.unit_of_measure,
                    'reorder_point': float(material.reorder_point or 0),
                    'storage_location': material.storage_location,
                    'notes': material.notes
                },
                'inventory': summary_data,
                'recent_transactions': [
                    {
                        'date': t.transaction_date.strftime('%Y-%m-%d'),
                        'type': t.transaction_type,
                        'quantity': float(t.quantity),
                        'reference': f"{t.reference_type}-{t.reference_number}" if t.reference_number else "",
                        'notes': t.notes or ""
                    }
                    for t in transactions
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get inventory summary for {material_id}: {e}")
            return None
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for inventory module.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            # Material statistics
            material_stats = self.material_service.get_material_statistics()
            
            # Transaction statistics
            transaction_stats = self.transaction_service.get_transaction_statistics()
            
            # Recent transactions
            recent_transactions = self.transaction_service.get_recent_transactions(limit=10)
            
            # Low stock materials
            low_stock_materials = self.material_service.get_low_stock_materials()
            
            # Calculate total inventory value (placeholder)
            total_value = 0.0
            for material in self.material_service.get_all_materials():
                # This would use actual inventory summary data
                total_value += 1000.00  # Placeholder
            
            return {
                'summary_cards': {
                    'total_skus': material_stats['total_materials'],
                    'low_stock_items': material_stats['low_stock_count'],
                    'total_value': f"${total_value:,.2f}",
                    'recent_receiving': transaction_stats['weekly_receiving']
                },
                'recent_activity': recent_transactions,
                'low_stock_materials': [
                    {
                        'sku': m.sku,
                        'name': m.name,
                        'category': m.category,
                        'reorder_point': float(m.reorder_point or 0),
                        'current_stock': 50  # Placeholder - would use actual stock
                    }
                    for m in low_stock_materials[:10]
                ],
                'category_breakdown': material_stats['category_counts']
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
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
    
    def search_inventory(self, search_term: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search inventory with optional filters.
        
        Args:
            search_term: Search term for materials
            filters: Optional filters (category, low_stock, etc.)
            
        Returns:
            List of material dictionaries with inventory information
        """
        try:
            # Get materials matching search
            materials = self.material_service.search_materials(
                search_term, 
                filters.get('category') if filters else None
            )
            
            results = []
            for material in materials:
                # Apply additional filters
                if filters:
                    if filters.get('low_stock') and not material.is_low_stock:
                        continue
                
                # Get inventory data (placeholder)
                inventory_data = {
                    'on_hand': 100,  # Placeholder
                    'available': 100,
                    'status': 'Normal' if not material.is_low_stock else 'Low Stock'
                }
                
                results.append({
                    'id': str(material.id),
                    'sku': material.sku,
                    'description': material.description,
                    'category': material.category,
                    'on_hand': inventory_data['on_hand'],
                    'available': inventory_data['available'],
                    'status': inventory_data['status'],
                    'reorder_point': float(material.reorder_point or 0),
                    'storage_location': material.storage_location or ''
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search inventory: {e}")
            return []
    
    def get_material_options(self) -> List[Dict[str, str]]:
        """
        Get material options for dropdowns and autocomplete.
        
        Returns:
            List of material dictionaries with basic info
        """
        try:
            materials = self.material_service.get_all_materials(active_only=True)
            
            return [
                {
                    'id': str(material.id),
                    'sku': material.sku,
                    'name': material.name,
                    'description': material.description or '',
                    'category': material.category,
                    'unit_of_measure': material.unit_of_measure
                }
                for material in materials
            ]
            
        except Exception as e:
            logger.error(f"Failed to get material options: {e}")
            return []
    
    def validate_transaction(self, transaction_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate transaction data before processing.
        
        Args:
            transaction_data: Transaction data to validate
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Check required fields
        if 'material_id' not in transaction_data:
            errors.append("Material ID is required")
        
        if 'quantity' not in transaction_data:
            errors.append("Quantity is required")
        elif not isinstance(transaction_data['quantity'], (int, float, str)) or float(transaction_data['quantity']) == 0:
            errors.append("Quantity must be a non-zero number")
        
        if 'transaction_type' not in transaction_data:
            errors.append("Transaction type is required")
        
        # Validate material exists
        if 'material_id' in transaction_data:
            material = self.material_service.get_material_by_id(transaction_data['material_id'])
            if not material:
                errors.append("Material not found")
        
        # Validate transaction type specific requirements
        transaction_type = transaction_data.get('transaction_type')
        if transaction_type == 'Adjustment' and 'reason_code' not in transaction_data:
            errors.append("Reason code is required for adjustments")
        
        return len(errors) == 0, errors
