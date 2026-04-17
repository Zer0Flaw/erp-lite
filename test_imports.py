#!/usr/bin/env python3
"""
Simple test script to check Shop Floor imports
"""

try:
    print("Testing Shop Floor imports...")
    
    # Test database models
    from database.models.shop_floor import TimeEntry, ProductionOutput, ProductionBatch, ProductionStation
    print("✓ Shop Floor models imported successfully")
    
    # Test services
    from modules.shop_floor.services.time_entry_service import TimeEntryService
    from modules.shop_floor.services.production_output_service import ProductionOutputService
    from modules.shop_floor.services.batch_tracking_service import BatchTrackingService
    from modules.shop_floor.services.station_management_service import StationManagementService
    print("✓ Shop Floor services imported successfully")
    
    # Test controller
    from modules.shop_floor.controllers.shop_floor_controller import ShopFloorController
    print("✓ Shop Floor controller imported successfully")
    
    # Test views
    from modules.shop_floor.views.job_clock import JobClockView
    from modules.shop_floor.views.production_recording import ProductionRecordingView
    from modules.shop_floor.views.batch_tracking import BatchTrackingView
    from modules.shop_floor.views.station_management import StationManagementView
    print("✓ Shop Floor views imported successfully")
    
    print("\n🎉 All Shop Floor imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
