"""
Sidebar navigation component for XPanda ERP-Lite.
Provides module navigation with icons and collapsible functionality.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QButtonGroup, QScrollArea, QFrame, QLabel,
    QSizePolicy, QToolButton, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter

logger = logging.getLogger(__name__)


class SidebarButton(QPushButton):
    """Custom button for sidebar navigation with hover effects."""
    
    def __init__(self, icon_text: str, label: str, module_name: str, parent=None):
        super().__init__(parent)
        
        self.module_name = module_name
        self.label = label
        self.icon_text = icon_text
        
        # Setup button properties
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setMaximumHeight(42)
        
        # Create layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(10)
        
        # Icon label (using Unicode symbols)
        self.icon_label = QLabel(icon_text)
        self.icon_label.setMinimumWidth(30)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont("Segoe UI", 14, QFont.Weight.Normal)
        self.icon_label.setFont(icon_font)
        self.layout.addWidget(self.icon_label)
        
        # Text label
        self.text_label = QLabel(label)
        text_font = QFont("Segoe UI", 12, QFont.Weight.Medium)
        self.text_label.setFont(text_font)
        self.layout.addWidget(self.text_label)
        
        # Set object name for styling
        self.setObjectName("sidebar-button")
    
    def set_collapsed(self, collapsed: bool) -> None:
        """Show/hide text label based on collapsed state."""
        self.text_label.setVisible(not collapsed)


class Sidebar(QWidget):
    """Sidebar navigation with module buttons and collapsible functionality."""
    
    # Signals
    module_selected = pyqtSignal(str)
    settings_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_collapsed = False
        self.button_group: Optional[QButtonGroup] = None
        self.module_buttons: dict[str, SidebarButton] = {}
        
        self.setup_ui()
        self.setup_connections()
        
        logger.debug("Sidebar initialized")
    
    def setup_ui(self) -> None:
        """Create and layout sidebar components."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 10, 5, 10)
        self.main_layout.setSpacing(0)
        
        # Header with collapse button
        self.setup_header()
        
        # Module buttons
        self.setup_module_buttons()
        
        # Spacer
        self.main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Footer with settings button
        self.setup_footer()
        
        # Set sidebar background
        self.setStyleSheet("""
            QWidget#sidebar {
                background-color: #2C3E50;
                border-right: 1px solid #34495E;
            }
        """)
        self.setObjectName("sidebar")
    
    def setup_header(self) -> None:
        """Create header with title and collapse button."""
        # Header container
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Company logo/text
        self.company_label = QLabel("XPanda")
        self.company_label.setProperty("class", "company-header")
        header_layout.addWidget(self.company_label)
        
        # Collapse button
        self.collapse_button = QToolButton()
        self.collapse_button.setText("«")
        self.collapse_button.clicked.connect(self.toggle_collapse)
        header_layout.addWidget(self.collapse_button)
        
        self.main_layout.addWidget(header_widget)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #34495E;")
        self.main_layout.addWidget(separator)
    
    def setup_module_buttons(self) -> None:
        """Create module navigation buttons."""
        # Button group for exclusive selection
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        # Module definitions with Unicode icons
        modules = [
            ("inventory", "inventory", "📦 Inventory", "Inventory & Materials"),
            ("production", "production", "⚙️ Production", "Production & Scheduling"),
            ("production_bom", "bom", "🔧 BOM Editor", "Bill of Materials"),
            ("production_work_orders", "work", "📋 Work Orders", "Work Order Management"),
            ("orders", "orders", "🛒 Orders", "Order Management"),
            ("orders_customers", "customers", "👥 Customers", "Customer Management"),
            ("orders_processing", "processing", "📊 Processing", "Order Processing"),
            ("quality", "quality", "✅ Quality", "Quality Management"),
            ("quality_inspections", "inspections", "🔍 Inspections", "Inspection Management"),
            ("quality_ncr", "ncr", "⚠️ NCR", "NCR Tracking"),
        ]
        
        # Create scroll area for module buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for buttons
        buttons_widget = QWidget()
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        buttons_layout.setSpacing(2)
        
        # Group modules by section
        current_section = None
        for icon, module_id, short_name, full_name in modules:
            # Add section header if section changes
            section = self.get_module_section(module_id)
            if section != current_section:
                section_header = QLabel(section)
                section_header.setProperty("class", "section-header")
                section_header.setAlignment(Qt.AlignmentFlag.AlignLeft)
                buttons_layout.addWidget(section_header)
                current_section = section
            
            button = SidebarButton(icon, full_name, module_id)
            self.button_group.addButton(button)
            self.module_buttons[module_id] = button
            buttons_layout.addWidget(button)
        
        # Set inventory as default selected
        if "inventory" in self.module_buttons:
            self.module_buttons["inventory"].setChecked(True)
        
        scroll_area.setWidget(buttons_widget)
        self.main_layout.addWidget(scroll_area)
    
    def setup_footer(self) -> None:
        """Create footer with settings and user info."""
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #34495E;")
        self.main_layout.addWidget(separator)
        
        # Settings button
        settings_button = SidebarButton("⚙️", "Settings", "settings")
        self.main_layout.addWidget(settings_button)
        
        # User info (placeholder)
        user_label = QLabel("Admin User")
        user_label.setProperty("class", "muted")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(user_label)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        if self.button_group:
            self.button_group.idClicked.connect(self.on_module_selected)
    
    def on_module_selected(self, button_id: int) -> None:
        """Handle module button selection."""
        button = self.button_group.button(button_id)
        if button and hasattr(button, 'module_name'):
            self.module_selected.emit(button.module_name)
            logger.debug(f"Module selected: {button.module_name}")
    
    def toggle_collapse(self) -> None:
        """Toggle sidebar collapsed state."""
        self.is_collapsed = not self.is_collapsed
        
        # Animate the collapse
        if self.is_collapsed:
            self.collapse_button.setText("»")
            self.company_label.setText("X")
            self.setMaximumWidth(80)
        else:
            self.collapse_button.setText("«")
            self.company_label.setText("XPanda")
            self.setMaximumWidth(350)
        
        # Update button text visibility
        for button in self.module_buttons.values():
            button.set_collapsed(self.is_collapsed)
        
        logger.debug(f"Sidebar collapsed: {self.is_collapsed}")
    
    def set_active_module(self, module_name: str) -> None:
        """Set the active module programmatically."""
        if module_name in self.module_buttons:
            self.module_buttons[module_name].setChecked(True)
            self.module_selected.emit(module_name)
    
    def get_module_section(self, module_id: str) -> Optional[str]:
        """Get section name for a module ID."""
        section_mapping = {
            'inventory': None,  # Inventory is top level
            'production': 'PRODUCTION',
            'production_bom': 'PRODUCTION',
            'production_work_orders': 'PRODUCTION',
            'orders': 'ORDERS',
            'orders_customers': 'ORDERS',
            'orders_processing': 'ORDERS',
            'quality': 'QUALITY',
            'quality_inspections': 'QUALITY',
            'quality_ncr': 'QUALITY',
        }
        return section_mapping.get(module_id)
    
    def get_current_module(self) -> Optional[str]:
        """Get currently selected module."""
        if self.button_group and self.button_group.checkedButton():
            button = self.button_group.checkedButton()
            if hasattr(button, 'module_name'):
                return button.module_name
        return None
