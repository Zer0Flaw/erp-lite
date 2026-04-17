"""
Settings dialog for XPanda ERP-Lite.
Provides configuration interface for database, Google Drive, and application settings.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTabWidget, QWidget,
    QFormLayout, QSpinBox, QComboBox, QCheckBox,
    QTextEdit, QFileDialog, QMessageBox, QGroupBox,
    QSizePolicy, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIntValidator

from config import Config, DatabaseConfig, GoogleDriveConfig, AppConfig

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Settings configuration dialog."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        
        self.settings = settings
        self.config = Config()
        
        # Load current settings
        self.load_settings_from_storage()
        
        self.setup_ui()
        self.setup_connections()
        self.load_ui_values()
        
        logger.debug("Settings dialog initialized")
    
    def setup_ui(self) -> None:
        """Create and layout dialog components."""
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Database tab
        self.setup_database_tab()
        
        # Google Drive tab
        self.setup_google_drive_tab()
        
        # Application tab
        self.setup_application_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        self.setup_buttons(main_layout)
    
    def setup_database_tab(self) -> None:
        """Create database configuration tab."""
        db_widget = QWidget()
        db_layout = QVBoxLayout(db_widget)
        
        # Database connection group
        connection_group = QGroupBox("Database Connection")
        connection_layout = QFormLayout(connection_group)
        
        # Database fields
        self.db_host_input = QLineEdit()
        self.db_port_input = QLineEdit()
        self.db_port_input.setValidator(QIntValidator(1, 65535))
        self.db_name_input = QLineEdit()
        self.db_user_input = QLineEdit()
        self.db_password_input = QLineEdit()
        self.db_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        connection_layout.addRow("Host:", self.db_host_input)
        connection_layout.addRow("Port:", self.db_port_input)
        connection_layout.addRow("Database Name:", self.db_name_input)
        connection_layout.addRow("Username:", self.db_user_input)
        connection_layout.addRow("Password:", self.db_password_input)
        
        db_layout.addWidget(connection_group)
        
        # Test connection button
        test_btn_layout = QHBoxLayout()
        test_btn_layout.addStretch()
        
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.setProperty("class", "secondary")
        test_btn_layout.addWidget(self.test_connection_btn)
        
        db_layout.addLayout(test_btn_layout)
        db_layout.addStretch()
        
        self.tab_widget.addTab(db_widget, "Database")
    
    def setup_google_drive_tab(self) -> None:
        """Create Google Drive configuration tab."""
        drive_widget = QWidget()
        drive_layout = QVBoxLayout(drive_widget)
        
        # Google Drive connection group
        connection_group = QGroupBox("Google Drive Connection")
        connection_layout = QFormLayout(connection_group)
        
        # Drive fields
        self.root_folder_input = QLineEdit()
        self.root_folder_input.setPlaceholderText("Optional - leave empty for root folder")
        self.client_secrets_input = QLineEdit()
        self.credentials_input = QLineEdit()
        
        connection_layout.addRow("Root Folder ID:", self.root_folder_input)
        connection_layout.addRow("Client Secrets File:", self.client_secrets_input)
        connection_layout.addRow("Credentials File:", self.credentials_input)
        
        # File selection buttons
        client_secrets_btn = QPushButton("Browse...")
        client_secrets_btn.clicked.connect(self.browse_client_secrets)
        connection_layout.addRow("", client_secrets_btn)
        
        credentials_btn = QPushButton("Browse...")
        credentials_btn.clicked.connect(self.browse_credentials)
        connection_layout.addRow("", credentials_btn)
        
        drive_layout.addWidget(connection_group)
        
        # Folder structure group
        folder_group = QGroupBox("Folder Structure")
        folder_layout = QFormLayout(folder_group)
        
        self.sops_folder_input = QLineEdit()
        self.reports_folder_input = QLineEdit()
        self.quality_folder_input = QLineEdit()
        
        folder_layout.addRow("SOPs Folder:", self.sops_folder_input)
        folder_layout.addRow("Reports Folder:", self.reports_folder_input)
        folder_layout.addRow("Quality Documents:", self.quality_folder_input)
        
        drive_layout.addWidget(folder_group)
        drive_layout.addStretch()
        
        self.tab_widget.addTab(drive_widget, "Google Drive")
    
    def setup_application_tab(self) -> None:
        """Create application configuration tab."""
        app_widget = QWidget()
        app_layout = QVBoxLayout(app_widget)
        
        # Company information group
        company_group = QGroupBox("Company Information")
        company_layout = QFormLayout(company_group)
        
        self.company_name_input = QLineEdit()
        self.company_address_input = QTextEdit()
        self.company_address_input.setMaximumHeight(80)
        
        company_layout.addRow("Company Name:", self.company_name_input)
        company_layout.addRow("Address:", self.company_address_input)
        
        app_layout.addWidget(company_group)
        
        # Application preferences group
        prefs_group = QGroupBox("Application Preferences")
        prefs_layout = QFormLayout(prefs_group)
        
        self.default_uom_combo = QComboBox()
        self.default_uom_combo.addItems(["EA", "LB", "KG", "FT", "M", "GAL", "L"])
        
        self.date_format_input = QLineEdit()
        self.date_format_input.setPlaceholderText("e.g., %Y-%m-%d")
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["default", "dark", "light"])
        
        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(60, 3600)
        self.auto_save_spin.setSuffix(" seconds")
        
        prefs_layout.addRow("Default Unit of Measure:", self.default_uom_combo)
        prefs_layout.addRow("Date Format:", self.date_format_input)
        prefs_layout.addRow("Theme:", self.theme_combo)
        prefs_layout.addRow("Auto-save Interval:", self.auto_save_spin)
        
        app_layout.addWidget(prefs_group)
        app_layout.addStretch()
        
        self.tab_widget.addTab(app_widget, "Application")
    
    def setup_buttons(self, parent_layout) -> None:
        """Create dialog buttons."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setProperty("class", "success")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        parent_layout.addLayout(button_layout)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        self.test_connection_btn.clicked.connect(self.test_database_connection)
    
    def load_settings_from_storage(self) -> None:
        """Load settings from QSettings into config object."""
        # Database settings
        self.config.database.host = self.settings.value("database/host", "localhost")
        self.config.database.port = self.settings.value("database/port", 5432, type=int)
        self.config.database.database = self.settings.value("database/database", "xpanda_erp")
        self.config.database.username = self.settings.value("database/username", "postgres")
        self.config.database.password = self.settings.value("database/password", "")
        
        # Google Drive settings
        self.config.google_drive.root_folder_id = self.settings.value("google_drive/root_folder_id")
        self.config.google_drive.client_secrets_file = self.settings.value("google_drive/client_secrets", "client_secrets.json")
        self.config.google_drive.credentials_file = self.settings.value("google_drive/credentials", "credentials.json")
        self.config.google_drive.sops_folder = self.settings.value("google_drive/sops_folder", "SOPs")
        self.config.google_drive.reports_folder = self.settings.value("google_drive/reports_folder", "Reports")
        self.config.google_drive.quality_folder = self.settings.value("google_drive/quality_folder", "Quality Documents")
        
        # Application settings
        self.config.app.company_name = self.settings.value("app/company_name", "XPanda Foam")
        self.config.app.company_address = self.settings.value("app/company_address", "")
        self.config.app.default_unit_of_measure = self.settings.value("app/default_uom", "EA")
        self.config.app.date_format = self.settings.value("app/date_format", "%Y-%m-%d")
        self.config.app.theme = self.settings.value("app/theme", "default")
        self.config.app.auto_save_interval = self.settings.value("app/auto_save_interval", 300, type=int)
    
    def load_ui_values(self) -> None:
        """Load config values into UI widgets."""
        # Database
        self.db_host_input.setText(self.config.database.host)
        self.db_port_input.setText(str(self.config.database.port))
        self.db_name_input.setText(self.config.database.database)
        self.db_user_input.setText(self.config.database.username)
        self.db_password_input.setText(self.config.database.password)
        
        # Google Drive
        self.root_folder_input.setText(self.config.google_drive.root_folder_id or "")
        self.client_secrets_input.setText(self.config.google_drive.client_secrets_file)
        self.credentials_input.setText(self.config.google_drive.credentials_file)
        self.sops_folder_input.setText(self.config.google_drive.sops_folder)
        self.reports_folder_input.setText(self.config.google_drive.reports_folder)
        self.quality_folder_input.setText(self.config.google_drive.quality_folder)
        
        # Application
        self.company_name_input.setText(self.config.app.company_name)
        self.company_address_input.setText(self.config.app.company_address)
        
        uom_index = self.default_uom_combo.findText(self.config.app.default_unit_of_measure)
        if uom_index >= 0:
            self.default_uom_combo.setCurrentIndex(uom_index)
        
        self.date_format_input.setText(self.config.app.date_format)
        
        theme_index = self.theme_combo.findText(self.config.app.theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        self.auto_save_spin.setValue(self.config.app.auto_save_interval)
    
    def save_settings(self) -> None:
        """Save settings from UI to storage."""
        try:
            # Database settings
            self.settings.setValue("database/host", self.db_host_input.text())
            self.settings.setValue("database/port", int(self.db_port_input.text() or "5432"))
            self.settings.setValue("database/database", self.db_name_input.text())
            self.settings.setValue("database/username", self.db_user_input.text())
            self.settings.setValue("database/password", self.db_password_input.text())
            
            # Google Drive settings
            self.settings.setValue("google_drive/root_folder_id", self.root_folder_input.text() or None)
            self.settings.setValue("google_drive/client_secrets", self.client_secrets_input.text())
            self.settings.setValue("google_drive/credentials", self.credentials_input.text())
            self.settings.setValue("google_drive/sops_folder", self.sops_folder_input.text())
            self.settings.setValue("google_drive/reports_folder", self.reports_folder_input.text())
            self.settings.setValue("google_drive/quality_folder", self.quality_folder_input.text())
            
            # Application settings
            self.settings.setValue("app/company_name", self.company_name_input.text())
            self.settings.setValue("app/company_address", self.company_address_input.toPlainText())
            self.settings.setValue("app/default_uom", self.default_uom_combo.currentText())
            self.settings.setValue("app/date_format", self.date_format_input.text())
            self.settings.setValue("app/theme", self.theme_combo.currentText())
            self.settings.setValue("app/auto_save_interval", self.auto_save_spin.value())
            
            # Sync settings
            self.settings.sync()
            
            logger.info("Settings saved successfully")
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
    def test_database_connection(self) -> None:
        """Test database connection with current settings."""
        try:
            from database.connection import DatabaseManager
            
            # Create temporary config
            temp_config = DatabaseConfig()
            temp_config.host = self.db_host_input.text()
            temp_config.port = int(self.db_port_input.text() or "5432")
            temp_config.database = self.db_name_input.text()
            temp_config.username = self.db_user_input.text()
            temp_config.password = self.db_password_input.text()
            
            # Test connection
            db_manager = DatabaseManager(temp_config)
            if db_manager.connect():
                QMessageBox.information(self, "Success", "Database connection successful!")
                db_manager.disconnect()
            else:
                QMessageBox.warning(self, "Connection Failed", "Could not connect to database with these settings.")
                
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            QMessageBox.critical(self, "Error", f"Connection test failed: {e}")
    
    def browse_client_secrets(self) -> None:
        """Browse for client secrets file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Client Secrets File", "", "JSON Files (*.json)"
        )
        if file_path:
            self.client_secrets_input.setText(file_path)
    
    def browse_credentials(self) -> None:
        """Browse for credentials file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Credentials File", "", "JSON Files (*.json)"
        )
        if file_path:
            self.credentials_input.setText(file_path)
