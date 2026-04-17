import sys
sys.path.insert(0, '.')

print("Testing imports step by step...")

try:
    print("1. Testing database.connection import...")
    from database.connection import DatabaseManager
    print("   ✓ DatabaseManager imported")
    
    print("2. Testing shop floor models...")
    from database.models.shop_floor import TimeEntry, ProductionOutput, ProductionBatch, ProductionStation
    print("   ✓ Shop floor models imported")
    
    print("3. Testing time entry service...")
    from modules.shop_floor.services.time_entry_service import TimeEntryService
    print("   ✓ TimeEntryService imported")
    
    print("4. Testing shop floor controller...")
    from modules.shop_floor.controllers.shop_floor_controller import ShopFloorController
    print("   ✓ ShopFloorController imported")
    
    print("5. Testing job clock view...")
    from modules.shop_floor.views.job_clock import JobClockView
    print("   ✓ JobClockView imported")
    
    print("\n🎉 All Shop Floor imports successful!")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
