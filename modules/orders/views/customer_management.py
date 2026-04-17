"""
Customer Management view for XPanda ERP-Lite.
Provides interface for creating and editing customer records.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QFormLayout, QScrollArea, QSplitter, QMessageBox,
    QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete

logger = logging.getLogger(__name__)


class CustomerManagement(QWidget):
    """Customer management widget for maintaining customer records."""
    
    # Signals
    customer_saved = pyqtSignal(str)
    customer_cancelled = pyqtSignal()
    customer_selected = pyqtSignal(str)
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        
        # UI components
        self.customers_table: Optional[DataTableWithFilter] = None
        self.customer_form: Optional[QWidget] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_customers()
        
        logger.debug("Customer management initialized")
    
    def setup_ui(self) -> None:
        """Create and layout customer management components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Customer Management")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setProperty("class", "header")
        main_layout.addWidget(title_label)
        
        # Create splitter for table and form
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Customers table
        table_widget = self.create_customers_table()
        splitter.addWidget(table_widget)
        
        # Right side - Customer form
        form_widget = self.create_customer_form()
        splitter.addWidget(form_widget)
        
        # Set splitter sizes (50% table, 50% form)
        splitter.setSizes([500, 500])
        
        main_layout.addWidget(splitter)
        
        # Styling is now handled by centralized StyleManager
    
    def create_customers_table(self) -> QWidget:
        """Create customers table widget."""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 10, 0)
        
        # Header
        header_label = QLabel("Customers")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setProperty("class", "section-header")
        table_layout.addWidget(header_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.new_customer_button = QPushButton("New Customer")
        self.new_customer_button.setProperty("class", "primary")
        buttons_layout.addWidget(self.new_customer_button)
        
        self.edit_customer_button = QPushButton("Edit")
        self.edit_customer_button.setProperty("class", "secondary")
        self.edit_customer_button.setEnabled(False)
        buttons_layout.addWidget(self.edit_customer_button)
        
        self.delete_customer_button = QPushButton("Delete")
        self.delete_customer_button.setProperty("class", "danger")
        self.delete_customer_button.setEnabled(False)
        buttons_layout.addWidget(self.delete_customer_button)
        
        buttons_layout.addStretch()
        table_layout.addLayout(buttons_layout)
        
        # Customers table
        self.customers_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'customer_code', 'title': 'Customer Code', 'width': 100},
            {'key': 'name', 'title': 'Name', 'resizable': True},
            {'key': 'company_name', 'title': 'Company', 'resizable': True},
            {'key': 'contact_person', 'title': 'Contact', 'width': 120},
            {'key': 'phone', 'title': 'Phone', 'width': 120},
            {'key': 'email', 'title': 'Email', 'width': 150},
            {'key': 'status', 'title': 'Status', 'width': 80},
            {'key': 'customer_type', 'title': 'Type', 'width': 80}
        ]
        
        self.customers_table.set_columns(columns)
        table_layout.addWidget(self.customers_table)
        
        return table_widget
    
    def create_customer_form(self) -> QWidget:
        """Create customer form widget."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(10, 0, 0, 0)
        
        # Form tabs
        self.form_tabs = QTabWidget()
        
        # Basic Information tab
        basic_tab = self.create_basic_info_tab()
        self.form_tabs.addTab(basic_tab, "Basic Info")
        
        # Address tab
        address_tab = self.create_address_tab()
        self.form_tabs.addTab(address_tab, "Address")
        
        # Business tab
        business_tab = self.create_business_tab()
        self.form_tabs.addTab(business_tab, "Business")
        
        form_layout.addWidget(self.form_tabs)
        
        # Form action buttons
        self.create_form_buttons(form_layout)
        
        return form_widget
    
    def create_basic_info_tab(self) -> QWidget:
        """Create basic information tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Customer Information
        info_frame = QFrame()
        info_frame.setProperty("class", "form-section")
        info_layout = QFormLayout(info_frame)
        
        self.customer_code_edit = QLineEdit()
        self.customer_code_edit.setPlaceholderText("e.g., CUST-001")
        info_layout.addRow("Customer Code *:", self.customer_code_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., John Smith")
        info_layout.addRow("Name *:", self.name_edit)
        
        self.company_name_edit = QLineEdit()
        self.company_name_edit.setPlaceholderText("e.g., ABC Construction")
        info_layout.addRow("Company Name:", self.company_name_edit)
        
        self.contact_person_edit = QLineEdit()
        self.contact_person_edit.setPlaceholderText("e.g., John Smith")
        info_layout.addRow("Contact Person:", self.contact_person_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("e.g., (555) 123-4567")
        info_layout.addRow("Phone:", self.phone_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("e.g., john@abcconstruction.com")
        info_layout.addRow("Email:", self.email_edit)
        
        self.website_edit = QLineEdit()
        self.website_edit.setPlaceholderText("e.g., www.abcconstruction.com")
        info_layout.addRow("Website:", self.website_edit)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Active', 'Inactive', 'Suspended', 'Blacklisted'])
        info_layout.addRow("Status:", self.status_combo)
        
        tab_layout.addWidget(info_frame)
        tab_layout.addStretch()
        
        return tab_widget
    
    def create_address_tab(self) -> QWidget:
        """Create address tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Billing Address
        billing_frame = QFrame()
        billing_frame.setProperty("class", "form-section")
        billing_layout = QFormLayout(billing_frame)
        
        billing_layout.addRow(QLabel("Billing Address"))
        
        self.billing_address_line1_edit = QLineEdit()
        self.billing_address_line1_edit.setPlaceholderText("Street address")
        billing_layout.addRow("Address Line 1 *:", self.billing_address_line1_edit)
        
        self.billing_address_line2_edit = QLineEdit()
        self.billing_address_line2_edit.setPlaceholderText("Apartment, suite, unit, building, floor, etc.")
        billing_layout.addRow("Address Line 2:", self.billing_address_line2_edit)
        
        self.billing_city_edit = QLineEdit()
        self.billing_city_edit.setPlaceholderText("City")
        billing_layout.addRow("City *:", self.billing_city_edit)
        
        self.billing_state_edit = QLineEdit()
        self.billing_state_edit.setPlaceholderText("State/Province")
        billing_layout.addRow("State *:", self.billing_state_edit)
        
        self.billing_postal_code_edit = QLineEdit()
        self.billing_postal_code_edit.setPlaceholderText("Postal Code")
        billing_layout.addRow("Postal Code *:", self.billing_postal_code_edit)
        
        self.billing_country_edit = QLineEdit()
        self.billing_country_edit.setText("USA")
        billing_layout.addRow("Country:", self.billing_country_edit)
        
        tab_layout.addWidget(billing_frame)
        
        # Shipping Address
        shipping_frame = QFrame()
        shipping_frame.setProperty("class", "form-section")
        shipping_layout = QFormLayout(shipping_frame)
        
        shipping_layout.addRow(QLabel("Shipping Address"))
        
        self.same_as_billing_checkbox = QCheckBox("Same as billing address")
        shipping_layout.addRow("", self.same_as_billing_checkbox)
        
        self.shipping_address_line1_edit = QLineEdit()
        self.shipping_address_line1_edit.setPlaceholderText("Street address")
        shipping_layout.addRow("Address Line 1:", self.shipping_address_line1_edit)
        
        self.shipping_address_line2_edit = QLineEdit()
        self.shipping_address_line2_edit.setPlaceholderText("Apartment, suite, unit, building, floor, etc.")
        shipping_layout.addRow("Address Line 2:", self.shipping_address_line2_edit)
        
        self.shipping_city_edit = QLineEdit()
        self.shipping_city_edit.setPlaceholderText("City")
        shipping_layout.addRow("City:", self.shipping_city_edit)
        
        self.shipping_state_edit = QLineEdit()
        self.shipping_state_edit.setPlaceholderText("State/Province")
        shipping_layout.addRow("State:", self.shipping_state_edit)
        
        self.shipping_postal_code_edit = QLineEdit()
        self.shipping_postal_code_edit.setPlaceholderText("Postal Code")
        shipping_layout.addRow("Postal Code:", self.shipping_postal_code_edit)
        
        self.shipping_country_edit = QLineEdit()
        self.shipping_country_edit.setText("USA")
        shipping_layout.addRow("Country:", self.shipping_country_edit)
        
        tab_layout.addWidget(shipping_frame)
        tab_layout.addStretch()
        
        # Connect checkbox
        self.same_as_billing_checkbox.toggled.connect(self.on_same_as_billing_toggled)
        
        return tab_widget
    
    def create_business_tab(self) -> QWidget:
        """Create business tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Business Information
        business_frame = QFrame()
        business_frame.setProperty("class", "form-section")
        business_layout = QFormLayout(business_frame)
        
        self.customer_type_combo = QComboBox()
        self.customer_type_combo.addItems(['Wholesale', 'Retail', 'Distributor', 'Manufacturer', 'Other'])
        business_layout.addRow("Customer Type:", self.customer_type_combo)
        
        self.tax_exempt_checkbox = QCheckBox()
        business_layout.addRow("Tax Exempt:", self.tax_exempt_checkbox)
        
        self.tax_id_edit = QLineEdit()
        self.tax_id_edit.setPlaceholderText("Tax ID / VAT number")
        business_layout.addRow("Tax ID:", self.tax_id_edit)
        
        self.credit_limit_spin = QDoubleSpinBox()
        self.credit_limit_spin.setRange(0, 9999999.99)
        self.credit_limit_spin.setDecimals(2)
        self.credit_limit_spin.setPrefix("$")
        business_layout.addRow("Credit Limit:", self.credit_limit_spin)
        
        self.payment_terms_combo = QComboBox()
        self.payment_terms_combo.addItems(['NET15', 'NET30', 'NET45', 'NET60', 'COD', 'Prepaid'])
        business_layout.addRow("Payment Terms:", self.payment_terms_combo)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Customer notes...")
        business_layout.addRow("Notes:", self.notes_edit)
        
        tab_layout.addWidget(business_frame)
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
        self.save_button = QPushButton("Save Customer")
        self.save_button.setProperty("class", "primary")
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        parent_layout.addLayout(buttons_layout)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Table selection
        if self.customers_table:
            self.customers_table.selection_changed.connect(self.on_customer_selection_changed)
            self.customers_table.row_double_clicked.connect(self.on_customer_double_clicked)
        
        # Buttons
        self.new_customer_button.clicked.connect(self.new_customer)
        self.edit_customer_button.clicked.connect(self.edit_selected_customer)
        self.delete_customer_button.clicked.connect(self.delete_selected_customer)
        
        # Form buttons
        self.save_button.clicked.connect(self.save_customer)
        self.clear_form_button.clicked.connect(self.clear_form)
    
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
                    'contact_person': 'John Smith',
                    'phone': '(555) 123-4567',
                    'email': 'john@abcconstruction.com',
                    'status': 'Active',
                    'customer_type': 'Wholesale'
                },
                {
                    'customer_code': 'CUST-002',
                    'name': 'Jane Doe',
                    'company_name': 'XYZ Manufacturing',
                    'contact_person': 'Jane Doe',
                    'phone': '(555) 234-5678',
                    'email': 'jane@xyzmanufacturing.com',
                    'status': 'Active',
                    'customer_type': 'Retail'
                },
                {
                    'customer_code': 'CUST-003',
                    'name': 'Bob Wilson',
                    'company_name': 'DEF Supplies',
                    'contact_person': 'Bob Wilson',
                    'phone': '(555) 345-6789',
                    'email': 'bob@defsupplies.com',
                    'status': 'Active',
                    'customer_type': 'Distributor'
                }
            ]
            
            # Load into table
            self.customers_table.load_data(customers_data)
            
        except Exception as e:
            logger.error(f"Error loading customers: {e}")
    
    def on_customer_selection_changed(self, selected_data: List[Dict[str, Any]]) -> None:
        """Handle customer selection changes."""
        has_selection = bool(selected_data)
        
        # Enable/disable action buttons
        self.edit_customer_button.setEnabled(has_selection)
        self.delete_customer_button.setEnabled(has_selection)
        
        # Load customer data into form
        if has_selection:
            customer = selected_data[0]
            self.load_customer_into_form(customer)
    
    def on_customer_double_clicked(self, row: int) -> None:
        """Handle double-click on customer."""
        if self.customers_table:
            selected_data = self.customers_table.get_selected_data()
            if selected_data:
                customer = selected_data[0]
                self.customer_selected.emit(customer.get('customer_code', ''))
    
    def load_customer_into_form(self, customer: Dict[str, Any]) -> None:
        """Load customer data into form."""
        # Load basic information
        self.customer_code_edit.setText(customer.get('customer_code', ''))
        self.name_edit.setText(customer.get('name', ''))
        self.company_name_edit.setText(customer.get('company_name', ''))
        self.contact_person_edit.setText(customer.get('contact_person', ''))
        self.phone_edit.setText(customer.get('phone', ''))
        self.email_edit.setText(customer.get('email', ''))
        self.website_edit.setText(customer.get('website', ''))
        self.status_combo.setCurrentText(customer.get('status', 'Active'))
        
        # Load address information
        self.billing_address_line1_edit.setText(customer.get('billing_address_line1', ''))
        self.billing_address_line2_edit.setText(customer.get('billing_address_line2', ''))
        self.billing_city_edit.setText(customer.get('billing_city', ''))
        self.billing_state_edit.setText(customer.get('billing_state', ''))
        self.billing_postal_code_edit.setText(customer.get('billing_postal_code', ''))
        self.billing_country_edit.setText(customer.get('billing_country', 'USA'))
        
        self.shipping_address_line1_edit.setText(customer.get('shipping_address_line1', ''))
        self.shipping_address_line2_edit.setText(customer.get('shipping_address_line2', ''))
        self.shipping_city_edit.setText(customer.get('shipping_city', ''))
        self.shipping_state_edit.setText(customer.get('shipping_state', ''))
        self.shipping_postal_code_edit.setText(customer.get('shipping_postal_code', ''))
        self.shipping_country_edit.setText(customer.get('shipping_country', 'USA'))
        
        # Load business information
        self.customer_type_combo.setCurrentText(customer.get('customer_type', 'Wholesale'))
        self.tax_exempt_checkbox.setChecked(customer.get('tax_exempt', False))
        self.tax_id_edit.setText(customer.get('tax_id', ''))
        
        credit_limit = customer.get('credit_limit', 0)
        if credit_limit:
            self.credit_limit_spin.setValue(float(credit_limit))
        else:
            self.credit_limit_spin.setValue(0)
        
        self.payment_terms_combo.setCurrentText(customer.get('payment_terms', 'NET30'))
        self.notes_edit.setPlainText(customer.get('notes', ''))
    
    def on_same_as_billing_toggled(self, checked: bool) -> None:
        """Handle same as billing address checkbox."""
        if checked:
            # Copy billing address to shipping address
            self.shipping_address_line1_edit.setText(self.billing_address_line1_edit.text())
            self.shipping_address_line2_edit.setText(self.billing_address_line2_edit.text())
            self.shipping_city_edit.setText(self.billing_city_edit.text())
            self.shipping_state_edit.setText(self.billing_state_edit.text())
            self.shipping_postal_code_edit.setText(self.billing_postal_code_edit.text())
            self.shipping_country_edit.setText(self.billing_country_edit.text())
            
            # Disable shipping address fields
            self.shipping_address_line1_edit.setEnabled(False)
            self.shipping_address_line2_edit.setEnabled(False)
            self.shipping_city_edit.setEnabled(False)
            self.shipping_state_edit.setEnabled(False)
            self.shipping_postal_code_edit.setEnabled(False)
            self.shipping_country_edit.setEnabled(False)
        else:
            # Enable shipping address fields
            self.shipping_address_line1_edit.setEnabled(True)
            self.shipping_address_line2_edit.setEnabled(True)
            self.shipping_city_edit.setEnabled(True)
            self.shipping_state_edit.setEnabled(True)
            self.shipping_postal_code_edit.setEnabled(True)
            self.shipping_country_edit.setEnabled(True)
    
    def new_customer(self) -> None:
        """Create new customer."""
        self.clear_form()
        
        # Generate customer code
        customer_code = f"CUST-{str(len(self.customers_table.data_table.filtered_data) + 1).zfill(3)}"
        self.customer_code_edit.setText(customer_code)
        
        # Set default values
        self.status_combo.setCurrentText('Active')
        self.customer_type_combo.setCurrentText('Wholesale')
        self.payment_terms_combo.setCurrentText('NET30')
        self.billing_country_edit.setText('USA')
        self.shipping_country_edit.setText('USA')
        
        # Focus on first field
        self.name_edit.setFocus()
    
    def edit_selected_customer(self) -> None:
        """Edit selected customer."""
        selected_data = self.customers_table.get_selected_data()
        if selected_data:
            customer = selected_data[0]
            self.load_customer_into_form(customer)
    
    def delete_selected_customer(self) -> None:
        """Delete selected customer."""
        selected_data = self.customers_table.get_selected_data()
        if not selected_data:
            return
        
        customer = selected_data[0]
        customer_code = customer.get('customer_code', '')
        customer_name = customer.get('name', '')
        
        if confirm_delete("Customer", f"{customer_name} ({customer_code})"):
            # Delete customer (this would call the service/controller)
            try:
                # Placeholder for actual delete logic
                logger.info(f"Deleting customer: {customer_code}")
                
                # Refresh table
                self.load_customers()
                
                # Clear form
                self.clear_form()
                
                show_info("Success", f"Customer '{customer_name}' deleted successfully!")
                
            except Exception as e:
                logger.error(f"Error deleting customer: {e}")
                show_error("Error", f"Failed to delete customer: {e}")
    
    def save_customer(self) -> None:
        """Save customer data."""
        # Validate form
        is_valid, errors = self.validate_form()
        
        if not is_valid:
            error_text = "Please correct the following errors:\n\n" + "\n".join(f"· {error}" for error in errors)
            show_error("Validation Error", error_text)
            return
        
        # Get customer data
        customer_data = self.get_customer_data()
        
        # Save customer (this would call the service/controller)
        try:
            # Placeholder for actual save logic
            logger.info(f"Saving customer: {customer_data['customer_code']}")
            
            # Show success message
            show_info("Success", f"Customer '{customer_data['customer_code']}' saved successfully!")
            
            # Refresh table
            self.load_customers()
            
            # Emit signal
            self.customer_saved.emit(customer_data['customer_code'])
            
        except Exception as e:
            logger.error(f"Error saving customer: {e}")
            show_error("Error", f"Failed to save customer: {e}")
    
    def validate_form(self) -> tuple[bool, List[str]]:
        """Validate customer form data."""
        errors = []
        
        # Required fields
        if not self.customer_code_edit.text().strip():
            errors.append("Customer Code is required")
        
        if not self.name_edit.text().strip():
            errors.append("Name is required")
        
        if not self.billing_address_line1_edit.text().strip():
            errors.append("Billing Address Line 1 is required")
        
        if not self.billing_city_edit.text().strip():
            errors.append("Billing City is required")
        
        if not self.billing_state_edit.text().strip():
            errors.append("Billing State is required")
        
        if not self.billing_postal_code_edit.text().strip():
            errors.append("Billing Postal Code is required")
        
        return len(errors) == 0, errors
    
    def get_customer_data(self) -> Dict[str, Any]:
        """Get customer data from form."""
        customer_data = {
            'customer_code': self.customer_code_edit.text().strip(),
            'name': self.name_edit.text().strip(),
            'company_name': self.company_name_edit.text().strip(),
            'contact_person': self.contact_person_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'website': self.website_edit.text().strip(),
            'status': self.status_combo.currentText(),
            
            # Billing address
            'billing_address_line1': self.billing_address_line1_edit.text().strip(),
            'billing_address_line2': self.billing_address_line2_edit.text().strip(),
            'billing_city': self.billing_city_edit.text().strip(),
            'billing_state': self.billing_state_edit.text().strip(),
            'billing_postal_code': self.billing_postal_code_edit.text().strip(),
            'billing_country': self.billing_country_edit.text().strip(),
            
            # Shipping address
            'shipping_address_line1': self.shipping_address_line1_edit.text().strip(),
            'shipping_address_line2': self.shipping_address_line2_edit.text().strip(),
            'shipping_city': self.shipping_city_edit.text().strip(),
            'shipping_state': self.shipping_state_edit.text().strip(),
            'shipping_postal_code': self.shipping_postal_code_edit.text().strip(),
            'shipping_country': self.shipping_country_edit.text().strip(),
            
            # Business information
            'customer_type': self.customer_type_combo.currentText(),
            'tax_exempt': self.tax_exempt_checkbox.isChecked(),
            'tax_id': self.tax_id_edit.text().strip(),
            'credit_limit': self.credit_limit_spin.value(),
            'payment_terms': self.payment_terms_combo.currentText(),
            'notes': self.notes_edit.toPlainText().strip(),
            'created_by': 'System'  # Would get from user session
        }
        
        return customer_data
    
    def clear_form(self) -> None:
        """Clear customer form."""
        # Clear basic information
        self.customer_code_edit.clear()
        self.name_edit.clear()
        self.company_name_edit.clear()
        self.contact_person_edit.clear()
        self.phone_edit.clear()
        self.email_edit.clear()
        self.website_edit.clear()
        self.status_combo.setCurrentText('Active')
        
        # Clear billing address
        self.billing_address_line1_edit.clear()
        self.billing_address_line2_edit.clear()
        self.billing_city_edit.clear()
        self.billing_state_edit.clear()
        self.billing_postal_code_edit.clear()
        self.billing_country_edit.setText('USA')
        
        # Clear shipping address
        self.same_as_billing_checkbox.setChecked(False)
        self.shipping_address_line1_edit.clear()
        self.shipping_address_line2_edit.clear()
        self.shipping_city_edit.clear()
        self.shipping_state_edit.clear()
        self.shipping_postal_code_edit.clear()
        self.shipping_country_edit.setText('USA')
        
        # Clear business information
        self.customer_type_combo.setCurrentText('Wholesale')
        self.tax_exempt_checkbox.setChecked(False)
        self.tax_id_edit.clear()
        self.credit_limit_spin.setValue(0)
        self.payment_terms_combo.setCurrentText('NET30')
        self.notes_edit.clear()
    
    def refresh_data(self) -> None:
        """Refresh customers data."""
        self.load_customers()
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.new_customer()
    
    def save(self) -> None:
        """Handle save action."""
        self.save_customer()
    
    def search(self) -> None:
        """Handle search action."""
        if self.customers_table:
            self.customers_table.search_input.setFocus()
            self.customers_table.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save."""
        # Could implement auto-save functionality here
        pass
