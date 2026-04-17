#!/usr/bin/env python3
"""
Run database migration for XPanda ERP-Lite.
"""

import os
import sys

def run_migration():
    """Run the Alembic migration to create database tables."""
    try:
        # Change to project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Import and use the database manager
        from utils.db_manager import DatabaseUtility
        
        db_util = DatabaseUtility()
        
        print("Running database migration...")
        
        # Run migration
        success = db_util.run_migrations()
        
        if success:
            print("Migration completed successfully!")
            print("Database tables have been created.")
            return 0
        else:
            print("Failed to run migration")
            return 1
            
    except Exception as e:
        print(f"Error running migration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_migration())
