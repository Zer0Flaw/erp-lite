#!/usr/bin/env python3
"""
Create initial database migration for XPanda ERP-Lite.
"""

import os
import sys

def create_initial_migration():
    """Create the initial Alembic migration."""
    try:
        # Change to project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Import and use the database manager
        from utils.db_manager import DatabaseUtility
        
        db_util = DatabaseUtility()
        
        print("Creating initial database migration...")
        
        # Create migration
        success = db_util.create_migration("Initial schema - inventory tables")
        
        if success:
            print("Migration created successfully!")
            print("Now run: python utils/db_manager.py migrate")
            return 0
        else:
            print("Failed to create migration")
            return 1
            
    except Exception as e:
        print(f"Error creating migration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(create_initial_migration())
