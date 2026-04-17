"""
Quality views package for XPanda ERP-Lite.
Contains view classes for quality management.
"""

from .quality_dashboard import QualityDashboard
from .inspection_management import InspectionManagement
from .ncr_tracking import NCRTracking

__all__ = [
    'QualityDashboard',
    'InspectionManagement',
    'NCRTracking'
]