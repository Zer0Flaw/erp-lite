"""
Material Detail view for XPanda ERP-Lite.
Displays detailed information about a specific material.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class MaterialDetailView(QWidget):
    """Detailed view of a single material."""
    
    # Signals
    back_to_dashboard = pyqtSignal()
    edit_material = pyqtSignal(str)
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        self.current_material_id: Optional[str] = None
        
        self.setup_ui()
        self.setup_connections()
        
        logger.debug("Material detail view initialized")
    
    def setup_ui(self) -> None:
        """Create and layout material detail components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self.setup_header(main_layout)
        
        # Content area
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)
        
        # Material information
        self.setup_material_info(content_layout)
        
        # Stock history table
        self.setup_stock_history(content_layout)
        
        content_scroll.setWidget(content_widget)
        main_layout.addWidget(content_scroll)
    
    def setup_header(self, parent_layout) -> None:
        """Create view header."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Material Details")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setProperty("class", "header")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Action buttons
        back_btn = QPushButton("Back to Dashboard")
        back_btn.setProperty("class", "secondary")
        back_btn.clicked.connect(self.back_to_dashboard.emit)
        header_layout.addWidget(back_btn)
        
        edit_btn = QPushButton("Edit Material")
        edit_btn.setProperty("class", "primary")
        edit_btn.clicked.connect(self.on_edit_clicked)
        header_layout.addWidget(edit_btn)
        
        parent_layout.addWidget(header_widget)
    
    def setup_material_info(self, parent_layout) -> None:
        """Create material information section."""
        info_group = QGroupBox("Material Information")
        info_layout = QVBoxLayout(info_group)
        
        # Create info grid
        info_widget = QWidget()
        info_grid = QHBoxLayout(info_widget)
        info_grid.setContentsMargins(0, 0, 0, 0)
        
        # Left column
        left_column = QVBoxLayout()
        self.info_labels = {}
        
        info_fields = [
            ("SKU:", "sku"),
            ("Description:", "description"),
            ("Category:", "category"),
            ("Unit of Measure:", "uom"),
        ]
        
        for label_text, key in info_fields:
            field_layout = QHBoxLayout()
            
            label = QLabel(label_text)
            label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            field_layout.addWidget(label)
            
            value_label = QLabel("Not loaded")
            value_label.setProperty("class", "info-value")
            field_layout.addWidget(value_label)
            field_layout.addStretch()
            
            self.info_labels[key] = value_label
            left_column.addLayout(field_layout)
        
        info_grid.addLayout(left_column)
        info_grid.addStretch()
        info_layout.addWidget(info_widget)
        parent_layout.addWidget(info_group)
    
    def setup_stock_history(self, parent_layout) -> None:
        """Create stock history table."""
        history_group = QGroupBox("Stock History")
        history_layout = QVBoxLayout(history_group)
        
        # Table widget
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Type", "Quantity", "Reference", "Notes"
        ])
        
        # Configure table
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSortingEnabled(True)
        
        # Resize columns
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        history_layout.addWidget(self.history_table)
        parent_layout.addWidget(history_group)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        pass
    
    def load_material(self, material_id: str) -> None:
        """Load material data into the view."""
        self.current_material_id = material_id
        
        # Placeholder data - will be replaced with actual database query
        material_data = {
            "sku": material_id,
            "description": "Sample Material Description",
            "category": "Raw Material",
            "uom": "EA"
        }
        
        # Update info labels
        for key, value in material_data.items():
            if key in self.info_labels:
                self.info_labels[key].setText(str(value))
        
        # Load stock history
        self.load_stock_history()
    
    def load_stock_history(self) -> None:
        """Load stock history data."""
        if not self.history_table:
            return
        
        # Clear existing data
        self.history_table.setRowCount(0)
        
        # Placeholder data
        sample_history = [
            ["2024-01-15", "Receiving", "100", "PO-1234", "Initial stock"],
            ["2024-01-14", "Adjustment", "-5", "ADJ-001", "Damage"],
            ["2024-01-13", "Consumption", "-10", "WO-5678", "Production use"],
        ]
        
        for record in sample_history:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            for col, value in enumerate(record):
                table_item = QTableWidgetItem(value)
                self.history_table.setItem(row, col, table_item)
    
    def on_edit_clicked(self) -> None:
        """Handle edit button click."""
        if self.current_material_id:
            self.edit_material.emit(self.current_material_id)
    
    def new_record(self) -> None:
        """Handle new record action."""
        pass
    
    def save(self) -> None:
        """Handle save action."""
        pass
    
    def search(self) -> None:
        """Handle search action."""
        pass
    
    def auto_save(self) -> None:
        """Handle auto-save."""
        pass
