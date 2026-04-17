"""
Order Processing view for XPanda ERP-Lite.
Provides interface for creating and managing sales orders.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit,
    QFormLayout, QScrollArea, QSplitter, QMessageBox,
    QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete

logger = logging.getLogger(__name__)


class OrderProcessing(QWidget):
    """Order processing widget for sales order management."""
    
    # Signals
    order_saved = pyqtSignal(str)
    order_cancelled = pyqtSignal()
    order_selected = pyqtSignal(str)
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        
        # UI components
        self.orders_table: Optional[DataTableWithFilter] = None
        self.order_form: Optional[QWidget] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_orders()
        
        logger.debug("Order processing initialized")
    
    def setup_ui(self) -> None:
        """Create and layout order processing components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Order Processing")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setProperty("class", "header")
        main_layout.addWidget(title_label)
        
        # Create splitter for table and form
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Orders table
        table_widget = self.create_orders_table()
        splitter.addWidget(table_widget)
        
        # Right side - Order form
        form_widget = self.create_order_form()
        splitter.addWidget(form_widget)
        
        # Set splitter sizes (50% table, 50% form)
        splitter.setSizes([500, 500])
        
        main_layout.addWidget(splitter)
        
        # Styling is now handled by centralized StyleManager
    
    def create_orders_table(self) -> QWidget:
        """Create orders table widget."""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 10, 0)
        
        # Header
        header_label = QLabel("Sales Orders")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setProperty("class", "section-header")
        table_layout.addWidget(header_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.new_order_button = QPushButton("New Order")
        self.new_order_button.setProperty("class", "primary")
        buttons_layout.addWidget(self.new_order_button)
        
        self.confirm_order_button = QPushButton("Confirm")
        self.confirm_order_button.setProperty("class", "success")
        self.confirm_order_button.setEnabled(False)
        buttons_layout.addWidget(self.confirm_order_button)
        
        self.ship_order_button = QPushButton("Ship")
        self.ship_order_button.setProperty("class", "success")
        self.ship_order_button.setEnabled(False)
        buttons_layout.addWidget(self.ship_order_button)
        
        self.cancel_order_button = QPushButton("Cancel")
        self.cancel_order_button.setProperty("class", "danger")
        self.cancel_order_button.setEnabled(False)
        buttons_layout.addWidget(self.cancel_order_button)
        
        buttons_layout.addStretch()
        table_layout.addLayout(buttons_layout)
        
        # Orders table
        self.orders_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'order_number', 'title': 'Order #', 'width': 80},
            {'key': 'customer_name', 'title': 'Customer', 'resizable': True},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'priority', 'title': 'Priority', 'width': 80},
            {'key': 'total_amount', 'title': 'Total', 'width': 80},
            {'key': 'payment_status', 'title': 'Payment', 'width': 80},
            {'key': 'fulfillment_status', 'title': 'Fulfillment', 'width': 100},
            {'key': 'order_date', 'title': 'Order Date', 'width': 100},
            {'key': 'promised_ship_date', 'title': 'Ship Date', 'width': 100}
        ]
        
        self.orders_table.set_columns(columns)
        table_layout.addWidget(self.orders_table)
        
        return table_widget
    
    def create_order_form(self) -> QWidget:
        """Create order form widget."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(10, 0, 0, 0)
        
        # Form tabs
        self.form_tabs = QTabWidget()
        
        # Basic Information tab
        basic_tab = self.create_basic_info_tab()
        self.form_tabs.addTab(basic_tab, "Basic Info")
        
        # Order Lines tab
        lines_tab = self.create_order_lines_tab()
        self.form_tabs.addTab(lines_tab, "Order Lines")
        
        # Payment & Fulfillment tab
        payment_tab = self.create_payment_fulfillment_tab()
        self.form_tabs.addTab(payment_tab, "Payment & Fulfillment")
        
        form_layout.addWidget(self.form_tabs)
        
        # Form action buttons
        self.create_form_buttons(form_layout)
        
        return form_widget
    
    def create_basic_info_tab(self) -> QWidget:
        """Create basic information tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Order Information
        info_frame = QFrame()
        info_frame.setProperty("class", "form-section")
        info_layout = QFormLayout(info_frame)
        
        self.order_number_edit = QLineEdit()
        self.order_number_edit.setPlaceholderText("e.g., SO-001")
        self.order_number_edit.setReadOnly(True)
        info_layout.addRow("Order Number:", self.order_number_edit)
        
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(False)
        # Will be populated with available customers
        info_layout.addRow("Customer *:", self.customer_combo)
        
        self.customer_purchase_order_edit = QLineEdit()
        self.customer_purchase_order_edit.setPlaceholderText("Customer PO number")
        info_layout.addRow("Customer PO:", self.customer_purchase_order_edit)
        
        # Dates
        self.order_date_edit = QDateEdit()
        self.order_date_edit.setCalendarPopup(True)
        self.order_date_edit.setDate(QDate.currentDate())
        info_layout.addRow("Order Date:", self.order_date_edit)
        
        self.requested_ship_date_edit = QDateEdit()
        self.requested_ship_date_edit.setCalendarPopup(True)
        info_layout.addRow("Requested Ship Date:", self.requested_ship_date_edit)
        
        self.promised_ship_date_edit = QDateEdit()
        self.promised_ship_date_edit.setCalendarPopup(True)
        info_layout.addRow("Promised Ship Date:", self.promised_ship_date_edit)
        
        # Status and Priority
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Draft', 'Pending', 'Confirmed', 'In Production', 'Ready to Ship', 'Shipped', 'Delivered', 'Cancelled', 'Returned'])
        info_layout.addRow("Status:", self.status_combo)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['Low', 'Normal', 'High', 'Urgent'])
        self.priority_combo.setCurrentText('Normal')
        info_layout.addRow("Priority:", self.priority_combo)
        
        # Sales Information
        self.sales_rep_edit = QLineEdit()
        self.sales_rep_edit.setPlaceholderText("Sales representative")
        info_layout.addRow("Sales Rep:", self.sales_rep_edit)
        
        tab_layout.addWidget(info_frame)
        tab_layout.addStretch()
        
        return tab_widget
    
    def create_order_lines_tab(self) -> QWidget:
        """Create order lines tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_label = QLabel("Order Lines")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setProperty("class", "section-header")
        tab_layout.addWidget(header_label)
        
        # Action buttons for lines
        lines_buttons_layout = QHBoxLayout()
        
        self.add_line_button = QPushButton("Add Line")
        self.add_line_button.setProperty("class", "primary")
        lines_buttons_layout.addWidget(self.add_line_button)
        
        self.remove_line_button = QPushButton("Remove Selected")
        self.remove_line_button.setProperty("class", "danger")
        self.remove_line_button.setEnabled(False)
        lines_buttons_layout.addWidget(self.remove_line_button)
        
        lines_buttons_layout.addStretch()
        tab_layout.addLayout(lines_buttons_layout)
        
        # Order lines table
        self.order_lines_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'product_sku', 'title': 'Product SKU', 'width': 120},
            {'key': 'product_name', 'title': 'Product Name', 'resizable': True},
            {'key': 'quantity', 'title': 'Quantity', 'width': 80},
            {'key': 'unit_of_measure', 'title': 'UOM', 'width': 60},
            {'key': 'unit_price', 'title': 'Unit Price', 'width': 80},
            {'key': 'discount_percentage', 'title': 'Discount %', 'width': 80},
            {'key': 'line_total', 'title': 'Line Total', 'width': 80}
        ]
        
        self.order_lines_table.set_columns(columns)
        tab_layout.addWidget(self.order_lines_table)
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setProperty("class", "form-section")
        summary_layout = QHBoxLayout(summary_frame)
        
        self.subtotal_label = QLabel("Subtotal: $0.00")
        self.subtotal_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.subtotal_label)
        
        self.tax_label = QLabel("Tax: $0.00")
        self.tax_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.tax_label)
        
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.total_label)
        
        summary_layout.addStretch()
        
        tab_layout.addWidget(summary_frame)
        
        return tab_widget
    
    def create_payment_fulfillment_tab(self) -> QWidget:
        """Create payment and fulfillment tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Payment Information
        payment_frame = QFrame()
        payment_frame.setProperty("class", "form-section")
        payment_layout = QFormLayout(payment_frame)
        
        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems(['Pending', 'Paid', 'Partially Paid', 'Overdue', 'Refunded'])
        payment_layout.addRow("Payment Status:", self.payment_status_combo)
        
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(['Credit Card', 'Check', 'Wire Transfer', 'Cash', 'Other'])
        payment_layout.addRow("Payment Method:", self.payment_method_combo)
        
        self.payment_terms_combo = QComboBox()
        self.payment_terms_combo.addItems(['NET15', 'NET30', 'NET45', 'NET60', 'COD', 'Prepaid'])
        payment_layout.addRow("Payment Terms:", self.payment_terms_combo)
        
        self.paid_amount_spin = QDoubleSpinBox()
        self.paid_amount_spin.setRange(0, 9999999.99)
        self.paid_amount_spin.setDecimals(2)
        self.paid_amount_spin.setPrefix("$")
        payment_layout.addRow("Paid Amount:", self.paid_amount_spin)
        
        tab_layout.addWidget(payment_frame)
        
        # Fulfillment Information
        fulfillment_frame = QFrame()
        fulfillment_frame.setProperty("class", "form-section")
        fulfillment_layout = QFormLayout(fulfillment_frame)
        
        self.fulfillment_status_combo = QComboBox()
        self.fulfillment_status_combo.addItems(['Pending', 'Partially Fulfilled', 'Fulfilled', 'Backordered', 'Cancelled'])
        fulfillment_layout.addRow("Fulfillment Status:", self.fulfillment_status_combo)
        
        self.tracking_number_edit = QLineEdit()
        self.tracking_number_edit.setPlaceholderText("Tracking number")
        fulfillment_layout.addRow("Tracking Number:", self.tracking_number_edit)
        
        self.carrier_combo = QComboBox()
        self.carrier_combo.addItems(['UPS', 'FedEx', 'USPS', 'DHL', 'Other'])
        fulfillment_layout.addRow("Carrier:", self.carrier_combo)
        
        self.shipping_method_combo = QComboBox()
        self.shipping_method_combo.addItems(['Ground', '2-Day', 'Overnight', 'Freight', 'Local Delivery'])
        fulfillment_layout.addRow("Shipping Method:", self.shipping_method_combo)
        
        self.shipping_amount_spin = QDoubleSpinBox()
        self.shipping_amount_spin.setRange(0, 9999.99)
        self.shipping_amount_spin.setDecimals(2)
        self.shipping_amount_spin.setPrefix("$")
        fulfillment_layout.addRow("Shipping Amount:", self.shipping_amount_spin)
        
        tab_layout.addWidget(fulfillment_frame)
        
        # Notes
        notes_frame = QFrame()
        notes_frame.setProperty("class", "form-section")
        notes_layout = QFormLayout(notes_frame)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Order notes...")
        notes_layout.addRow("Notes:", self.notes_edit)
        
        self.internal_notes_edit = QTextEdit()
        self.internal_notes_edit.setMaximumHeight(100)
        self.internal_notes_edit.setPlaceholderText("Internal notes...")
        notes_layout.addRow("Internal Notes:", self.internal_notes_edit)
        
        tab_layout.addWidget(notes_frame)
        tab_layout.addStretch()
        
        return tab_widget
    
    def create_form_buttons(self, parent_layout) -> None:
        """Create form action buttons."""
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Clear button
        self.clear_form_button = QPushButton("Clear")
        self.clear_form_button.setProperty("class", "secondary")
        buttons_layout.addWidget(self.clear_form_button)
        
        # Save button
        self.save_button = QPushButton("Save Order")
        self.save_button.setProperty("class", "primary")
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        parent_layout.addLayout(buttons_layout)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Table selection
        if self.orders_table:
            self.orders_table.selection_changed.connect(self.on_order_selection_changed)
            self.orders_table.row_double_clicked.connect(self.on_order_double_clicked)
        
        # Buttons
        self.new_order_button.clicked.connect(self.new_order)
        self.confirm_order_button.clicked.connect(self.confirm_order)
        self.ship_order_button.clicked.connect(self.ship_order)
        self.cancel_order_button.clicked.connect(self.cancel_order)
        
        # Form buttons
        self.save_button.clicked.connect(self.save_order)
        self.clear_form_button.clicked.connect(self.clear_form)
        
        # Order lines
        if self.order_lines_table:
            self.order_lines_table.selection_changed.connect(self.on_line_selection_changed)
        
        self.add_line_button.clicked.connect(self.add_order_line)
        self.remove_line_button.clicked.connect(self.remove_selected_line)
    
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
                    'priority': 'Normal',
                    'total_amount': 1500.00,
                    'payment_status': 'Paid',
                    'fulfillment_status': 'Partially Fulfilled',
                    'order_date': '2024-04-15',
                    'promised_ship_date': '2024-04-20'
                },
                {
                    'order_number': 'SO-002',
                    'customer_name': 'XYZ Manufacturing',
                    'status': 'In Production',
                    'priority': 'High',
                    'total_amount': 3200.00,
                    'payment_status': 'Partially Paid',
                    'fulfillment_status': 'Pending',
                    'order_date': '2024-04-16',
                    'promised_ship_date': '2024-04-25'
                },
                {
                    'order_number': 'SO-003',
                    'customer_name': 'DEF Supplies',
                    'status': 'Ready to Ship',
                    'priority': 'Normal',
                    'total_amount': 850.00,
                    'payment_status': 'Paid',
                    'fulfillment_status': 'Fulfilled',
                    'order_date': '2024-04-17',
                    'promised_ship_date': '2024-04-18'
                }
            ]
            
            # Load into table
            self.orders_table.load_data(orders_data)
            
        except Exception as e:
            logger.error(f"Error loading orders: {e}")
    
    def on_order_selection_changed(self, selected_data: List[Dict[str, Any]]) -> None:
        """Handle order selection changes."""
        has_selection = bool(selected_data)
        
        # Enable/disable action buttons based on selection and status
        if has_selection:
            order = selected_data[0]
            status = order.get('status', '')
            
            self.confirm_order_button.setEnabled(status == 'Pending')
            self.ship_order_button.setEnabled(status in ['Confirmed', 'In Production', 'Ready to Ship'])
            self.cancel_order_button.setEnabled(status not in ['Shipped', 'Delivered'])
            
            # Load order data into form
            self.load_order_into_form(order)
        else:
            self.confirm_order_button.setEnabled(False)
            self.ship_order_button.setEnabled(False)
            self.cancel_order_button.setEnabled(False)
    
    def on_order_double_clicked(self, row: int) -> None:
        """Handle double-click on order."""
        if self.orders_table:
            selected_data = self.orders_table.get_selected_data()
            if selected_data:
                order = selected_data[0]
                self.order_selected.emit(order.get('order_number', ''))
    
    def load_order_into_form(self, order: Dict[str, Any]) -> None:
        """Load order data into form."""
        # Load basic information
        self.order_number_edit.setText(order.get('order_number', ''))
        self.customer_combo.setCurrentText(order.get('customer_name', ''))
        self.customer_purchase_order_edit.setText(order.get('customer_purchase_order', ''))
        
        # Load dates
        if order.get('order_date'):
            self.order_date_edit.setDate(QDate.fromString(order['order_date'], 'yyyy-MM-dd'))
        
        if order.get('requested_ship_date'):
            self.requested_ship_date_edit.setDate(QDate.fromString(order['requested_ship_date'], 'yyyy-MM-dd'))
        
        if order.get('promised_ship_date'):
            self.promised_ship_date_edit.setDate(QDate.fromString(order['promised_ship_date'], 'yyyy-MM-dd'))
        
        # Load status and priority
        self.status_combo.setCurrentText(order.get('status', 'Draft'))
        self.priority_combo.setCurrentText(order.get('priority', 'Normal'))
        
        # Load sales information
        self.sales_rep_edit.setText(order.get('sales_rep', ''))
        
        # Load payment information
        self.payment_status_combo.setCurrentText(order.get('payment_status', 'Pending'))
        self.payment_method_combo.setCurrentText(order.get('payment_method', 'Credit Card'))
        self.payment_terms_combo.setCurrentText(order.get('payment_terms', 'NET30'))
        
        paid_amount = order.get('paid_amount', 0)
        if paid_amount:
            self.paid_amount_spin.setValue(float(paid_amount))
        else:
            self.paid_amount_spin.setValue(0)
        
        # Load fulfillment information
        self.fulfillment_status_combo.setCurrentText(order.get('fulfillment_status', 'Pending'))
        self.tracking_number_edit.setText(order.get('tracking_number', ''))
        self.carrier_combo.setCurrentText(order.get('carrier', 'UPS'))
        self.shipping_method_combo.setCurrentText(order.get('shipping_method', 'Ground'))
        
        shipping_amount = order.get('shipping_amount', 0)
        if shipping_amount:
            self.shipping_amount_spin.setValue(float(shipping_amount))
        else:
            self.shipping_amount_spin.setValue(0)
        
        # Load notes
        self.notes_edit.setPlainText(order.get('notes', ''))
        self.internal_notes_edit.setPlainText(order.get('internal_notes', ''))
        
        # Update financial summary
        self.update_financial_summary(order.get('subtotal', 0), order.get('tax_amount', 0), order.get('total_amount', 0))
    
    def on_line_selection_changed(self, selected_data: List[Dict[str, Any]]) -> None:
        """Handle line selection changes."""
        self.remove_line_button.setEnabled(bool(selected_data))
    
    def add_order_line(self) -> None:
        """Add a new order line."""
        # This would open a dialog to select product and enter quantity
        # For now, add a placeholder line
        new_line = {
            'product_sku': '',
            'product_name': '',
            'quantity': 1.0,
            'unit_of_measure': 'EA',
            'unit_price': 0.0,
            'discount_percentage': 0.0,
            'line_total': 0.0
        }
        
        if self.order_lines_table:
            current_data = self.order_lines_table.data_table.filtered_data
            current_data.append(new_line)
            self.order_lines_table.load_data(current_data)
        
        self.update_financial_summary()
    
    def remove_selected_line(self) -> None:
        """Remove selected order line."""
        if not self.order_lines_table:
            return
        
        selected_data = self.order_lines_table.get_selected_data()
        if not selected_data:
            return
        
        # Confirm deletion
        if confirm_delete("Order Line", f"{len(selected_data)} selected line(s)"):
            # Remove selected lines
            current_data = self.order_lines_table.data_table.filtered_data
            for line in selected_data:
                if line in current_data:
                    current_data.remove(line)
            
            self.order_lines_table.load_data(current_data)
            self.update_financial_summary()
    
    def update_financial_summary(self, subtotal: float = 0, tax_amount: float = 0, total_amount: float = 0) -> None:
        """Update financial summary labels."""
        if self.order_lines_table and not subtotal:
            # Calculate from order lines
            current_data = self.order_lines_table.data_table.filtered_data
            subtotal = sum(line.get('line_total', 0) for line in current_data)
            
            # Simple tax calculation (8%)
            tax_amount = subtotal * 0.08
            total_amount = subtotal + tax_amount + self.shipping_amount_spin.value()
        
        self.subtotal_label.setText(f"Subtotal: ${subtotal:,.2f}")
        self.tax_label.setText(f"Tax: ${tax_amount:,.2f}")
        self.total_label.setText(f"Total: ${total_amount:,.2f}")
    
    def new_order(self) -> None:
        """Create new order."""
        self.clear_form()
        
        # Generate order number
        order_number = f"SO-{str(len(self.orders_table.data_table.filtered_data) + 1).zfill(3)}"
        self.order_number_edit.setText(order_number)
        
        # Set default values
        self.status_combo.setCurrentText('Draft')
        self.priority_combo.setCurrentText('Normal')
        self.order_date_edit.setDate(QDate.currentDate())
        self.promised_ship_date_edit.setDate(QDate.currentDate().addDays(7))
        self.payment_status_combo.setCurrentText('Pending')
        self.payment_terms_combo.setCurrentText('NET30')
        self.fulfillment_status_combo.setCurrentText('Pending')
        self.shipping_method_combo.setCurrentText('Ground')
        
        # Focus on first field
        self.customer_combo.setFocus()
    
    def confirm_order(self) -> None:
        """Confirm selected order."""
        selected_data = self.orders_table.get_selected_data()
        if not selected_data:
            return
        
        order = selected_data[0]
        order_number = order.get('order_number', '')
        
        if confirm_delete("Confirm Order", f"Confirm order {order_number}? This will move it to production."):
            # Update status to 'Confirmed'
            order['status'] = 'Confirmed'
            
            # Refresh table
            self.load_orders()
            
            show_info("Success", f"Order {order_number} confirmed successfully!")
    
    def ship_order(self) -> None:
        """Ship selected order."""
        selected_data = self.orders_table.get_selected_data()
        if not selected_data:
            return
        
        order = selected_data[0]
        order_number = order.get('order_number', '')
        
        if confirm_delete("Ship Order", f"Ship order {order_number}? This will mark it as shipped."):
            # Update status to 'Shipped'
            order['status'] = 'Shipped'
            order['fulfillment_status'] = 'Fulfilled'
            
            # Refresh table
            self.load_orders()
            
            show_info("Success", f"Order {order_number} shipped successfully!")
    
    def cancel_order(self) -> None:
        """Cancel selected order."""
        selected_data = self.orders_table.get_selected_data()
        if not selected_data:
            return
        
        order = selected_data[0]
        order_number = order.get('order_number', '')
        
        if confirm_delete("Cancel Order", f"Cancel order {order_number}? This action cannot be undone."):
            # Update status to 'Cancelled'
            order['status'] = 'Cancelled'
            
            # Refresh table
            self.load_orders()
            
            show_info("Success", f"Order {order_number} cancelled successfully!")
    
    def save_order(self) -> None:
        """Save order data."""
        # Validate form
        is_valid, errors = self.validate_form()
        
        if not is_valid:
            error_text = "Please correct the following errors:\n\n" + "\n".join(f"· {error}" for error in errors)
            show_error("Validation Error", error_text)
            return
        
        # Get order data
        order_data = self.get_order_data()
        
        # Save order (this would call the service/controller)
        try:
            # Placeholder for actual save logic
            logger.info(f"Saving order: {order_data['order_number']}")
            
            # Show success message
            show_info("Success", f"Order '{order_data['order_number']}' saved successfully!")
            
            # Refresh table
            self.load_orders()
            
            # Emit signal
            self.order_saved.emit(order_data['order_number'])
            
        except Exception as e:
            logger.error(f"Error saving order: {e}")
            show_error("Error", f"Failed to save order: {e}")
    
    def validate_form(self) -> tuple[bool, List[str]]:
        """Validate order form data."""
        errors = []
        
        # Required fields
        if not self.customer_combo.currentText():
            errors.append("Customer is required")
        
        if self.order_lines_table:
            current_data = self.order_lines_table.data_table.filtered_data
            if not current_data:
                errors.append("At least one order line is required")
            
            for i, line in enumerate(current_data):
                if not line.get('product_sku'):
                    errors.append(f"Line {i+1}: Product SKU is required")
                
                if not line.get('quantity') or line.get('quantity') <= 0:
                    errors.append(f"Line {i+1}: Quantity must be greater than 0")
        
        return len(errors) == 0, errors
    
    def get_order_data(self) -> Dict[str, Any]:
        """Get order data from form."""
        order_data = {
            'order_number': self.order_number_edit.text().strip(),
            'customer_name': self.customer_combo.currentText(),
            'customer_purchase_order': self.customer_purchase_order_edit.text().strip(),
            'order_date': self.order_date_edit.date().toString('yyyy-MM-dd'),
            'requested_ship_date': self.requested_ship_date_edit.date().toString('yyyy-MM-dd'),
            'promised_ship_date': self.promised_ship_date_edit.date().toString('yyyy-MM-dd'),
            'status': self.status_combo.currentText(),
            'priority': self.priority_combo.currentText(),
            'sales_rep': self.sales_rep_edit.text().strip(),
            'payment_status': self.payment_status_combo.currentText(),
            'payment_method': self.payment_method_combo.currentText(),
            'payment_terms': self.payment_terms_combo.currentText(),
            'paid_amount': self.paid_amount_spin.value(),
            'fulfillment_status': self.fulfillment_status_combo.currentText(),
            'tracking_number': self.tracking_number_edit.text().strip(),
            'carrier': self.carrier_combo.currentText(),
            'shipping_method': self.shipping_method_combo.currentText(),
            'shipping_amount': self.shipping_amount_spin.value(),
            'notes': self.notes_edit.toPlainText().strip(),
            'internal_notes': self.internal_notes_edit.toPlainText().strip(),
            'created_by': 'System'  # Would get from user session
        }
        
        # Add order lines
        if self.order_lines_table:
            order_data['order_lines'] = self.order_lines_table.data_table.filtered_data
        
        # Calculate financial summary
        subtotal = sum(line.get('line_total', 0) for line in order_data.get('order_lines', []))
        tax_amount = subtotal * 0.08  # Simple tax calculation
        total_amount = subtotal + tax_amount + order_data['shipping_amount']
        
        order_data['subtotal'] = subtotal
        order_data['tax_amount'] = tax_amount
        order_data['total_amount'] = total_amount
        
        return order_data
    
    def clear_form(self) -> None:
        """Clear order form."""
        # Clear basic information
        self.order_number_edit.clear()
        self.customer_combo.setCurrentText('')
        self.customer_purchase_order_edit.clear()
        
        self.order_date_edit.setDate(QDate.currentDate())
        self.requested_ship_date_edit.setDate(QDate.currentDate())
        self.promised_ship_date_edit.setDate(QDate.currentDate().addDays(7))
        
        self.status_combo.setCurrentText('Draft')
        self.priority_combo.setCurrentText('Normal')
        
        self.sales_rep_edit.clear()
        
        # Clear payment information
        self.payment_status_combo.setCurrentText('Pending')
        self.payment_method_combo.setCurrentText('Credit Card')
        self.payment_terms_combo.setCurrentText('NET30')
        self.paid_amount_spin.setValue(0)
        
        # Clear fulfillment information
        self.fulfillment_status_combo.setCurrentText('Pending')
        self.tracking_number_edit.clear()
        self.carrier_combo.setCurrentText('UPS')
        self.shipping_method_combo.setCurrentText('Ground')
        self.shipping_amount_spin.setValue(0)
        
        # Clear notes
        self.notes_edit.clear()
        self.internal_notes_edit.clear()
        
        # Clear order lines
        if self.order_lines_table:
            self.order_lines_table.load_data([])
        
        # Update financial summary
        self.update_financial_summary()
    
    def refresh_data(self) -> None:
        """Refresh orders data."""
        self.load_orders()
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.new_order()
    
    def save(self) -> None:
        """Handle save action."""
        self.save_order()
    
    def search(self) -> None:
        """Handle search action."""
        if self.orders_table:
            self.orders_table.search_input.setFocus()
            self.orders_table.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save."""
        # Could implement auto-save functionality here
        pass
