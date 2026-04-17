"""
Status bar component for XPanda ERP-Lite.
Displays database connection status, Google Drive sync status, and system messages.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QStatusBar, QLabel, QHBoxLayout, QWidget, 
    QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter

logger = logging.getLogger(__name__)


class StatusBar(QStatusBar):
    """Custom status bar with connection status and message display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Status indicators
        self.db_status_label: Optional[QLabel] = None
        self.drive_status_label: Optional[QLabel] = None
        self.module_label: Optional[QLabel] = None
        self.message_label: Optional[QLabel] = None
        self.progress_bar: Optional[QProgressBar] = None
        
        # Status states
        self.db_connected = False
        self.drive_synced = False
        self.current_module = ""
        
        self.setup_ui()
        self.setup_timer()
        
        logger.debug("Status bar initialized")
    
    def setup_ui(self) -> None:
        """Create and layout status bar components."""
        # Main container widget
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(5, 2, 5, 2)
        container_layout.setSpacing(15)
        
        # Database connection status
        self.db_status_label = self.create_status_indicator("DB", "#E74C3C")
        container_layout.addWidget(self.db_status_label)
        
        # Google Drive sync status
        self.drive_status_label = self.create_status_indicator("Drive", "#E74C3C")
        container_layout.addWidget(self.drive_status_label)
        
        # Current module
        self.module_label = QLabel("Module: None")
        self.module_label.setFont(QFont("Arial", 9))
        self.module_label.setStyleSheet("color: #7F8C8D;")
        container_layout.addWidget(self.module_label)
        
        # Spacer
        container_layout.addStretch()
        
        # Message area
        self.message_label = QLabel("Ready")
        self.message_label.setFont(QFont("Arial", 9))
        self.message_label.setStyleSheet("color: #2C3E50;")
        container_layout.addWidget(self.message_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setMaximumHeight(16)
        container_layout.addWidget(self.progress_bar)
        
        # Add container to status bar
        self.addWidget(container)
        
        # Set status bar style
        self.setStyleSheet("""
            QStatusBar {
                background-color: #ECF0F1;
                border-top: 1px solid #BDC3C7;
                color: #2C3E50;
            }
            QStatusBar::item {
                border: none;
            }
        """)
    
    def create_status_indicator(self, text: str, color: str) -> QLabel:
        """Create a status indicator with colored dot."""
        label = QLabel()
        label.setFont(QFont("Arial", 9))
        
        # Create status with colored dot
        status_html = f"""
        <table cellpadding="0" cellspacing="0">
            <tr>
                <td><div style="width: 8px; height: 8px; background-color: {color}; 
                     border-radius: 50%; margin-right: 5px;"></div></td>
                <td>{text}</td>
            </tr>
        </table>
        """
        label.setText(status_html)
        return label
    
    def setup_timer(self) -> None:
        """Setup periodic status updates."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status_display)
        self.update_timer.start(10000)  # Update every 10 seconds
    
    def update_status_display(self) -> None:
        """Update the visual display of all status indicators."""
        # Update database status
        self.update_db_status(self.db_connected)
        
        # Update Drive status
        self.update_drive_status(self.drive_synced)
        
        # Update module
        self.update_module(self.current_module)
    
    def update_db_status(self, connected: bool) -> None:
        """Update database connection status indicator."""
        self.db_connected = connected
        color = "#27AE60" if connected else "#E74C3C"
        text = "DB" if connected else "DB (Offline)"
        
        status_html = f"""
        <table cellpadding="0" cellspacing="0">
            <tr>
                <td><div style="width: 8px; height: 8px; background-color: {color}; 
                     border-radius: 50%; margin-right: 5px;"></div></td>
                <td>{text}</td>
            </tr>
        </table>
        """
        
        if self.db_status_label:
            self.db_status_label.setText(status_html)
    
    def update_drive_status(self, synced: bool) -> None:
        """Update Google Drive sync status indicator."""
        self.drive_synced = synced
        color = "#27AE60" if synced else "#F39C12"
        text = "Drive" if synced else "Drive (Syncing)"
        
        status_html = f"""
        <table cellpadding="0" cellspacing="0">
            <tr>
                <td><div style="width: 8px; height: 8px; background-color: {color}; 
                     border-radius: 50%; margin-right: 5px;"></div></td>
                <td>{text}</td>
            </tr>
        </table>
        """
        
        if self.drive_status_label:
            self.drive_status_label.setText(status_html)
    
    def update_module(self, module_name: str) -> None:
        """Update current module display."""
        self.current_module = module_name
        if self.module_label:
            display_name = module_name.title() if module_name else "None"
            self.module_label.setText(f"Module: {display_name}")
    
    def show_message(self, message: str, timeout: int = 0) -> None:
        """Display a temporary message in the status bar."""
        if self.message_label:
            self.message_label.setText(message)
            
        if timeout > 0:
            # Clear message after timeout
            QTimer.singleShot(timeout, lambda: self.clear_message())
    
    def clear_message(self) -> None:
        """Clear the current message."""
        if self.message_label:
            self.message_label.setText("Ready")
    
    def show_progress(self, minimum: int = 0, maximum: int = 100, value: int = 0) -> None:
        """Show progress bar with specified values."""
        if self.progress_bar:
            self.progress_bar.setMinimum(minimum)
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(value)
            self.progress_bar.setVisible(True)
    
    def update_progress(self, value: int) -> None:
        """Update progress bar value."""
        if self.progress_bar and self.progress_bar.isVisible():
            self.progress_bar.setValue(value)
    
    def hide_progress(self) -> None:
        """Hide progress bar."""
        if self.progress_bar:
            self.progress_bar.setVisible(False)
    
    def set_syncing(self, syncing: bool) -> None:
        """Set Drive syncing status."""
        if syncing:
            self.update_drive_status(False)
            self.show_progress(0, 100, 0)
            self.show_message("Syncing with Google Drive...")
        else:
            self.update_drive_status(True)
            self.hide_progress()
            self.show_message("Google Drive sync completed", 3000)
