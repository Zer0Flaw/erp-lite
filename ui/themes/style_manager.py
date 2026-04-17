"""
Theme and style management for XPanda ERP-Lite.
Provides consistent styling across the application.
"""

import logging
from typing import Dict, Any
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QFile, QTextStream

logger = logging.getLogger(__name__)


class StyleManager:
    """Manages application themes and styles."""
    
    def __init__(self):
        self.current_theme = "default"
        self.themes: Dict[str, str] = {
            "default": self.get_default_style(),
            "dark": self.get_dark_style(),
            "light": self.get_light_style(),
        }
    
    def apply_theme(self, widget: QWidget, theme_name: str = "default") -> None:
        """
        Apply a theme to a widget or the entire application.
        
        Args:
            widget: Widget to apply theme to
            theme_name: Name of the theme to apply
        """
        try:
            if theme_name in self.themes:
                style = self.themes[theme_name]
                widget.setStyleSheet(style)
                self.current_theme = theme_name
                logger.debug(f"Applied theme: {theme_name}")
            else:
                logger.warning(f"Unknown theme: {theme_name}")
                self.apply_theme(widget, "default")
        except Exception as e:
            logger.error(f"Error applying theme {theme_name}: {e}")
    
    def get_default_style(self) -> str:
        """Get the default application style."""
        return """
        /* Main Window */
        QMainWindow {
            background-color: #FFFFFF;
        }
        
        /* Sidebar */
        QWidget#sidebar {
            background-color: #2C3E50;
            border-right: 1px solid #34495E;
        }
        
        /* Tables */
        QTableWidget {
            background-color: #FFFFFF;
            alternate-background-color: #F8F9FA;
            gridline-color: #E9ECEF;
            selection-background-color: #3498DB;
            selection-color: white;
            border: 1px solid #DEE2E6;
            border-radius: 4px;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #E9ECEF;
        }
        
        QTableWidget::item:selected {
            background-color: #3498DB;
            color: white;
        }
        
        QHeaderView::section {
            background-color: #F8F9FA;
            padding: 8px;
            border: 1px solid #DEE2E6;
            border-right: 1px solid #E9ECEF;
            font-weight: bold;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #3498DB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #2980B9;
        }
        
        QPushButton:pressed {
            background-color: #21618C;
        }
        
        QPushButton:disabled {
            background-color: #BDC3C7;
            color: #7F8C8D;
        }
        
        /* Secondary Button */
        QPushButton[class="secondary"] {
            background-color: #95A5A6;
        }
        
        QPushButton[class="secondary"]:hover {
            background-color: #7F8C8D;
        }
        
        /* Danger Button */
        QPushButton[class="danger"] {
            background-color: #E74C3C;
        }
        
        QPushButton[class="danger"]:hover {
            background-color: #C0392B;
        }
        
        /* Success Button */
        QPushButton[class="success"] {
            background-color: #27AE60;
        }
        
        QPushButton[class="success"]:hover {
            background-color: #229954;
        }
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #3498DB;
        }
        
        /* Combo Boxes */
        QComboBox {
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
            min-width: 150px;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #7F8C8D;
        }
        
        /* Checkboxes */
        QCheckBox {
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #BDC3C7;
            border-radius: 3px;
            background-color: white;
        }
        
        QCheckBox::indicator:checked {
            background-color: #3498DB;
            border-color: #3498DB;
        }
        
        /* Radio Buttons */
        QRadioButton::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #BDC3C7;
            border-radius: 9px;
            background-color: white;
        }
        
        QRadioButton::indicator:checked {
            background-color: #3498DB;
            border-color: #3498DB;
        }
        
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #DEE2E6;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #F8F9FA;
            border: 1px solid #DEE2E6;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom-color: white;
        }
        
        /* Group Boxes */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #DEE2E6;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        /* Labels */
        QLabel {
            color: #2C3E50;
        }
        
        QLabel[class="header"] {
            font-size: 18px;
            font-weight: bold;
            color: #2C3E50;
        }
        
        QLabel[class="subheader"] {
            font-size: 14px;
            font-weight: bold;
            color: #34495E;
        }
        
        QLabel[class="success"] {
            color: #27AE60;
            font-weight: bold;
        }
        
        QLabel[class="warning"] {
            color: #F39C12;
            font-weight: bold;
        }
        
        QLabel[class="error"] {
            color: #E74C3C;
            font-weight: bold;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #ECF0F1;
            border-top: 1px solid #BDC3C7;
            color: #2C3E50;
        }
        
        /* Tooltips */
        QToolTip {
            background-color: #34495E;
            color: white;
            border: 1px solid #2C3E50;
            padding: 5px;
            border-radius: 3px;
        }
        
        /* Scroll Bars */
        QScrollBar:vertical {
            background-color: #F8F9FA;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #BDC3C7;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #95A5A6;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* Progress Bar */
        QProgressBar {
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            text-align: center;
            background-color: #F8F9FA;
        }
        
        QProgressBar::chunk {
            background-color: #3498DB;
            border-radius: 3px;
        }
        """
    
    def get_dark_style(self) -> str:
        """Get dark theme style."""
        return """
        /* Dark Theme */
        QMainWindow {
            background-color: #1A1A1A;
        }
        
        QWidget#sidebar {
            background-color: #0D1117;
            border-right: 1px solid #21262D;
        }
        
        QTableWidget {
            background-color: #0D1117;
            alternate-background-color: #161B22;
            gridline-color: #21262D;
            selection-background-color: #1F6FEB;
            selection-color: white;
            border: 1px solid #30363D;
            color: #C9D1D9;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #21262D;
            color: #C9D1D9;
        }
        
        QPushButton {
            background-color: #238636;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2EA043;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 8px;
            background-color: #0D1117;
            color: #C9D1D9;
        }
        
        QLabel {
            color: #C9D1D9;
        }
        
        QStatusBar {
            background-color: #0D1117;
            border-top: 1px solid #21262D;
            color: #C9D1D9;
        }
        """
    
    def get_light_style(self) -> str:
        """Get light theme style."""
        return """
        /* Light Theme */
        QMainWindow {
            background-color: #FAFAFA;
        }
        
        QWidget#sidebar {
            background-color: #F5F5F5;
            border-right: 1px solid #E0E0E0;
        }
        
        QTableWidget {
            background-color: #FFFFFF;
            alternate-background-color: #FAFAFA;
            gridline-color: #F0F0F0;
            selection-background-color: #2196F3;
            selection-color: white;
            border: 1px solid #E0E0E0;
        }
        
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #1976D2;
        }
        
        QLabel {
            color: #212121;
        }
        
        QStatusBar {
            background-color: #F5F5F5;
            border-top: 1px solid #E0E0E0;
            color: #212121;
        }
        """
    
    def get_available_themes(self) -> list:
        """Get list of available theme names."""
        return list(self.themes.keys())
    
    def get_current_theme(self) -> str:
        """Get the currently applied theme name."""
        return self.current_theme
