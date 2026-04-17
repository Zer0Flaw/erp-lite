"""
Message box components for XPanda ERP-Lite.
Provides standardized dialogs for user notifications and confirmations.
"""

import logging
from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter

logger = logging.getLogger(__name__)


class InfoMessageBox(QMessageBox):
    """Information message box with consistent styling."""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setText(message)
        self.setIcon(QMessageBox.Icon.Information)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply styling
        self.setStyleSheet("""
            QMessageBox {
                background-color: white;
                border: 1px solid #DEE2E6;
                border-radius: 8px;
            }
            
            QMessageBox QLabel {
                color: #2C3E50;
                font-size: 12px;
            }
            
            QMessageBox QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QMessageBox QPushButton:hover {
                background-color: #2980B9;
            }
        """)


class WarningMessageBox(QMessageBox):
    """Warning message box with consistent styling."""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setText(message)
        self.setIcon(QMessageBox.Icon.Warning)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply styling
        self.setStyleSheet("""
            QMessageBox {
                background-color: #FFF3CD;
                border: 1px solid #F39C12;
                border-radius: 8px;
            }
            
            QMessageBox QLabel {
                color: #856404;
                font-size: 12px;
            }
            
            QMessageBox QPushButton {
                background-color: #F39C12;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QMessageBox QPushButton:hover {
                background-color: #E67E22;
            }
        """)


class ErrorMessageBox(QMessageBox):
    """Error message box with consistent styling."""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setText(message)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply styling
        self.setStyleSheet("""
            QMessageBox {
                background-color: #F8D7DA;
                border: 1px solid #E74C3C;
                border-radius: 8px;
            }
            
            QMessageBox QLabel {
                color: #721C24;
                font-size: 12px;
            }
            
            QMessageBox QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QMessageBox QPushButton:hover {
                background-color: #C0392B;
            }
        """)


class ConfirmMessageBox(QDialog):
    """Custom confirmation dialog with Yes/No/Cancel options."""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 200)
        
        self.result = QMessageBox.StandardButton.Cancel
        
        self.setup_ui(message)
    
    def setup_ui(self, message: str) -> None:
        """Create dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Message label
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 11))
        layout.addWidget(message_label)
        
        layout.addStretch()
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Yes button
        self.yes_button = QPushButton("Yes")
        self.yes_button.setProperty("class", "success")
        self.yes_button.clicked.connect(self.on_yes)
        button_layout.addWidget(self.yes_button)
        
        # No button
        self.no_button = QPushButton("No")
        self.no_button.setProperty("class", "secondary")
        self.no_button.clicked.connect(self.on_no)
        button_layout.addWidget(self.no_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("class", "secondary")
        self.cancel_button.clicked.connect(self.on_cancel)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #DEE2E6;
                border-radius: 8px;
            }
            
            QLabel {
                color: #2C3E50;
            }
            
            QPushButton[class="success"] {
                background-color: #27AE60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton[class="success"]:hover {
                background-color: #229954;
            }
            
            QPushButton[class="secondary"] {
                background-color: #95A5A6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton[class="secondary"]:hover {
                background-color: #7F8C8D;
            }
        """)
    
    def on_yes(self) -> None:
        """Handle Yes button click."""
        self.result = QMessageBox.StandardButton.Yes
        self.accept()
    
    def on_no(self) -> None:
        """Handle No button click."""
        self.result = QMessageBox.StandardButton.No
        self.accept()
    
    def on_cancel(self) -> None:
        """Handle Cancel button click."""
        self.result = QMessageBox.StandardButton.Cancel
        self.reject()
    
    @staticmethod
    def confirm(title: str, message: str, parent=None) -> QMessageBox.StandardButton:
        """Show confirmation dialog and return result."""
        dialog = ConfirmMessageBox(title, message, parent)
        dialog.exec()
        return dialog.result


