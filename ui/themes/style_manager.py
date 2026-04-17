"""
Theme and style management for XPanda ERP-Lite.
Provides consistent modern dark theme styling across the application.
"""

import logging
import platform
from typing import Dict, Any
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QFile, QTextStream
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class StyleManager:
    """Manages application themes and styles."""
    
    def __init__(self):
        self.current_theme = "dark"
        self.themes: Dict[str, str] = {
            "dark": self.get_dark_style(),
            "light": self.get_light_style(),
            "default": self.get_dark_style(),  # Default to dark
        }
        
        # Setup base font for the application
        self.setup_base_font()
    
    def setup_base_font(self) -> None:
        """Setup base font for the entire application."""
        try:
            app = QApplication.instance()
            if app:
                # Platform-specific font stack
                if platform.system() == "Windows":
                    font_family = "Segoe UI"
                elif platform.system() == "Darwin":  # macOS
                    font_family = "SF Pro Display"
                else:  # Linux and others
                    font_family = "Helvetica Neue, Arial, sans-serif"
                
                base_font = QFont(font_family, 13)  # Base font size
                base_font.setWeight(QFont.Weight.Normal)
                app.setFont(base_font)
                logger.debug(f"Set base font: {font_family}")
        except Exception as e:
            logger.error(f"Error setting base font: {e}")
    
    def apply_theme(self, widget: QWidget, theme_name: str = "dark") -> None:
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
                self.apply_theme(widget, "dark")
        except Exception as e:
            logger.error(f"Error applying theme {theme_name}: {e}")
    
    def get_dark_style(self) -> str:
        """Get modern dark theme style."""
        return """
        /* Modern Dark Theme - GitHub Inspired */
        
        /* Application Base */
        QApplication {
            font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
            font-size: 13px;
            color: #C9D1D9;
        }
        
        /* Main Window */
        QMainWindow {
            background-color: #0F1117;
            color: #E6EDF3;
        }
        
        /* Sidebar */
        QWidget#sidebar {
            background-color: #0A0C10;
            border-right: 1px solid #1C1F26;
        }
        
        /* Sidebar Module Buttons */
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 8px;
            color: #8B949E;
            text-align: left;
            padding: 8px 12px;
            margin: 2px;
            min-height: 42px;
            font-size: 12px;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #161B22;
            color: #C9D1D9;
        }
        
        QPushButton:checked {
            background-color: #1C2433;
            color: #E6EDF3;
            border-left: 3px solid #58A6FF;
        }
        
        QPushButton:pressed {
            background-color: #1C2433;
        }
        
        /* Company Header */
        QLabel[class="company-header"] {
            color: #58A6FF;
            font-size: 14px;
            font-weight: bold;
        }
        
        /* Sidebar Section Headers */
        QLabel[class="section-header"] {
            color: #484F58;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-top: 16px;
            margin-bottom: 8px;
            padding: 4px 0px;
        }
        
        /* Content Area */
        QWidget[class="content-area"] {
            background-color: #161B22;
            padding: 32px;
        }
        
        /* Summary Cards */
        QWidget[class="summary-card"] {
            background-color: #1C2128;
            border: 1px solid #2D333B;
            border-bottom: 2px solid #2D333B;
            border-radius: 8px;
            padding: 20px;
            margin: 8px;
        }
        
        QWidget[class="summary-card"][accent="success"] {
            border-left: 4px solid #3FB950;
        }
        
        QWidget[class="summary-card"][accent="warning"] {
            border-left: 4px solid #D29922;
        }
        
        QWidget[class="summary-card"][accent="danger"] {
            border-left: 4px solid #F85149;
        }
        
        QWidget[class="summary-card"][accent="primary"] {
            border-left: 4px solid #58A6FF;
        }
        
        QLabel[class="card-category"] {
            color: #8B949E;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        
        QLabel[class="card-value"] {
            color: #E6EDF3;
            font-size: 28px;
            font-weight: bold;
        }
        
        QLabel[class="card-stat"] {
            color: #484F58;
            font-size: 11px;
            margin-top: 4px;
        }
        
        /* Page Headers */
        QLabel[class="page-header"] {
            color: #E6EDF3;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        /* Section Headers */
        QLabel[class="section-header"] {
            color: #C9D1D9;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 16px;
        }
        
        /* Tables */
        QTableWidget {
            background-color: #0D1117;
            alternate-background-color: #131820;
            gridline-color: transparent;
            selection-background-color: #1F3A5F;
            selection-color: #E6EDF3;
            border: 1px solid #30363D;
            border-radius: 6px;
            color: #C9D1D9;
        }
        
        QTableWidget::item {
            padding: 12px 8px;
            border-bottom: 1px solid #21262D;
            min-height: 44px;
        }
        
        QTableWidget::item:selected {
            background-color: #1F3A5F;
            color: #E6EDF3;
        }
        
        QTableWidget::item:hover {
            background-color: #1C2433;
        }
        
        QHeaderView::section {
            background-color: #161B22;
            color: #8B949E;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 12px 8px;
            border: none;
            border-bottom: 1px solid #21262D;
            border-right: 1px solid #21262D;
        }
        
        QHeaderView::section:first {
            border-left: 1px solid #21262D;
            border-top-left-radius: 6px;
        }
        
        QHeaderView::section:last {
            border-right: 1px solid #21262D;
            border-top-right-radius: 6px;
        }
        
        QHeaderView::section:only-one {
            border-left: 1px solid #21262D;
            border-right: 1px solid #21262D;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        
        /* Buttons */
        QPushButton[class="primary"] {
            background-color: #238636;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 13px;
        }
        
        QPushButton[class="primary"]:hover {
            background-color: #2EA043;
        }
        
        QPushButton[class="primary"]:pressed {
            background-color: #238636;
        }
        
        QPushButton[class="accent"] {
            background-color: #1F6FEB;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 13px;
        }
        
        QPushButton[class="accent"]:hover {
            background-color: #388BFD;
        }
        
        QPushButton[class="accent"]:pressed {
            background-color: #1F6FEB;
        }
        
        QPushButton[class="secondary"] {
            background-color: transparent;
            border: 1px solid #30363D;
            color: #C9D1D9;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 13px;
        }
        
        QPushButton[class="secondary"]:hover {
            border-color: #58A6FF;
            color: #58A6FF;
            background-color: transparent;
        }
        
        QPushButton[class="danger"] {
            background-color: #DA3633;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 13px;
        }
        
        QPushButton[class="danger"]:hover {
            background-color: #F85149;
        }
        
        QPushButton[class="danger"]:pressed {
            background-color: #DA3633;
        }
        
        QPushButton[class="success"] {
            background-color: #3FB950;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 13px;
        }
        
        QPushButton[class="success"]:hover {
            background-color: #3FB950;
        }
        
        QPushButton[class="success"]:pressed {
            background-color: #238636;
        }
        
        QPushButton:disabled {
            background-color: #21262D;
            color: #484F58;
            border: 1px solid #30363D;
        }
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
            background-color: #0D1117;
            border: 1px solid #30363D;
            border-radius: 6px;
            padding: 12px;
            color: #C9D1D9;
            font-size: 13px;
            selection-background-color: #1F3A5F;
            selection-color: #E6EDF3;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, 
        QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
            border: 1px solid #58A6FF;
        }
        
        /* Combo Boxes */
        QComboBox {
            background-color: #1C2128;
            border: 1px solid #30363D;
            border-radius: 6px;
            padding: 12px;
            color: #C9D1D9;
            font-size: 13px;
            min-height: 40px;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 30px;
            background-color: #1C2128;
        }
        
        QComboBox::down-arrow {
            image: none;
            border: none;
            width: 10px;
            height: 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8B949E, stop:1 #8B949E);
        }
        
        QComboBox QAbstractItemView {
            background-color: #1C2128;
            border: 1px solid #30363D;
            selection-background-color: #1F3A5F;
            selection-color: #E6EDF3;
            color: #C9D1D9;
            padding: 8px;
        }
        
        QComboBox QAbstractItemView::item {
            min-height: 40px;
            padding: 8px;
        }
        
        QComboBox QAbstractItemView::item:hover {
            background-color: #161B22;
        }
        
        QComboBox QAbstractItemView::item:selected {
            background-color: #1F3A5F;
        }
        
        /* Checkboxes */
        QCheckBox {
            spacing: 8px;
            color: #C9D1D9;
            font-size: 13px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #30363D;
            border-radius: 3px;
            background-color: #0D1117;
        }
        
        QCheckBox::indicator:checked {
            background-color: #58A6FF;
            border-color: #58A6FF;
        }
        
        /* Radio Buttons */
        QRadioButton {
            spacing: 8px;
            color: #C9D1D9;
            font-size: 13px;
        }
        
        QRadioButton::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #30363D;
            border-radius: 9px;
            background-color: #0D1117;
        }
        
        QRadioButton::indicator:checked {
            background-color: #58A6FF;
            border-color: #58A6FF;
        }
        
        /* Tabs */
        QTabWidget::pane {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 8px;
        }
        
        QTabBar::tab {
            background-color: #1C2128;
            border: 1px solid #30363D;
            padding: 12px 24px;
            margin-right: 2px;
            color: #8B949E;
            font-size: 13px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        
        QTabBar::tab:selected {
            background-color: #161B22;
            color: #E6EDF3;
            border-bottom-color: #161B22;
        }
        
        QTabBar::tab:hover {
            background-color: #1C2433;
            color: #C9D1D9;
        }
        
        /* Group Boxes */
        QGroupBox {
            background-color: #161B22;
            border: 1px solid #2D333B;
            border-radius: 8px;
            margin-top: 16px;
            padding-top: 16px;
            font-size: 13px;
            color: #C9D1D9;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px 0 8px;
            color: #8B949E;
            font-weight: 600;
            font-size: 13px;
        }
        
        /* Labels */
        QLabel {
            color: #C9D1D9;
            font-size: 13px;
        }
        
        QLabel[class="subheader"] {
            color: #8B949E;
            font-size: 11px;
            margin-bottom: 4px;
        }
        
        QLabel[class="muted"] {
            color: #484F58;
            font-size: 11px;
        }
        
        QLabel[class="success"] {
            color: #3FB950;
            font-weight: 600;
        }
        
        QLabel[class="warning"] {
            color: #D29922;
            font-weight: 600;
        }
        
        QLabel[class="error"] {
            color: #F85149;
            font-weight: 600;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #0A0C10;
            border-top: 1px solid #21262D;
            color: #8B949E;
            font-size: 12px;
        }
        
        /* Tooltips */
        QToolTip {
            background-color: #2D333B;
            color: #E6EDF3;
            border: 1px solid #444C56;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 12px;
        }
        
        /* Scroll Bars */
        QScrollBar:vertical {
            background-color: #161B22;
            width: 12px;
            border-radius: 6px;
            border: none;
        }
        
        QScrollBar::handle:vertical {
            background-color: #30363D;
            border-radius: 6px;
            min-height: 20px;
            border: none;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #484F58;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
            border: none;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        
        QScrollBar:horizontal {
            background-color: #161B22;
            height: 12px;
            border-radius: 6px;
            border: none;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #30363D;
            border-radius: 6px;
            min-width: 20px;
            border: none;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #484F58;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
            border: none;
        }
        
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        
        /* Progress Bar */
        QProgressBar {
            background-color: #21262D;
            border: 1px solid #30363D;
            border-radius: 6px;
            text-align: center;
            color: #C9D1D9;
            font-size: 12px;
            padding: 2px;
        }
        
        QProgressBar::chunk {
            background-color: #58A6FF;
            border-radius: 4px;
        }
        
        /* Dialogs */
        QDialog {
            background-color: #1C2128;
            border: 1px solid #30363D;
            border-radius: 8px;
        }
        
        /* Form Sections */
        QWidget[class="form-section"] {
            background-color: #161B22;
            border: 1px solid #2D333B;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0px;
        }
        
        /* Dividers */
        QFrame[class="divider"] {
            background-color: #21262D;
            max-height: 1px;
        }
        """
    
    def get_light_style(self) -> str:
        """Get light theme style (placeholder for future implementation)."""
        return """
        /* Light Theme - Placeholder */
        QMainWindow {
            background-color: #FFFFFF;
            color: #24292F;
        }
        
        QWidget#sidebar {
            background-color: #F6F8FA;
            border-right: 1px solid #D0D7DE;
        }
        
        QPushButton {
            background-color: #0969DA;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
        }
        
        QLabel {
            color: #24292F;
        }
        """
    
    def get_available_themes(self) -> list:
        """Get list of available theme names."""
        return list(self.themes.keys())
    
    def get_current_theme(self) -> str:
        """Get currently applied theme name."""
        return self.current_theme
