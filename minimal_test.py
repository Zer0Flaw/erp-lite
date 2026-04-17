"""
Minimal test to isolate import issues
"""

print("Starting minimal import test...")

try:
    # Test database connection import first
    from database.connection import DatabaseManager
    print("✓ DatabaseManager imported successfully")
    
    # Test shop floor models
    from database.models.shop_floor import TimeEntry
    print("✓ TimeEntry model imported successfully")
    
    # Test service import
    from modules.shop_floor.services.time_entry_service import TimeEntryService
    print("✓ TimeEntryService imported successfully")
    
    print("All basic imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
