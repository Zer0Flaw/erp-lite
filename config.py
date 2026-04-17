"""
Configuration management for XPanda ERP-Lite application.
Handles database connection settings, Google Drive configuration, and application preferences.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    database: str = os.getenv('DB_NAME', 'xpanda_erp')
    username: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', '')
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class GoogleDriveConfig:
    """Google Drive integration configuration."""
    root_folder_id: Optional[str] = os.getenv('GOOGLE_DRIVE_ROOT_FOLDER_ID')
    client_secrets_file: str = os.getenv('GOOGLE_CLIENT_SECRETS', 'client_secrets.json')
    credentials_file: str = os.getenv('GOOGLE_CREDENTIALS', 'credentials.json')
    
    # Default folder structure
    sops_folder: str = "SOPs"
    reports_folder: str = "Reports"
    quality_folder: str = "Quality Documents"


@dataclass
class AppConfig:
    """General application configuration."""
    company_name: str = os.getenv('COMPANY_NAME', 'XPanda Foam')
    company_address: str = os.getenv('COMPANY_ADDRESS', '')
    default_unit_of_measure: str = os.getenv('DEFAULT_UOM', 'EA')
    date_format: str = os.getenv('DATE_FORMAT', '%Y-%m-%d')
    theme: str = os.getenv('THEME', 'default')
    
    # Application settings
    auto_save_interval: int = int(os.getenv('AUTO_SAVE_INTERVAL', '300'))  # seconds
    max_recent_items: int = int(os.getenv('MAX_RECENT_ITEMS', '10'))


class Config:
    """Main configuration class that holds all application settings."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.google_drive = GoogleDriveConfig()
        self.app = AppConfig()
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        if not self.database.host:
            issues.append("Database host is required")
        if not self.database.database:
            issues.append("Database name is required")
        if not self.database.username:
            issues.append("Database username is required")
        
        if not os.path.exists(self.google_drive.client_secrets_file):
            issues.append(f"Google Drive client secrets file not found: {self.google_drive.client_secrets_file}")
        
        return issues
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary for saving."""
        return {
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
                'username': self.database.username,
                'password': self.database.password,
            },
            'google_drive': {
                'root_folder_id': self.google_drive.root_folder_id,
                'client_secrets_file': self.google_drive.client_secrets_file,
                'credentials_file': self.google_drive.credentials_file,
                'sops_folder': self.google_drive.sops_folder,
                'reports_folder': self.google_drive.reports_folder,
                'quality_folder': self.google_drive.quality_folder,
            },
            'app': {
                'company_name': self.app.company_name,
                'company_address': self.app.company_address,
                'default_unit_of_measure': self.app.default_unit_of_measure,
                'date_format': self.app.date_format,
                'theme': self.app.theme,
                'auto_save_interval': self.app.auto_save_interval,
                'max_recent_items': self.app.max_recent_items,
            }
        }


# Global configuration instance
config = Config()
