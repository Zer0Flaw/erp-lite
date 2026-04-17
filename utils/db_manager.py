"""
Database management utility for XPanda ERP-Lite.
Provides helper functions for database setup, migrations, and maintenance.
"""

import os
import sys
import logging
from typing import Optional
from subprocess import run, PIPE

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from database.connection import DatabaseManager
from database.models import *

logger = logging.getLogger(__name__)


class DatabaseUtility:
    """Utility class for database management operations."""
    
    def __init__(self):
        self.db_manager = DatabaseManager(config.database)
    
    def setup_database(self) -> bool:
        """
        Set up the database from scratch.
        Creates tables and runs initial migrations.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Setting up database...")
            
            # Connect to database
            if not self.db_manager.connect():
                logger.error("Failed to connect to database")
                return False
            
            # Create initial migration
            if not self.create_initial_migration():
                logger.error("Failed to create initial migration")
                return False
            
            # Run migrations
            if not self.run_migrations():
                logger.error("Failed to run migrations")
                return False
            
            logger.info("Database setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return False
        finally:
            self.db_manager.disconnect()
    
    def create_initial_migration(self) -> bool:
        """
        Create the initial Alembic migration.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if migrations directory exists and has files
            versions_dir = "database/migrations/versions"
            if not os.path.exists(versions_dir):
                os.makedirs(versions_dir)
            
            # Check if we already have migrations
            existing_migrations = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
            if existing_migrations:
                logger.info("Migrations already exist, skipping initial migration")
                return True
            
            # Create initial migration using Alembic
            result = run([
                sys.executable, "-m", "alembic", 
                "revision", "--autogenerate", "-m", "Initial schema"
            ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if result.returncode == 0:
                logger.info("Initial migration created successfully")
                return True
            else:
                logger.error(f"Alembic command failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create initial migration: {e}")
            return False
    
    def run_migrations(self) -> bool:
        """
        Run all pending database migrations.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Run Alembic upgrade
            result = run([
                sys.executable, "-m", "alembic", 
                "upgrade", "head"
            ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if result.returncode == 0:
                logger.info("Database migrations completed successfully")
                return True
            else:
                logger.error(f"Migration failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            return False
    
    def create_migration(self, message: str) -> bool:
        """
        Create a new migration with the given message.
        
        Args:
            message: Migration message/description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = run([
                sys.executable, "-m", "alembic", 
                "revision", "--autogenerate", "-m", message
            ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if result.returncode == 0:
                logger.info(f"Migration '{message}' created successfully")
                return True
            else:
                logger.error(f"Failed to create migration: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return False
    
    def downgrade_migration(self, revision: str = "-1") -> bool:
        """
        Downgrade database to a specific revision.
        
        Args:
            revision: Target revision (default: one step back)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = run([
                sys.executable, "-m", "alembic", 
                "downgrade", revision
            ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if result.returncode == 0:
                logger.info(f"Database downgraded to revision {revision}")
                return True
            else:
                logger.error(f"Downgrade failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to downgrade: {e}")
            return False
    
    def get_migration_history(self) -> Optional[list]:
        """
        Get the history of database migrations.
        
        Returns:
            List of migration revisions or None if failed
        """
        try:
            result = run([
                sys.executable, "-m", "alembic", 
                "history", "--verbose"
            ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if result.returncode == 0:
                return result.stdout.split('\n')
            else:
                logger.error(f"Failed to get migration history: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return None
    
    def get_current_revision(self) -> Optional[str]:
        """
        Get the current database revision.
        
        Returns:
            Current revision string or None if failed
        """
        try:
            result = run([
                sys.executable, "-m", "alembic", 
                "current"
            ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Failed to get current revision: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def reset_database(self) -> bool:
        """
        Reset the database by dropping all tables and recreating them.
        WARNING: This will delete all data!
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.warning("Resetting database - all data will be lost!")
            
            if not self.db_manager.connect():
                return False
            
            # Drop all tables
            if not self.db_manager.drop_tables():
                return False
            
            # Run migrations to recreate schema
            if not self.run_migrations():
                return False
            
            logger.info("Database reset completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            return False
        finally:
            self.db_manager.disconnect()
    
    def check_database_health(self) -> dict:
        """
        Check database health and status.
        
        Returns:
            Dictionary with health status information
        """
        health_info = {
            'connected': False,
            'current_revision': None,
            'tables_count': 0,
            'errors': []
        }
        
        try:
            # Check connection
            health_info['connected'] = self.db_manager.check_connection()
            
            if health_info['connected']:
                # Get current revision
                health_info['current_revision'] = self.get_current_revision()
                
                # Count tables
                with self.db_manager.get_session() as session:
                    from sqlalchemy import inspect
                    inspector = inspect(session.bind)
                    health_info['tables_count'] = len(inspector.get_table_names())
            else:
                health_info['errors'].append("Database connection failed")
                
        except Exception as e:
            health_info['errors'].append(f"Health check failed: {e}")
            logger.error(f"Database health check failed: {e}")
        
        return health_info


def main():
    """Command-line interface for database management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="XPanda ERP-Lite Database Management Utility")
    parser.add_argument("command", choices=[
        "setup", "migrate", "create-migration", "downgrade", 
        "history", "current", "reset", "health"
    ], help="Command to execute")
    parser.add_argument("--message", help="Migration message (for create-migration)")
    parser.add_argument("--revision", help="Target revision (for downgrade)")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    utility = DatabaseUtility()
    
    if args.command == "setup":
        success = utility.setup_database()
    elif args.command == "migrate":
        success = utility.run_migrations()
    elif args.command == "create-migration":
        if not args.message:
            print("Error: --message is required for create-migration")
            return 1
        success = utility.create_migration(args.message)
    elif args.command == "downgrade":
        revision = args.revision or "-1"
        success = utility.downgrade_migration(revision)
    elif args.command == "history":
        history = utility.get_migration_history()
        if history:
            for line in history:
                print(line)
        success = history is not None
    elif args.command == "current":
        current = utility.get_current_revision()
        if current:
            print(f"Current revision: {current}")
        success = current is not None
    elif args.command == "reset":
        success = utility.reset_database()
    elif args.command == "health":
        health = utility.check_database_health()
        print("Database Health Status:")
        print(f"  Connected: {health['connected']}")
        print(f"  Current Revision: {health['current_revision']}")
        print(f"  Tables Count: {health['tables_count']}")
        if health['errors']:
            print("  Errors:")
            for error in health['errors']:
                print(f"    - {error}")
        success = len(health['errors']) == 0
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
