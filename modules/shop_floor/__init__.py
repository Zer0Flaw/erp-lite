"""
Shop Floor Module Package for XPanda ERP-Lite.
Provides shop floor management capabilities including time tracking,
production recording, batch traceability, and station management.
"""

from .controllers import ShopFloorController
from .services import (
    TimeEntryService,
    ProductionOutputService,
    BatchTrackingService,
    StationManagementService
)
from .views import (
    JobClockView,
    ProductionRecordingView,
    BatchTrackingView,
    StationManagementView
)

__all__ = [
    'ShopFloorController',
    'TimeEntryService',
    'ProductionOutputService',
    'BatchTrackingService',
    'StationManagementService',
    'JobClockView',
    'ProductionRecordingView',
    'BatchTrackingView',
    'StationManagementView'
]
