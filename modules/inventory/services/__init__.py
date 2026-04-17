"""
Inventory services package for XPanda ERP-Lite.
Contains service classes for material and transaction management.
"""

from .material_service import MaterialService
from .transaction_service import TransactionService
from .inventory_service import InventoryService

__all__ = [
    'MaterialService',
    'TransactionService', 
    'InventoryService'
]