"""
Database connection management for XPanda ERP-Lite.
Handles PostgreSQL connection, session management, and basic database operations.
"""

import logging
from typing import Optional, Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import psycopg2
from psycopg2.extensions import connection as pg_connection

from config import DatabaseConfig

logger = logging.getLogger(__name__)

# SQLAlchemy base class for all models
Base = declarative_base()


class DatabaseManager:
    """Manages PostgreSQL database connections and sessions."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine: Optional[object] = None
        self.session_factory: Optional[sessionmaker] = None
        self._is_connected = False
        
    def connect(self) -> bool:
        """
        Establish database connection and create engine.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test basic PostgreSQL connection first
            if not self._test_connection():
                return False
            
            # Create SQLAlchemy engine with connection pooling
            self.engine = create_engine(
                self.config.connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Validate connections before use
                echo=False  # Set to True for SQL debugging
            )
            
            # Add connection event listeners
            self._setup_event_listeners()
            
            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            # Test SQLAlchemy connection
            with self.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            
            self._is_connected = True
            logger.info("Database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self._is_connected = False
            return False
    
    def _test_connection(self) -> bool:
        """
        Test basic PostgreSQL connection using psycopg2.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Testing database connection to {self.config.host}:{self.config.port}/{self.config.database}")
            
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                connect_timeout=10
            )
            
            # Test if we can execute a query
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            
            logger.info(f"Database connection test successful. PostgreSQL version: {version[0] if version else 'Unknown'}")
            return True
            
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            logger.error(f"PostgreSQL connection failed: {error_msg}")
            
            # Provide helpful error messages
            if "does not exist" in error_msg:
                logger.error(f"Database '{self.config.database}' does not exist. Please create it first.")
            elif "authentication failed" in error_msg.lower() or "password authentication failed" in error_msg.lower():
                logger.error(f"Authentication failed for user '{self.config.username}'. Check username and password.")
            elif "connection refused" in error_msg.lower():
                logger.error(f"Connection refused. Check if PostgreSQL is running on {self.config.host}:{self.config.port}")
            elif "timeout" in error_msg.lower():
                logger.error("Connection timeout. Check network connectivity and firewall settings.")
            
            return False
        except Exception as e:
            logger.error(f"Unexpected connection error: {e}")
            return False
    
    def _setup_event_listeners(self) -> None:
        """Setup SQLAlchemy event listeners for logging and monitoring."""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Log new database connections."""
            logger.debug("New database connection established")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout from pool."""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin to pool."""
            logger.debug("Connection checked in to pool")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.
        
        Yields:
            SQLAlchemy Session object
        """
        if not self._is_connected or not self.session_factory:
            raise RuntimeError("Database not connected")
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[dict] = None) -> list:
        """
        Execute a raw SQL query and return results.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of query results
        """
        try:
            with self.get_session() as session:
                result = session.execute(query, params or {})
                return result.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def create_tables(self) -> bool:
        """
        Create all database tables from SQLAlchemy models.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def drop_tables(self) -> bool:
        """
        Drop all database tables. Use with caution!
        
        Returns:
            True if successful, False otherwise
        """
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("All database tables dropped")
            return True
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            return False
    
    def check_connection(self) -> bool:
        """
        Check if database connection is alive.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"Connection check failed: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Close database connection and cleanup resources."""
        try:
            if self.engine:
                self.engine.dispose()
                self.engine = None
            self.session_factory = None
            self._is_connected = False
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._is_connected
    
    def get_connection_info(self) -> dict:
        """
        Get current connection information.
        
        Returns:
            Dictionary with connection details
        """
        return {
            'host': self.config.host,
            'port': self.config.port,
            'database': self.config.database,
            'username': self.config.username,
            'connected': self._is_connected
        }
