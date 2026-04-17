"""
Receiving Log view for XPanda ERP-Lite.
Displays and manages material receiving records.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QHeaderView,
    QLineEdit, QComboBox, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class ReceivingLogView(QWidget):
    """Receiving log for tracking incoming materials."""
    
    # Signals
    back_to_dashboard = pyqtSignal()
    new_receiving = pyqtSignal()
    receiving_selected = pyqtSignal(str)
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        
        # UI components
        self.receiving_table: Optional[QTableWidget] = None
        self.search_input: Optional[QLineEdit] = None
        self.filter_combo: Optional[QComboBox] = None
        self.date_filter: Optional[QDateEdit] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
        
        logger.debug("Receiving log view initialized")
    
    def setup_ui(self) -> None:
        """Create and layout receiving log components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self.setup_header(main_layout)
        
        # Filters
        self.setup_filters(main_layout)
        
        # Receiving table
        self.setup_receiving_table(main_layout)
    
    def setup_header(self, parent_layout) -> None:
        """Create view header."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Receiving Log")
        title.setProperty("class", "page-header")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Action buttons
        back_btn = QPushButton("Back to Dashboard")
        back_btn.setProperty("class", "secondary")
        back_btn.clicked.connect(self.back_to_dashboard.emit)
        header_layout.addWidget(back_btn)
        
        new_receiving_btn = QPushButton("New Receiving")
        new_receiving_btn.setProperty("class", "success")
        new_receiving_btn.clicked.connect(self.new_receiving.emit)
        header_layout.addWidget(new_receiving_btn)
        
        parent_layout.addWidget(header_widget)
    
    def setup_filters(self, parent_layout) -> None:
        """Create filter controls."""
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        search_label = QLabel("Search:")
        search_label.setProperty("class", "subheader")
        filter_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by material or PO...")
        self.search_input.setMaximumWidth(200)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addSpacing(20)
        
        # Filter by status
        status_label = QLabel("Status:")
        status_label.setProperty("class", "subheader")
        filter_layout.addWidget(status_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Pending", "Completed", "Cancelled"])
        self.filter_combo.setMaximumWidth(120)
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addSpacing(20)
        
        # Date filter
        date_label = QLabel("From Date:")
        date_label.setProperty("class", "subheader")
        filter_layout.addWidget(date_label)
        
        self.date_filter = QDateEdit()
        self.date_filter.setDate(QDate.currentDate().addMonths(-1))
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setMaximumWidth(120)
        filter_layout.addWidget(self.date_filter)
        
        filter_layout.addStretch()
        
        # Apply filters button
        apply_btn = QPushButton("Apply Filters")
        apply_btn.setProperty("class", "accent")
        apply_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(apply_btn)
        
        parent_layout.addWidget(filter_widget)
    
    def setup_receiving_table(self, parent_layout) -> None:
        """Create receiving records table."""
        # Table widget
        self.receiving_table = QTableWidget()
        self.receiving_table.setColumnCount(7)
        self.receiving_table.setHorizontalHeaderLabels([
            "Date", "PO Number", "Material", "Quantity", "Status", "Received By", "Notes"
        ])
        
        # Configure table
        self.receiving_table.setAlternatingRowColors(True)
        self.receiving_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.receiving_table.setSortingEnabled(True)
        
        # Resize columns
        header = self.receiving_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        
        parent_layout.addWidget(self.receiving_table)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        if self.receiving_table:
            self.receiving_table.itemDoubleClicked.connect(self.on_receiving_double_clicked)
        
        if self.search_input:
            self.search_input.returnPressed.connect(self.apply_filters)
        
        if self.filter_combo:
            self.filter_combo.currentTextChanged.connect(self.apply_filters)
    
    def load_data(self) -> None:
        """Load receiving records from database."""
        try:
            if not self.receiving_table:
                return
            
            # Clear existing data
            self.receiving_table.setRowCount(0)
            
            # Placeholder data - will be replaced with actual database query
            sample_receiving = [
                ["2024-01-15", "PO-1234", "EPS Beads - Standard", "500", "Completed", "J. Smith", "Received in good condition"],
                ["2024-01-14", "PO-1235", "Foam Adhesive - 1gal", "25", "Completed", "M. Johnson", "Lot #ABC123"],
                ["2024-01-13", "PO-1236", "EPS Block 24x24x96", "100", "Pending", "A. Brown", "Awaiting inspection"],
                ["2024-01-12", "PO-1237", "Packaging Materials", "200", "Completed", "J. Smith", "Standard packaging"],
            ]
            
            for record in sample_receiving:
                row = self.receiving_table.rowCount()
                self.receiving_table.insertRow(row)
                
                for col, value in enumerate(record):
                    table_item = QTableWidgetItem(value)
                    
                    # Set color based on status
                    if col == 4:  # Status column
                        if value == "Completed":
                            table_item.setProperty("class", "success")
                        elif value == "Pending":
                            table_item.setProperty("class", "warning")
                        elif value == "Cancelled":
                            table_item.setProperty("class", "error")
                    
                    self.receiving_table.setItem(row, col, table_item)
        
        except Exception as e:
            logger.error(f"Error loading receiving data: {e}")
    
    def apply_filters(self) -> None:
        """Apply current filters to the table."""
        # This would filter the table based on current filter values
        # For now, just reload the data
        self.load_data()
    
    def on_receiving_double_clicked(self, item) -> None:
        """Handle double-click on receiving record."""
        if item and self.receiving_table:
            row = item.row()
            po_item = self.receiving_table.item(row, 1)
            if po_item:
                po_number = po_item.text()
                self.receiving_selected.emit(po_number)
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.new_receiving.emit()
    
    def save(self) -> None:
        """Handle save action."""
        pass
    
    def search(self) -> None:
        """Handle search action."""
        if self.search_input:
            self.search_input.setFocus()
            self.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save."""
        pass
