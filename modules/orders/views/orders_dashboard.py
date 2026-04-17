"""
Orders Dashboard view for XPanda ERP-Lite.
Displays orders summary, active orders, and customer information.
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

logger = logging.getLogger(__name__)


class OrdersDashboard(QWidget):
    """Main orders dashboard with summary cards and tables."""
    
    # Signals
    order_selected = pyqtSignal(str)
    customer_selected = pyqtSignal(str)
    new_order_requested = pyqtSignal()
    new_customer_requested = pyqtSignal()
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        
        # UI components
        self.summary_cards: dict = {}
        self.orders_table: Optional[DataTableWithFilter] = None
        self.customers_table: Optional[DataTableWithFilter] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
        
        logger.debug("Orders dashboard initialized")
    
    def setup_ui(self) -> None:
        """Create and layout dashboard components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Orders Dashboard")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setProperty("class", "header")
        main_layout.addWidget(title_label)
        
        # Summary cards section
        self.setup_summary_cards(main_layout)
        
        # Tables section (horizontal layout)
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(15)
        
        # Orders table
        self.setup_orders_table(tables_layout)
        
        # Customers table
        self.setup_customers_table(tables_layout)
        
        main_layout.addLayout(tables_layout)
        
        # Styling is now handled by centralized StyleManager
    
    def setup_summary_cards(self, parent_layout) -> None:
        """Create summary cards section."""
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Define summary cards
        card_configs = [
            {"title": "Active Orders", "value": "0", "color": "#3498DB"},
            {"title": "New Orders", "value": "0", "color": "#27AE60"},
            {"title": "Pending Shipment", "value": "0", "color": "#F39C12"},
            {"title": "Overdue Payments", "value": "0", "color": "#E74C3C"}
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
    
    def setup_orders_table(self, parent_layout) -> None:
        """Create orders table."""
        # Container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 10, 0)
        
        # Table header
        header_label = QLabel("Recent Orders")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setProperty("class", "subheader")
        table_layout.addWidget(header_label)
        
        # Data table with filter
        self.orders_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'order_number', 'title': 'Order #', 'width': 80},
            {'key': 'customer_name', 'title': 'Customer', 'resizable': True},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'total_amount', 'title': 'Total', 'width': 80},
            {'key': 'payment_status', 'title': 'Payment', 'width': 80},
            {'key': 'fulfillment_status', 'title': 'Fulfillment', 'width': 100},
            {'key': 'order_date', 'title': 'Order Date', 'width': 100},
            {'key': 'priority', 'title': 'Priority', 'width': 80}
        ]
        
        self.orders_table.set_columns(columns)
        self.orders_table.data_table.setMaximumHeight(300)
        
        table_layout.addWidget(self.orders_table)
        parent_layout.addWidget(table_container)
    
    def setup_customers_table(self, parent_layout) -> None:
        """Create customers table."""
        # Container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(10, 0, 0, 0)
        
        # Table header
        header_label = QLabel("Recent Customers")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setProperty("class", "subheader")
        table_layout.addWidget(header_label)
        
        # Data table with filter
        self.customers_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'customer_code', 'title': 'Customer Code', 'width': 100},
            {'key': 'name', 'title': 'Name', 'resizable': True},
            {'key': 'company_name', 'title': 'Company', 'resizable': True},
            {'key': 'status', 'title': 'Status', 'width': 80},
            {'key': 'total_orders', 'title': 'Orders', 'width': 60},
            {'key': 'last_order_date', 'title': 'Last Order', 'width': 100}
        ]
        
        self.customers_table.set_columns(columns)
        self.customers_table.data_table.setMaximumHeight(300)
        
        table_layout.addWidget(self.customers_table)
        parent_layout.addWidget(table_container)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        if self.orders_table:
            self.orders_table.row_double_clicked.connect(self.on_order_double_clicked)
        
        if self.customers_table:
            self.customers_table.row_double_clicked.connect(self.on_customer_double_clicked)
    
    def load_data(self) -> None:
        """Load dashboard data from database."""
        try:
            # Load summary data
            self.load_summary_data()
            
            # Load orders
            self.load_orders()
            
            # Load customers
            self.load_customers()
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}")
    
    def load_summary_data(self) -> None:
        """Load summary statistics."""
        # Placeholder data - will be replaced with actual database queries
        summary_data = {
            "Active Orders": "8",
            "New Orders": "3", 
            "Pending Shipment": "5",
            "Overdue Payments": "2"
        }
        
        for title, value in summary_data.items():
            if title in self.summary_cards:
                card = self.summary_cards[title]
                # Update the value label (second child)
                if card.layout().count() >= 2:
                    value_label = card.layout().itemAt(1).widget()
                    if isinstance(value_label, QLabel):
                        value_label.setText(str(value))
    
    def load_orders(self) -> None:
        """Load orders into table."""
        if not self.orders_table:
            return
        
        try:
            # Placeholder data - will be replaced with actual database query
            orders_data = [
                {
                    'order_number': 'SO-001',
                    'customer_name': 'ABC Construction',
                    'status': 'Confirmed',
                    'total_amount': 1500.00,
                    'payment_status': 'Paid',
                    'fulfillment_status': 'Partially Fulfilled',
                    'order_date': '2024-04-15',
                    'priority': 'Normal'
                },
                {
                    'order_number': 'SO-002',
                    'customer_name': 'XYZ Manufacturing',
                    'status': 'In Production',
                    'total_amount': 3200.00,
                    'payment_status': 'Partially Paid',
                    'fulfillment_status': 'Pending',
                    'order_date': '2024-04-16',
                    'priority': 'High'
                },
                {
                    'order_number': 'SO-003',
                    'customer_name': 'DEF Supplies',
                    'status': 'Ready to Ship',
                    'total_amount': 850.00,
                    'payment_status': 'Paid',
                    'fulfillment_status': 'Fulfilled',
                    'order_date': '2024-04-17',
                    'priority': 'Normal'
                }
            ]
            
            # Load into table
            self.orders_table.load_data(orders_data)
            
        except Exception as e:
            logger.error(f"Error loading orders: {e}")
    
    def load_customers(self) -> None:
        """Load customers into table."""
        if not self.customers_table:
            return
        
        try:
            # Placeholder data - will be replaced with actual database query
            customers_data = [
                {
                    'customer_code': 'CUST-001',
                    'name': 'John Smith',
                    'company_name': 'ABC Construction',
                    'status': 'Active',
                    'total_orders': 5,
                    'last_order_date': '2024-04-15'
                },
                {
                    'customer_code': 'CUST-002',
                    'name': 'Jane Doe',
                    'company_name': 'XYZ Manufacturing',
                    'status': 'Active',
                    'total_orders': 3,
                    'last_order_date': '2024-04-16'
                },
                {
                    'customer_code': 'CUST-003',
                    'name': 'Bob Wilson',
                    'company_name': 'DEF Supplies',
                    'status': 'Active',
                    'total_orders': 8,
                    'last_order_date': '2024-04-17'
                }
            ]
            
            # Load into table
            self.customers_table.load_data(customers_data)
            
        except Exception as e:
            logger.error(f"Error loading customers: {e}")
    
    def on_order_double_clicked(self, row: int) -> None:
        """Handle double-click on order."""
        if self.orders_table:
            selected_data = self.orders_table.get_selected_data()
            if selected_data:
                order = selected_data[0]
                self.order_selected.emit(order.get('order_number', ''))
    
    def on_customer_double_clicked(self, row: int) -> None:
        """Handle double-click on customer."""
        if self.customers_table:
            selected_data = self.customers_table.get_selected_data()
            if selected_data:
                customer = selected_data[0]
                self.customer_selected.emit(customer.get('customer_code', ''))
    
    def refresh_data(self) -> None:
        """Refresh all dashboard data."""
        self.load_data()
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.new_order_requested.emit()
    
    def save(self) -> None:
        """Handle save action."""
        # Dashboard doesn't have editable data
        pass
    
    def search(self) -> None:
        """Handle search action."""
        if self.orders_table:
            self.orders_table.search_input.setFocus()
            self.orders_table.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save (not applicable to dashboard)."""
        pass
