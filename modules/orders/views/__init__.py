"""
Orders views package for XPanda ERP-Lite.
Contains view classes for orders management.
"""

from .orders_dashboard import OrdersDashboard
from .customer_management import CustomerManagement
from .order_processing import OrderProcessing

__all__ = [
    'OrdersDashboard',
    'CustomerManagement',
    'OrderProcessing'
]