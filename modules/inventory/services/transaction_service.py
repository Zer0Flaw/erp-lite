"""
Inventory transaction service for XPanda ERP-Lite.
Handles all inventory movements and stock adjustments.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from database.models.inventory import (
    InventoryTransaction, TransactionType, AdjustmentReason,
    Material, InventorySummary
)
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class TransactionService:
    """Service class for inventory transaction operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_receiving_transaction(self, transaction_data: Dict[str, Any]) -> Optional[InventoryTransaction]:
        """
        Create a receiving transaction for incoming materials.
        
        Args:
            transaction_data: Dictionary containing transaction information
            
        Returns:
            Created InventoryTransaction object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Verify material exists
                material = session.query(Material).filter(
                    Material.id == transaction_data['material_id'],
                    Material.deleted_at.is_(None)
                ).first()
                
                if not material:
                    logger.error(f"Material {transaction_data['material_id']} not found")
                    return None
                
                # Create transaction
                transaction = InventoryTransaction(
                    material_id=transaction_data['material_id'],
                    transaction_type=TransactionType.RECEIVING.value,
                    quantity=Decimal(str(transaction_data['quantity'])),
                    unit_cost=Decimal(str(transaction_data.get('unit_cost', 0))),
                    total_cost=Decimal(str(transaction_data.get('total_cost', 0))),
                    reference_type=transaction_data.get('reference_type', 'PO'),
                    reference_number=transaction_data.get('reference_number'),
                    lot_number=transaction_data.get('lot_number'),
                    batch_number=transaction_data.get('batch_number'),
                    transaction_date=transaction_data.get('transaction_date', datetime.utcnow()),
                    notes=transaction_data.get('notes', ''),
                    created_by=transaction_data.get('created_by', 'System'),
                    posted=True,  # Receiving transactions are posted immediately
                    posted_date=datetime.utcnow()
                )
                
                session.add(transaction)
                session.flush()
                
                # Update inventory summary
                self._update_inventory_summary(session, transaction)
                
                logger.info(f"Created receiving transaction: {transaction.id}")
                return transaction
                
        except Exception as e:
            logger.error(f"Failed to create receiving transaction: {e}")
            return None
    
    def create_adjustment_transaction(self, transaction_data: Dict[str, Any]) -> Optional[InventoryTransaction]:
        """
        Create a stock adjustment transaction.
        
        Args:
            transaction_data: Dictionary containing transaction information
            
        Returns:
            Created InventoryTransaction object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Verify material exists
                material = session.query(Material).filter(
                    Material.id == transaction_data['material_id'],
                    Material.deleted_at.is_(None)
                ).first()
                
                if not material:
                    logger.error(f"Material {transaction_data['material_id']} not found")
                    return None
                
                # Validate adjustment reason
                reason = transaction_data.get('reason_code')
                if reason not in [r.value for r in AdjustmentReason]:
                    logger.error(f"Invalid adjustment reason: {reason}")
                    return None
                
                # Create transaction
                transaction = InventoryTransaction(
                    material_id=transaction_data['material_id'],
                    transaction_type=TransactionType.ADJUSTMENT.value,
                    quantity=Decimal(str(transaction_data['quantity'])),
                    unit_cost=Decimal(str(transaction_data.get('unit_cost', 0))),
                    total_cost=Decimal(str(transaction_data.get('total_cost', 0))),
                    reference_type=transaction_data.get('reference_type', 'ADJ'),
                    reference_number=transaction_data.get('reference_number'),
                    reason_code=reason,
                    transaction_date=transaction_data.get('transaction_date', datetime.utcnow()),
                    notes=transaction_data.get('notes', ''),
                    created_by=transaction_data.get('created_by', 'System'),
                    posted=True,  # Adjustments are posted immediately
                    posted_date=datetime.utcnow()
                )
                
                session.add(transaction)
                session.flush()
                
                # Update inventory summary
                self._update_inventory_summary(session, transaction)
                
                logger.info(f"Created adjustment transaction: {transaction.id}")
                return transaction
                
        except Exception as e:
            logger.error(f"Failed to create adjustment transaction: {e}")
            return None
    
    def create_consumption_transaction(self, transaction_data: Dict[str, Any]) -> Optional[InventoryTransaction]:
        """
        Create a consumption transaction for material usage.
        
        Args:
            transaction_data: Dictionary containing transaction information
            
        Returns:
            Created InventoryTransaction object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Verify material exists
                material = session.query(Material).filter(
                    Material.id == transaction_data['material_id'],
                    Material.deleted_at.is_(None)
                ).first()
                
                if not material:
                    logger.error(f"Material {transaction_data['material_id']} not found")
                    return None
                
                # Create transaction (consumption is always negative quantity)
                quantity = -abs(Decimal(str(transaction_data['quantity'])))
                
                transaction = InventoryTransaction(
                    material_id=transaction_data['material_id'],
                    transaction_type=TransactionType.CONSUMPTION.value,
                    quantity=quantity,
                    unit_cost=Decimal(str(transaction_data.get('unit_cost', 0))),
                    total_cost=Decimal(str(transaction_data.get('total_cost', 0))),
                    reference_type=transaction_data.get('reference_type', 'WO'),
                    reference_number=transaction_data.get('reference_number'),
                    transaction_date=transaction_data.get('transaction_date', datetime.utcnow()),
                    notes=transaction_data.get('notes', ''),
                    created_by=transaction_data.get('created_by', 'System'),
                    posted=True,  # Consumption is posted immediately
                    posted_date=datetime.utcnow()
                )
                
                session.add(transaction)
                session.flush()
                
                # Update inventory summary
                self._update_inventory_summary(session, transaction)
                
                logger.info(f"Created consumption transaction: {transaction.id}")
                return transaction
                
        except Exception as e:
            logger.error(f"Failed to create consumption transaction: {e}")
            return None
    
    def get_transactions_by_material(self, material_id: UUID, limit: int = 100) -> List[InventoryTransaction]:
        """
        Get transactions for a specific material.
        
        Args:
            material_id: UUID of the material
            limit: Maximum number of transactions to return
            
        Returns:
            List of InventoryTransaction objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(InventoryTransaction).filter(
                    InventoryTransaction.material_id == material_id
                ).order_by(InventoryTransaction.transaction_date.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get transactions for material {material_id}: {e}")
            return []
    
    def get_recent_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent transactions across all materials.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction dictionaries with material info
        """
        try:
            with self.db_manager.get_session() as session:
                transactions = session.query(
                    InventoryTransaction, Material
                ).join(
                    Material, InventoryTransaction.material_id == Material.id
                ).filter(
                    Material.deleted_at.is_(None)
                ).order_by(
                    InventoryTransaction.transaction_date.desc()
                ).limit(limit).all()
                
                result = []
                for transaction, material in transactions:
                    result.append({
                        'id': str(transaction.id),
                        'date': transaction.transaction_date.strftime('%Y-%m-%d'),
                        'type': transaction.transaction_type,
                        'material_sku': material.sku,
                        'material_name': material.name,
                        'quantity': float(transaction.quantity),
                        'reference': f"{transaction.reference_type}-{transaction.reference_number}" if transaction.reference_number else "",
                        'notes': transaction.notes or ""
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get recent transactions: {e}")
            return []
    
    def get_transaction_statistics(self) -> Dict[str, Any]:
        """
        Get transaction statistics for dashboard.
        
        Returns:
            Dictionary with transaction statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total transactions today
                today = datetime.utcnow().date()
                today_transactions = session.query(InventoryTransaction).filter(
                    InventoryTransaction.transaction_date >= today
                ).count()
                
                # Receiving transactions this week
                week_ago = datetime.utcnow() - timedelta(days=7)
                weekly_receiving = session.query(InventoryTransaction).filter(
                    InventoryTransaction.transaction_date >= week_ago,
                    InventoryTransaction.transaction_type == TransactionType.RECEIVING.value
                ).count()
                
                # Adjustments this week
                weekly_adjustments = session.query(InventoryTransaction).filter(
                    InventoryTransaction.transaction_date >= week_ago,
                    InventoryTransaction.transaction_type == TransactionType.ADJUSTMENT.value
                ).count()
                
                return {
                    'today_transactions': today_transactions,
                    'weekly_receiving': weekly_receiving,
                    'weekly_adjustments': weekly_adjustments
                }
                
        except Exception as e:
            logger.error(f"Failed to get transaction statistics: {e}")
            return {
                'today_transactions': 0,
                'weekly_receiving': 0,
                'weekly_adjustments': 0
            }
    
    def _update_inventory_summary(self, session, transaction: InventoryTransaction) -> None:
        """
        Update inventory summary based on transaction.
        
        Args:
            session: Database session
            transaction: InventoryTransaction to process
        """
        try:
            # Get or create inventory summary
            summary = session.query(InventorySummary).filter(
                InventorySummary.material_id == transaction.material_id
            ).first()
            
            if not summary:
                summary = InventorySummary(
                    material_id=transaction.material_id,
                    on_hand=Decimal('0'),
                    committed=Decimal('0'),
                    available=Decimal('0'),
                    on_order=Decimal('0'),
                    total_value=Decimal('0'),
                    average_unit_cost=Decimal('0')
                )
                session.add(summary)
                session.flush()
            
            # Update quantities based on transaction type
            if transaction.transaction_type == TransactionType.RECEIVING.value:
                summary.on_hand += transaction.quantity
                summary.available += transaction.quantity
            elif transaction.transaction_type == TransactionType.ADJUSTMENT.value:
                summary.on_hand += transaction.quantity
                summary.available += transaction.quantity
            elif transaction.transaction_type == TransactionType.CONSUMPTION.value:
                summary.on_hand += transaction.quantity  # quantity is negative
                summary.available += transaction.quantity  # quantity is negative
            
            # Update cost information
            if transaction.unit_cost and transaction.unit_cost > 0:
                # Update average cost using weighted average
                if summary.on_hand > 0:
                    current_value = summary.average_unit_cost * (summary.on_hand - transaction.quantity)
                    new_value = transaction.total_cost or (transaction.unit_cost * transaction.quantity)
                    summary.average_unit_cost = (current_value + new_value) / summary.on_hand
                else:
                    summary.average_unit_cost = transaction.unit_cost
            
            # Update total value
            summary.total_value = summary.on_hand * summary.average_unit_cost
            summary.last_transaction_date = transaction.transaction_date
            summary.last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to update inventory summary: {e}")
            raise
