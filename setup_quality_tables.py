#!/usr/bin/env python3
"""
Setup quality database tables for XPanda ERP-Lite.
Runs the quality migration to create quality-related tables.
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_quality_tables():
    """Setup quality database tables using SQLAlchemy directly."""
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import required modules
        from database.connection import DatabaseManager
        from database.models.quality import (
            Inspection, InspectionLine, NonConformanceReport, 
            CAPAAction, QualityMetric
        )
        from database.models import Base
        from config import config
        
        logger.info("Setting up quality database tables...")
        
        # Create database manager
        db_manager = DatabaseManager(config.database)
        
        # Connect to database
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return 1
        
        # Create all quality tables
        logger.info("Creating quality database tables...")
        Base.metadata.create_all(db_manager.engine)
        
        logger.info("Quality database tables created successfully!")
        
        # Verify tables were created
        with db_manager.engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND (tablename LIKE '%inspection%' OR tablename LIKE '%ncr%' OR tablename LIKE '%capa%' OR tablename LIKE '%quality%')"))
            quality_tables = [row[0] for row in result]
            
            logger.info(f"Quality tables created: {', '.join(quality_tables)}")
        
        db_manager.disconnect()
        
        logger.info("Quality database setup completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error setting up quality database: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(setup_quality_tables())
