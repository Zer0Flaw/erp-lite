"""
Main inventory service for XPanda ERP-Lite.
Coordinates material and transaction operations for complete inventory management.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import func
from database.models.inventory import (
    Material, InventoryTransaction, InventorySummary, TransactionType
)
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

        Returns:
            Dict with 'material' and 'inventory' keys, or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                material = session.query(Material).filter(
                    Material.id == material_id,
                    Material.deleted_at.is_(None)
                ).first()

                if not material:
                    return None

                summary = session.query(InventorySummary).filter(
                    InventorySummary.material_id == material_id
                ).first()

                return {
                    'material': {
                        'id': str(material.id),
                        'sku': material.sku,
                        'name': material.name,
                        'description': material.description or '',
                        'category': material.category,
                        'unit_of_measure': material.unit_of_measure,
                        'reorder_point': float(material.reorder_point or 0),
                        'storage_location': material.storage_location or '',
                        'preferred_supplier': material.preferred_supplier or '',
                        'standard_cost': float(material.standard_cost) if material.standard_cost else None,
                        'notes': material.notes or ''
                    },
                    'inventory': {
                        'on_hand': float(summary.on_hand) if summary else 0.0,
                        'committed': float(summary.committed) if summary else 0.0,
                        'available': float(summary.available) if summary else 0.0,
                        'on_order': float(summary.on_order) if summary else 0.0,
                        'total_value': float(summary.total_value) if summary else 0.0,
                        'average_cost': float(summary.average_unit_cost) if summary else 0.0,
                    }
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
            with self.db_manager.get_session() as session:
                # Total active SKUs
                total_skus = session.query(Material).filter(
                    Material.deleted_at.is_(None),
                    Material.active == True
                ).count()

                # Total inventory value from InventorySummary
                total_value = session.query(
                    func.sum(InventorySummary.total_value)
                ).join(
                    Material, InventorySummary.material_id == Material.id
                ).filter(
                    Material.deleted_at.is_(None),
                    Material.active == True
                ).scalar() or 0

                # Low stock: available <= reorder_point (and reorder_point > 0)
                low_stock_count = session.query(InventorySummary).join(
                    Material, InventorySummary.material_id == Material.id
                ).filter(
                    Material.deleted_at.is_(None),
                    Material.active == True,
                    Material.reorder_point > 0,
                    InventorySummary.available <= Material.reorder_point
                ).count()

                # Receiving transactions in the last 7 days
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_receiving = session.query(InventoryTransaction).filter(
                    InventoryTransaction.transaction_type == TransactionType.RECEIVING.value,
                    InventoryTransaction.transaction_date >= week_ago
                ).count()

                # Low stock material list (top 10)
                low_stock_rows = session.query(Material, InventorySummary).join(
                    InventorySummary, InventorySummary.material_id == Material.id
                ).filter(
                    Material.deleted_at.is_(None),
                    Material.active == True,
                    Material.reorder_point > 0,
                    InventorySummary.available <= Material.reorder_point
                ).limit(10).all()

            # Recent activity is fetched via its own session
            recent_transactions = self.transaction_service.get_recent_transactions(limit=10)

            return {
                'summary_cards': {
                    'total_skus': total_skus,
                    'low_stock_items': low_stock_count,
                    'total_value': f"${float(total_value):,.2f}",
                    'recent_receiving': recent_receiving
                },
                'recent_activity': recent_transactions,
                'low_stock_materials': [
                    {
                        'sku': m.sku,
                        'name': m.name,
                        'category': m.category,
                        'reorder_point': float(m.reorder_point or 0),
                        'on_hand': float(s.on_hand),
                        'available': float(s.available)
                    }
                    for m, s in low_stock_rows
                ],
                'category_breakdown': {}
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
        Search inventory with stock levels from InventorySummary.

        Args:
            search_term: Search term for SKU, name, or description
            filters: Optional dict with keys 'category', 'low_stock'

        Returns:
            List of material dicts including on_hand, available, and status
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Material, InventorySummary).outerjoin(
                    InventorySummary, InventorySummary.material_id == Material.id
                ).filter(
                    Material.deleted_at.is_(None),
                    Material.active == True
                )

                if search_term:
                    pattern = f"%{search_term}%"
                    query = query.filter(
                        (Material.sku.ilike(pattern)) |
                        (Material.name.ilike(pattern)) |
                        (Material.description.ilike(pattern))
                    )

                if filters and filters.get('category'):
                    query = query.filter(Material.category == filters['category'])

                query = query.order_by(Material.sku)

                results = []
                for material, summary in query.all():
                    on_hand = float(summary.on_hand) if summary else 0.0
                    available = float(summary.available) if summary else 0.0
                    reorder_point = float(material.reorder_point) if material.reorder_point else 0.0

                    is_low = reorder_point > 0 and available <= reorder_point
                    if filters and filters.get('low_stock') and not is_low:
                        continue

                    results.append({
                        'id': str(material.id),
                        'sku': material.sku,
                        'description': material.name,
                        'category': material.category,
                        'on_hand': on_hand,
                        'available': available,
                        'status': 'Low Stock' if is_low else 'Normal',
                        'storage_location': material.storage_location or '',
                        'reorder_point': reorder_point,
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