class DeleteConfirmMessageBox(QDialog):
    """Specialized delete confirmation dialog."""
    
    def __init__(self, item_name: str, item_description: str = "", parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Confirm Delete")
        self.setModal(True)
        self.setMinimumSize(450, 250)
        
        self.confirmed = False
        
        self.setup_ui(item_name, item_description)
    
    def setup_ui(self, item_name: str, item_description: str) -> None:
        """Create dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Warning icon and message
        message_layout = QHBoxLayout()
        
        # Warning icon (text-based)
        warning_label = QLabel("!")
        warning_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        warning_label.setStyleSheet("""
            QLabel {
                color: #E74C3C;
                background-color: #FADBD8;
                border-radius: 20px;
                padding: 10px;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
            }
        """)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_layout.addWidget(warning_label)
        
        message_layout.addSpacing(15)
        
        # Message text
        message_widget = QWidget()
        message_widget_layout = QVBoxLayout(message_widget)
        message_widget_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(f"Delete {item_name}?")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #E74C3C;")
        message_widget_layout.addWidget(title_label)
        
        if item_description:
            desc_label = QLabel(f"{item_description}\n\nThis action cannot be undone.")
        else:
            desc_label = QLabel("This action cannot be undone.")
        
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7F8C8D;")
        message_widget_layout.addWidget(desc_label)
        
        message_layout.addWidget(message_widget)
        message_layout.addStretch()
        
        layout.addLayout(message_layout)
        layout.addStretch()
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.setProperty("class", "danger")
        self.delete_button.clicked.connect(self.on_delete)
        button_layout.addWidget(self.delete_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("class", "secondary")
        self.cancel_button.clicked.connect(self.on_cancel)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #DEE2E6;
                border-radius: 8px;
            }
            
            QLabel {
                color: #2C3E50;
            }
            
            QPushButton[class="danger"] {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton[class="danger"]:hover {
                background-color: #C0392B;
            }
            
            QPushButton[class="secondary"] {
                background-color: #95A5A6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton[class="secondary"]:hover {
                background-color: #7F8C8D;
            }
        """)
    
    def on_delete(self) -> None:
        """Handle Delete button click."""
        self.confirmed = True
        self.accept()
    
    def on_cancel(self) -> None:
        """Handle Cancel button click."""
        self.confirmed = False
        self.reject()
    
    @staticmethod
    def confirm_delete(item_name: str, item_description: str = "", parent=None) -> bool:
        """Show delete confirmation dialog and return result."""
        dialog = DeleteConfirmMessageBox(item_name, item_description, parent)
        dialog.exec()
        return dialog.confirmed


class ProgressMessageBox(QDialog):
    """Dialog for showing progress during long operations."""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 150)
        self.setMaximumSize(400, 150)
        
        self.setup_ui(message)
    
    def setup_ui(self, message: str) -> None:
        """Create dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        # Progress bar
        from PyQt6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)
        
        # Cancel button (optional)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
        
        # Styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #DEE2E6;
                border-radius: 8px;
            }
            
            QLabel {
                color: #2C3E50;
            }
            
            QProgressBar {
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                text-align: center;
                background-color: #F8F9FA;
            }
            
            QProgressBar::chunk {
                background-color: #3498DB;
                border-radius: 3px;
            }
            
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
    
    def update_message(self, message: str) -> None:
        """Update the message text."""
        self.message_label.setText(message)
    
    def set_progress(self, value: int, maximum: int = 100) -> None:
        """Set progress bar value."""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)


# Convenience functions

def show_info(title: str, message: str, parent=None) -> None:
    """Show information message box."""
    dialog = InfoMessageBox(title, message, parent)
    dialog.exec()


def show_warning(title: str, message: str, parent=None) -> None:
    """Show warning message box."""
    dialog = WarningMessageBox(title, message, parent)
    dialog.exec()


def show_error(title: str, message: str, parent=None) -> None:
    """Show error message box."""
    dialog = ErrorMessageBox(title, message, parent)
    dialog.exec()


def confirm_action(title: str, message: str, parent=None) -> bool:
    """Show confirmation dialog and return True if confirmed."""
    result = ConfirmMessageBox.confirm(title, message, parent)
    return result == QMessageBox.StandardButton.Yes


def confirm_delete(item_name: str, item_description: str = "", parent=None) -> bool:
    """Show delete confirmation dialog and return True if confirmed."""
    return DeleteConfirmMessageBox.confirm_delete(item_name, item_description, parent)
