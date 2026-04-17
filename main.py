"""
XPanda Foam ERP-Lite Desktop Application
Main entry point for the ERP system.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings, QTimer
from PyQt6.QtGui import QIcon
import logging
from typing import Optional

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from ui.main_window import MainWindow
from database.connection import DatabaseManager
from utils.logger import setup_logging


class ERPApplication:
    """Main application class for XPanda ERP-Lite."""
    
    def __init__(self):
        self.qt_app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.settings: Optional[QSettings] = None
    
    def setup_logging(self) -> None:
        """Configure application logging."""
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("XPanda ERP-Lite starting up...")
    
    def setup_application(self) -> bool:
        """Initialize the Qt application and core components."""
        try:
            # Create QApplication
            self.qt_app = QApplication(sys.argv)
            self.qt_app.setApplicationName("XPanda ERP-Lite")
            self.qt_app.setApplicationVersion("1.0.0")
            self.qt_app.setOrganizationName("XPanda Foam")
            
            # Set application icon (placeholder)
            if os.path.exists("ui/themes/icon.png"):
                self.qt_app.setWindowIcon(QIcon("ui/themes/icon.png"))
            
            # Setup QSettings for persistent configuration
            self.settings = QSettings("XPanda Foam", "ERP-Lite")
            
            # Initialize database connection
            self.db_manager = DatabaseManager(config.database)
            if not self.db_manager.connect():
                self.logger.error("Failed to connect to database")
                return False
            
            # Create main window
            self.main_window = MainWindow(self.db_manager, self.settings)
            self.main_window.show()
            
            self.logger.info("Application setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup application: {e}")
            return False
    
    def setup_auto_save(self) -> None:
        """Setup periodic auto-save functionality."""
        if self.settings:
            auto_save_interval = self.settings.value("app/auto_save_interval", 
                                                   config.app.auto_save_interval, 
                                                   type=int)
            
            auto_save_timer = QTimer()
            auto_save_timer.timeout.connect(self._auto_save)
            auto_save_timer.start(auto_save_interval * 1000)  # Convert to milliseconds
    
    def _auto_save(self) -> None:
        """Perform auto-save operations."""
        try:
            if self.main_window and hasattr(self.main_window, 'auto_save'):
                self.main_window.auto_save()
                self.logger.debug("Auto-save completed")
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
    
    def run(self) -> int:
        """Run the application main loop."""
        try:
            # Setup logging first
            self.setup_logging()
            
            # Validate configuration
            config_issues = config.validate()
            if config_issues:
                self.logger.error("Configuration validation failed:")
                for issue in config_issues:
                    self.logger.error(f"  - {issue}")
                return 1
            
            # Setup application components
            if not self.setup_application():
                return 1
            
            # Setup auto-save
            self.setup_auto_save()
            
            # Start the Qt event loop
            return self.qt_app.exec()
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return 1
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up application resources."""
        try:
            if self.db_manager:
                self.db_manager.disconnect()
                self.logger.info("Database connection closed")
            
            if self.settings:
                self.settings.sync()
                self.logger.info("Settings saved")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point."""
    app = ERPApplication()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
