"""
Production views package for XPanda ERP-Lite.
Contains view classes for production management.
"""

from .production_dashboard import ProductionDashboard
from .bom_editor import BOMEditor
from .work_order_management import WorkOrderManagement

__all__ = [
    'ProductionDashboard',
    'BOMEditor',
    'WorkOrderManagement'
]