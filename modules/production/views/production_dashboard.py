"""
Production Dashboard view for XPanda ERP-Lite.
Displays production summary, active work orders, and BOM status.
"""

import logging
from typing import Optional
from uuid import UUID
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete
from modules.inventory.controllers.inventory_controller import InventoryController

logger = logging.getLogger(__name__)


class ProductionDashboard(QWidget):
    """Main production dashboard with summary cards and tables."""
    
    # Signals
    work_order_selected = pyqtSignal(str)
    bom_selected = pyqtSignal(str)
    new_work_order_requested = pyqtSignal()
    new_bom_requested = pyqtSignal()
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        
        # UI components
        self.summary_cards: dict = {}
        self.work_orders_table: Optional[DataTableWithFilter] = None
        self.boms_table: Optional[DataTableWithFilter] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
        
        logger.debug("Production dashboard initialized")
    
    def setup_ui(self) -> None:
        """Create and layout dashboard components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Production Dashboard")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setProperty("class", "header")
        main_layout.addWidget(title_label)
        
        # Summary cards section
        self.setup_summary_cards(main_layout)
        
        # Tables section (horizontal layout)
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(15)
        
        # Work orders table
        self.setup_work_orders_table(tables_layout)
        
        # BOMs table
        self.setup_boms_table(tables_layout)
        
        main_layout.addLayout(tables_layout)
        
        # Styling is now handled by centralized StyleManager
    
    def setup_summary_cards(self, parent_layout) -> None:
        """Create summary cards section."""
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Define summary cards
        card_configs = [
            {"title": "Active Work Orders", "value": "0", "color": "#3498DB"},
            {"title": "BOMs Active", "value": "0", "color": "#27AE60"},
            {"title": "Production Today", "value": "0", "color": "#F39C12"},
            {"title": "Overdue Orders", "value": "0", "color": "#E74C3C"}
        ]
        
        for config in card_configs:
            card = self.create_summary_card(config["title"], config["value"], config["color"])
            self.summary_cards[config["title"]] = card
            cards_layout.addWidget(card)
        
        cards_layout.addStretch()
        parent_layout.addLayout(cards_layout)
    
    def create_summary_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a summary card widget."""
        card = QFrame()
        card.setProperty("class", "summary-card")
        card.setMinimumSize(200, 100)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel(title)
        title_label.setProperty("class", "card-title")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setProperty("class", "card-value")
        layout.addWidget(value_label)
        
        return card
    
    def setup_work_orders_table(self, parent_layout) -> None:
        """Create work orders table."""
        # Container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 10, 0)
        
        # Table header
        header_label = QLabel("Active Work Orders")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setProperty("class", "subheader")
        table_layout.addWidget(header_label)
        
        # Data table with filter
        self.work_orders_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'work_order_number', 'title': 'WO #', 'width': 80},
            {'key': 'finished_good_sku', 'title': 'Product SKU', 'width': 120},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'quantity_ordered', 'title': 'Ordered', 'width': 80},
            {'key': 'quantity_produced', 'title': 'Produced', 'width': 80},
            {'key': 'completion_percentage', 'title': 'Complete %', 'width': 80},
            {'key': 'due_date', 'title': 'Due Date', 'width': 100},
            {'key': 'priority', 'title': 'Priority', 'width': 80}
        ]
        
        self.work_orders_table.set_columns(columns)
        self.work_orders_table.data_table.setMaximumHeight(300)
        
        table_layout.addWidget(self.work_orders_table)
        parent_layout.addWidget(table_container)
    
    def setup_boms_table(self, parent_layout) -> None:
        """Create BOMs table."""
        # Container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(10, 0, 0, 0)
        
        # Table header
        header_label = QLabel("Recent BOMs")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setProperty("class", "subheader")
        table_layout.addWidget(header_label)
        
        # Data table with filter
        self.boms_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'bom_code', 'title': 'BOM Code', 'width': 100},
            {'key': 'name', 'title': 'Name', 'resizable': True},
            {'key': 'finished_good_sku', 'title': 'Product SKU', 'width': 120},
            {'key': 'version', 'title': 'Version', 'width': 60},
            {'key': 'status', 'title': 'Status', 'width': 80},
            {'key': 'line_count', 'title': 'Lines', 'width': 60},
            {'key': 'updated_at', 'title': 'Updated', 'width': 100}
        ]
        
        self.boms_table.set_columns(columns)
        self.boms_table.data_table.setMaximumHeight(300)
        
        table_layout.addWidget(self.boms_table)
        parent_layout.addWidget(table_container)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        if self.work_orders_table:
            self.work_orders_table.row_double_clicked.connect(self.on_work_order_double_clicked)
        
        if self.boms_table:
            self.boms_table.row_double_clicked.connect(self.on_bom_double_clicked)
    
    def load_data(self) -> None:
        """Load dashboard data from database."""
        try:
            # Load summary data
            self.load_summary_data()
            
            # Load work orders
            self.load_work_orders()
            
            # Load BOMs
            self.load_boms()
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}")
    
    def load_summary_data(self) -> None:
        """Load summary statistics."""
        # Placeholder data - will be replaced with actual database queries
        summary_data = {
            "Active Work Orders": "5",
            "BOMs Active": "12", 
            "Production Today": "3",
            "Overdue Orders": "1"
        }
        
        for title, value in summary_data.items():
            if title in self.summary_cards:
                card = self.summary_cards[title]
                # Update the value label (second child)
                if card.layout().count() >= 2:
                    value_label = card.layout().itemAt(1).widget()
                    if isinstance(value_label, QLabel):
                        value_label.setText(str(value))
    
    def load_work_orders(self) -> None:
        """Load work orders into table."""
        if not self.work_orders_table:
            return
        
        try:
            # Placeholder data - will be replaced with actual database query
            work_orders_data = [
                {
                    'work_order_number': 'WO-001',
                    'finished_good_sku': 'EPS-BLOCK-001',
                    'status': 'In Progress',
                    'quantity_ordered': 100,
                    'quantity_produced': 75,
                    'completion_percentage': 75.0,
                    'due_date': '2024-04-20',
                    'priority': 'Normal'
                },
                {
                    'work_order_number': 'WO-002',
                    'finished_good_sku': 'EPS-BLOCK-002',
                    'status': 'Planned',
                    'quantity_ordered': 50,
                    'quantity_produced': 0,
                    'completion_percentage': 0.0,
                    'due_date': '2024-04-25',
                    'priority': 'High'
                },
                {
                    'work_order_number': 'WO-003',
                    'finished_good_sku': 'EPS-BEAD-001',
                    'status': 'Completed',
                    'quantity_ordered': 200,
                    'quantity_produced': 200,
                    'completion_percentage': 100.0,
                    'due_date': '2024-04-15',
                    'priority': 'Normal'
                }
            ]
            
            # Load into table
            self.work_orders_table.load_data(work_orders_data)
            
        except Exception as e:
            logger.error(f"Error loading work orders: {e}")
    
    def load_boms(self) -> None:
        """Load BOMs into table."""
        if not self.boms_table:
            return
        
        try:
            # Placeholder data - will be replaced with actual database query
            boms_data = [
                {
                    'bom_code': 'BOM-001',
                    'name': 'EPS Block 24x24x96',
                    'finished_good_sku': 'EPS-BLOCK-001',
                    'version': '1.0',
                    'status': 'Active',
                    'line_count': 5,
                    'updated_at': '2024-04-15'
                },
                {
                    'bom_code': 'BOM-002',
                    'name': 'EPS Block 36x36x96',
                    'finished_good_sku': 'EPS-BLOCK-002',
                    'version': '1.1',
                    'status': 'Active',
                    'line_count': 6,
                    'updated_at': '2024-04-14'
                },
                {
                    'bom_code': 'BOM-003',
                    'name': 'EPS Beads Standard',
                    'finished_good_sku': 'EPS-BEAD-001',
                    'version': '2.0',
                    'status': 'Draft',
                    'line_count': 3,
                    'updated_at': '2024-04-13'
                }
            ]
            
            # Load into table
            self.boms_table.load_data(boms_data)
            
        except Exception as e:
            logger.error(f"Error loading BOMs: {e}")
    
    def on_work_order_double_clicked(self, row: int) -> None:
        """Handle double-click on work order."""
        if self.work_orders_table:
            selected_data = self.work_orders_table.get_selected_data()
            if selected_data:
                work_order = selected_data[0]
                self.work_order_selected.emit(work_order.get('work_order_number', ''))
    
    def on_bom_double_clicked(self, row: int) -> None:
        """Handle double-click on BOM."""
        if self.boms_table:
            selected_data = self.boms_table.get_selected_data()
            if selected_data:
                bom = selected_data[0]
                self.bom_selected.emit(bom.get('bom_code', ''))
    
    def refresh_data(self) -> None:
        """Refresh all dashboard data."""
        self.load_data()
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.new_work_order_requested.emit()
    
    def save(self) -> None:
        """Handle save action."""
        # Dashboard doesn't have editable data
        pass
    
    def search(self) -> None:
        """Handle search action."""
        if self.work_orders_table:
            self.work_orders_table.search_input.setFocus()
            self.work_orders_table.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save (not applicable to dashboard)."""
        pass
