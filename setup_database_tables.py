#!/usr/bin/env python3
"""
Setup database tables for XPanda ERP-Lite.
Runs the initial migration to create all database tables.
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database():
    """Setup database tables using SQLAlchemy directly."""
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import required modules
        from database.connection import DatabaseManager
        from database.models.inventory import Material, InventoryTransaction, MaterialSupplier, InventorySummary, StockAdjustment
        from database.models import Base
        from config import config
        
        logger.info("Setting up database tables...")
        
        # Create database manager
        db_manager = DatabaseManager(config.database)
        
        # Connect to database
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return 1
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(db_manager.engine)
        
        logger.info("Database tables created successfully!")
        
        # Verify tables were created
        with db_manager.engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result]
            
            logger.info(f"Tables created: {', '.join(tables)}")
        
        db_manager.disconnect()
        
        logger.info("Database setup completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(setup_database())
