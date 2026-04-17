"""
Work Order Management view for XPanda ERP-Lite.
Provides interface for creating and managing production work orders.
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


class WorkOrderManagement(QWidget):
    """Work order management widget for production planning."""
    
    # Signals
    work_order_saved = pyqtSignal(str)
    work_order_cancelled = pyqtSignal()
    work_order_selected = pyqtSignal(str)
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        
        # UI components
        self.work_orders_table: Optional[DataTableWithFilter] = None
        self.work_order_form: Optional[QWidget] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_work_orders()
        
        logger.debug("Work order management initialized")
    
    def setup_ui(self) -> None:
        """Create and layout work order management components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Work Order Management")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setProperty("class", "header")
        main_layout.addWidget(title_label)
        
        # Create splitter for table and form
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Work orders table
        table_widget = self.create_work_orders_table()
        splitter.addWidget(table_widget)
        
        # Right side - Work order form
        form_widget = self.create_work_order_form()
        splitter.addWidget(form_widget)
        
        # Set splitter sizes (50% table, 50% form)
        splitter.setSizes([500, 500])
        
        main_layout.addWidget(splitter)
        
        # Styling is now handled by centralized StyleManager
    
    def create_work_orders_table(self) -> QWidget:
        """Create work orders table widget."""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 10, 0)
        
        # Header
        header_label = QLabel("Work Orders")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setProperty("class", "section-header")
        table_layout.addWidget(header_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.new_work_order_button = QPushButton("New Work Order")
        self.new_work_order_button.setProperty("class", "primary")
        buttons_layout.addWidget(self.new_work_order_button)
        
        self.release_button = QPushButton("Release")
        self.release_button.setProperty("class", "success")
        self.release_button.setEnabled(False)
        buttons_layout.addWidget(self.release_button)
        
        self.complete_button = QPushButton("Complete")
        self.complete_button.setProperty("class", "success")
        self.complete_button.setEnabled(False)
        buttons_layout.addWidget(self.complete_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("class", "danger")
        self.cancel_button.setEnabled(False)
        buttons_layout.addWidget(self.cancel_button)
        
        buttons_layout.addStretch()
        table_layout.addLayout(buttons_layout)
        
        # Work orders table
        self.work_orders_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'work_order_number', 'title': 'WO #', 'width': 80},
            {'key': 'finished_good_sku', 'title': 'Product SKU', 'width': 120},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'priority', 'title': 'Priority', 'width': 80},
            {'key': 'quantity_ordered', 'title': 'Ordered', 'width': 80},
            {'key': 'quantity_produced', 'title': 'Produced', 'width': 80},
            {'key': 'completion_percentage', 'title': 'Complete %', 'width': 80},
            {'key': 'due_date', 'title': 'Due Date', 'width': 100},
            {'key': 'start_date', 'title': 'Start Date', 'width': 100}
        ]
        
        self.work_orders_table.set_columns(columns)
        table_layout.addWidget(self.work_orders_table)
        
        return table_widget
    
    def create_work_order_form(self) -> QWidget:
        """Create work order form widget."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(10, 0, 0, 0)
        
        # Form tabs
        self.form_tabs = QTabWidget()
        
        # Basic Information tab
        basic_tab = self.create_basic_info_tab()
        self.form_tabs.addTab(basic_tab, "Basic Info")
        
        # Production Details tab
        production_tab = self.create_production_details_tab()
        self.form_tabs.addTab(production_tab, "Production")
        
        # Quality tab
        quality_tab = self.create_quality_tab()
        self.form_tabs.addTab(quality_tab, "Quality")
        
        form_layout.addWidget(self.form_tabs)
        
        # Form action buttons
        self.create_form_buttons(form_layout)
        
        return form_widget
    
    def create_basic_info_tab(self) -> QWidget:
        """Create basic information tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Work Order Information
        info_frame = QFrame()
        info_frame.setProperty("class", "form-section")
        info_layout = QFormLayout(info_frame)
        
        self.work_order_number_edit = QLineEdit()
        self.work_order_number_edit.setPlaceholderText("e.g., WO-001")
        self.work_order_number_edit.setReadOnly(True)
        info_layout.addRow("Work Order #:", self.work_order_number_edit)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Planned', 'Released', 'In Progress', 'Completed', 'Cancelled', 'On Hold'])
        info_layout.addRow("Status:", self.status_combo)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['Low', 'Normal', 'High', 'Urgent'])
        self.priority_combo.setCurrentText('Normal')
        info_layout.addRow("Priority:", self.priority_combo)
        
        # Product Information
        self.finished_good_sku_edit = QLineEdit()
        self.finished_good_sku_edit.setPlaceholderText("e.g., EPS-BLOCK-001")
        info_layout.addRow("Product SKU *:", self.finished_good_sku_edit)
        
        self.finished_good_name_edit = QLineEdit()
        self.finished_good_name_edit.setPlaceholderText("e.g., EPS Block 24x24x96")
        info_layout.addRow("Product Name *:", self.finished_good_name_edit)
        
        # Quantity Information
        self.quantity_ordered_spin = QDoubleSpinBox()
        self.quantity_ordered_spin.setRange(0.0001, 999999.9999)
        self.quantity_ordered_spin.setDecimals(4)
        self.quantity_ordered_spin.setSuffix(" EA")
        info_layout.addRow("Quantity Ordered *:", self.quantity_ordered_spin)
        
        self.quantity_produced_spin = QDoubleSpinBox()
        self.quantity_produced_spin.setRange(0, 999999.9999)
        self.quantity_produced_spin.setDecimals(4)
        self.quantity_produced_spin.setSuffix(" EA")
        self.quantity_produced_spin.setValue(0)
        info_layout.addRow("Quantity Produced:", self.quantity_produced_spin)
        
        # Dates
        self.order_date_edit = QDateEdit()
        self.order_date_edit.setCalendarPopup(True)
        self.order_date_edit.setDate(QDate.currentDate())
        info_layout.addRow("Order Date:", self.order_date_edit)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        info_layout.addRow("Start Date:", self.start_date_edit)
        
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate().addDays(7))
        info_layout.addRow("Due Date:", self.due_date_edit)
        
        self.completion_date_edit = QDateEdit()
        self.completion_date_edit.setCalendarPopup(True)
        info_layout.addRow("Completion Date:", self.completion_date_edit)
        
        tab_layout.addWidget(info_frame)
        tab_layout.addStretch()
        
        return tab_widget
    
    def create_production_details_tab(self) -> QWidget:
        """Create production details tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Production Information
        prod_frame = QFrame()
        prod_frame.setProperty("class", "form-section")
        prod_layout = QFormLayout(prod_frame)
        
        self.bom_combo = QComboBox()
        self.bom_combo.setEditable(False)
        # Will be populated with available BOMs
        prod_layout.addRow("BOM:", self.bom_combo)
        
        self.estimated_hours_spin = QDoubleSpinBox()
        self.estimated_hours_spin.setRange(0, 999999.99)
        self.estimated_hours_spin.setDecimals(2)
        self.estimated_hours_spin.setSuffix(" hrs")
        prod_layout.addRow("Estimated Hours:", self.estimated_hours_spin)
        
        self.actual_hours_spin = QDoubleSpinBox()
        self.actual_hours_spin.setRange(0, 999999.99)
        self.actual_hours_spin.setDecimals(2)
        self.actual_hours_spin.setSuffix(" hrs")
        prod_layout.addRow("Actual Hours:", self.actual_hours_spin)
        
        self.yield_spin = QDoubleSpinBox()
        self.yield_spin.setRange(0, 100)
        self.yield_spin.setDecimals(2)
        self.yield_spin.setValue(100.0)
        self.yield_spin.setSuffix(" %")
        prod_layout.addRow("Yield %:", self.yield_spin)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Production notes...")
        prod_layout.addRow("Notes:", self.notes_edit)
        
        tab_layout.addWidget(prod_frame)
        tab_layout.addStretch()
        
        return tab_widget
    
    def create_quality_tab(self) -> QWidget:
        """Create quality tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Quality Information
        quality_frame = QFrame()
        quality_frame.setProperty("class", "form-section")
        quality_layout = QFormLayout(quality_frame)
        
        self.quality_status_combo = QComboBox()
        self.quality_status_combo.addItems(['Pending', 'Passed', 'Failed', 'Rework'])
        quality_layout.addRow("Quality Status:", self.quality_status_combo)
        
        self.inspector_edit = QLineEdit()
        self.inspector_edit.setPlaceholderText("Inspector name")
        quality_layout.addRow("Inspector:", self.inspector_edit)
        
        self.inspection_date_edit = QDateEdit()
        self.inspection_date_edit.setCalendarPopup(True)
        quality_layout.addRow("Inspection Date:", self.inspection_date_edit)
        
        self.quality_notes_edit = QTextEdit()
        self.quality_notes_edit.setMaximumHeight(100)
        self.quality_notes_edit.setPlaceholderText("Quality inspection notes...")
        quality_layout.addRow("Quality Notes:", self.quality_notes_edit)
        
        tab_layout.addWidget(quality_frame)
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
        self.save_button = QPushButton("Save Work Order")
        self.save_button.setProperty("class", "primary")
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        parent_layout.addLayout(buttons_layout)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Table selection
        if self.work_orders_table:
            self.work_orders_table.selection_changed.connect(self.on_work_order_selection_changed)
            self.work_orders_table.row_double_clicked.connect(self.on_work_order_double_clicked)
        
        # Buttons
        self.new_work_order_button.clicked.connect(self.new_work_order)
        self.release_button.clicked.connect(self.release_work_order)
        self.complete_button.clicked.connect(self.complete_work_order)
        self.cancel_button.clicked.connect(self.cancel_work_order)
        
        # Form buttons
        self.save_button.clicked.connect(self.save_work_order)
        self.clear_form_button.clicked.connect(self.clear_form)
    
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
                    'priority': 'Normal',
                    'quantity_ordered': 100,
                    'quantity_produced': 75,
                    'completion_percentage': 75.0,
                    'due_date': '2024-04-20',
                    'start_date': '2024-04-15'
                },
                {
                    'work_order_number': 'WO-002',
                    'finished_good_sku': 'EPS-BLOCK-002',
                    'status': 'Planned',
                    'priority': 'High',
                    'quantity_ordered': 50,
                    'quantity_produced': 0,
                    'completion_percentage': 0.0,
                    'due_date': '2024-04-25',
                    'start_date': ''
                },
                {
                    'work_order_number': 'WO-003',
                    'finished_good_sku': 'EPS-BEAD-001',
                    'status': 'Completed',
                    'priority': 'Normal',
                    'quantity_ordered': 200,
                    'quantity_produced': 200,
                    'completion_percentage': 100.0,
                    'due_date': '2024-04-15',
                    'start_date': '2024-04-10'
                }
            ]
            
            # Load into table
            self.work_orders_table.load_data(work_orders_data)
            
        except Exception as e:
            logger.error(f"Error loading work orders: {e}")
    
    def on_work_order_selection_changed(self, selected_data: List[Dict[str, Any]]) -> None:
        """Handle work order selection changes."""
        has_selection = bool(selected_data)
        
        # Enable/disable action buttons based on selection and status
        if has_selection:
            work_order = selected_data[0]
            status = work_order.get('status', '')
            
            self.release_button.setEnabled(status == 'Planned')
            self.complete_button.setEnabled(status == 'In Progress')
            self.cancel_button.setEnabled(status in ['Planned', 'Released'])
            
            # Load work order data into form
            self.load_work_order_into_form(work_order)
        else:
            self.release_button.setEnabled(False)
            self.complete_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
    
    def on_work_order_double_clicked(self, row: int) -> None:
        """Handle double-click on work order."""
        if self.work_orders_table:
            selected_data = self.work_orders_table.get_selected_data()
            if selected_data:
                work_order = selected_data[0]
                self.work_order_selected.emit(work_order.get('work_order_number', ''))
    
    def load_work_order_into_form(self, work_order: Dict[str, Any]) -> None:
        """Load work order data into form."""
        # Load basic information
        self.work_order_number_edit.setText(work_order.get('work_order_number', ''))
        self.status_combo.setCurrentText(work_order.get('status', 'Planned'))
        self.priority_combo.setCurrentText(work_order.get('priority', 'Normal'))
        
        self.finished_good_sku_edit.setText(work_order.get('finished_good_sku', ''))
        self.finished_good_name_edit.setText(work_order.get('finished_good_name', ''))
        
        self.quantity_ordered_spin.setValue(float(work_order.get('quantity_ordered', 0)))
        self.quantity_produced_spin.setValue(float(work_order.get('quantity_produced', 0)))
        
        # Load dates
        if work_order.get('order_date'):
            self.order_date_edit.setDate(QDate.fromString(work_order['order_date'], 'yyyy-MM-dd'))
        
        if work_order.get('start_date'):
            self.start_date_edit.setDate(QDate.fromString(work_order['start_date'], 'yyyy-MM-dd'))
        
        if work_order.get('due_date'):
            self.due_date_edit.setDate(QDate.fromString(work_order['due_date'], 'yyyy-MM-dd'))
        
        if work_order.get('completion_date'):
            self.completion_date_edit.setDate(QDate.fromString(work_order['completion_date'], 'yyyy-MM-dd'))
        
        # Load production details
        self.estimated_hours_spin.setValue(float(work_order.get('estimated_hours', 0)))
        self.actual_hours_spin.setValue(float(work_order.get('actual_hours', 0)))
        self.yield_spin.setValue(float(work_order.get('yield_percentage', 100)))
        
        self.notes_edit.setPlainText(work_order.get('notes', ''))
        
        # Load quality information
        self.quality_status_combo.setCurrentText(work_order.get('quality_status', 'Pending'))
        self.inspector_edit.setText(work_order.get('inspector', ''))
        
        if work_order.get('inspection_date'):
            self.inspection_date_edit.setDate(QDate.fromString(work_order['inspection_date'], 'yyyy-MM-dd'))
        
        self.quality_notes_edit.setPlainText(work_order.get('quality_notes', ''))
    
    def new_work_order(self) -> None:
        """Create new work order."""
        self.clear_form()
        
        # Generate work order number
        work_order_number = f"WO-{str(len(self.work_orders_table.data_table.filtered_data) + 1).zfill(3)}"
        self.work_order_number_edit.setText(work_order_number)
        
        # Set default values
        self.status_combo.setCurrentText('Planned')
        self.priority_combo.setCurrentText('Normal')
        self.order_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setDate(QDate.currentDate().addDays(7))
        
        # Focus on first field
        self.finished_good_sku_edit.setFocus()
    
    def release_work_order(self) -> None:
        """Release selected work order."""
        selected_data = self.work_orders_table.get_selected_data()
        if not selected_data:
            return
        
        work_order = selected_data[0]
        work_order_number = work_order.get('work_order_number', '')
        
        if confirm_delete("Release Work Order", f"Release work order {work_order_number}? This will start production."):
            # Update status to 'Released'
            work_order['status'] = 'Released'
            work_order['start_date'] = QDate.currentDate().toString('yyyy-MM-dd')
            
            # Refresh table
            self.load_work_orders()
            
            show_info("Success", f"Work order {work_order_number} released successfully!")
    
    def complete_work_order(self) -> None:
        """Complete selected work order."""
        selected_data = self.work_orders_table.get_selected_data()
        if not selected_data:
            return
        
        work_order = selected_data[0]
        work_order_number = work_order.get('work_order_number', '')
        
        if confirm_delete("Complete Work Order", f"Complete work order {work_order_number}? This will finish production."):
            # Update status to 'Completed'
            work_order['status'] = 'Completed'
            work_order['completion_date'] = QDate.currentDate().toString('yyyy-MM-dd')
            work_order['quantity_produced'] = work_order.get('quantity_ordered', 0)
            work_order['completion_percentage'] = 100.0
            
            # Refresh table
            self.load_work_orders()
            
            show_info("Success", f"Work order {work_order_number} completed successfully!")
    
    def cancel_work_order(self) -> None:
        """Cancel selected work order."""
        selected_data = self.work_orders_table.get_selected_data()
        if not selected_data:
            return
        
        work_order = selected_data[0]
        work_order_number = work_order.get('work_order_number', '')
        
        if confirm_delete("Cancel Work Order", f"Cancel work order {work_order_number}? This action cannot be undone."):
            # Update status to 'Cancelled'
            work_order['status'] = 'Cancelled'
            
            # Refresh table
            self.load_work_orders()
            
            show_info("Success", f"Work order {work_order_number} cancelled successfully!")
    
    def save_work_order(self) -> None:
        """Save work order data."""
        # Validate form
        is_valid, errors = self.validate_form()
        
        if not is_valid:
            error_text = "Please correct the following errors:\n\n" + "\n".join(f"· {error}" for error in errors)
            show_error("Validation Error", error_text)
            return
        
        # Get work order data
        work_order_data = self.get_work_order_data()
        
        # Save work order (this would call the service/controller)
        try:
            # Placeholder for actual save logic
            logger.info(f"Saving work order: {work_order_data['work_order_number']}")
            
            # Show success message
            show_info("Success", f"Work order '{work_order_data['work_order_number']}' saved successfully!")
            
            # Refresh table
            self.load_work_orders()
            
            # Emit signal
            self.work_order_saved.emit(work_order_data['work_order_number'])
            
        except Exception as e:
            logger.error(f"Error saving work order: {e}")
            show_error("Error", f"Failed to save work order: {e}")
    
    def validate_form(self) -> tuple[bool, List[str]]:
        """Validate work order form data."""
        errors = []
        
        # Required fields
        if not self.finished_good_sku_edit.text().strip():
            errors.append("Product SKU is required")
        
        if not self.finished_good_name_edit.text().strip():
            errors.append("Product Name is required")
        
        if self.quantity_ordered_spin.value() <= 0:
            errors.append("Quantity Ordered must be greater than 0")
        
        return len(errors) == 0, errors
    
    def get_work_order_data(self) -> Dict[str, Any]:
        """Get work order data from form."""
        work_order_data = {
            'work_order_number': self.work_order_number_edit.text().strip(),
            'status': self.status_combo.currentText(),
            'priority': self.priority_combo.currentText(),
            'finished_good_sku': self.finished_good_sku_edit.text().strip(),
            'finished_good_name': self.finished_good_name_edit.text().strip(),
            'quantity_ordered': self.quantity_ordered_spin.value(),
            'quantity_produced': self.quantity_produced_spin.value(),
            'order_date': self.order_date_edit.date().toString('yyyy-MM-dd'),
            'start_date': self.start_date_edit.date().toString('yyyy-MM-dd'),
            'due_date': self.due_date_edit.date().toString('yyyy-MM-dd'),
            'completion_date': self.completion_date_edit.date().toString('yyyy-MM-dd'),
            'estimated_hours': self.estimated_hours_spin.value(),
            'actual_hours': self.actual_hours_spin.value(),
            'yield_percentage': self.yield_spin.value(),
            'notes': self.notes_edit.toPlainText().strip(),
            'quality_status': self.quality_status_combo.currentText(),
            'inspector': self.inspector_edit.text().strip(),
            'inspection_date': self.inspection_date_edit.date().toString('yyyy-MM-dd'),
            'quality_notes': self.quality_notes_edit.toPlainText().strip(),
            'created_by': 'System'  # Would get from user session
        }
        
        return work_order_data
    
    def clear_form(self) -> None:
        """Clear work order form."""
        self.work_order_number_edit.clear()
        self.status_combo.setCurrentText('Planned')
        self.priority_combo.setCurrentText('Normal')
        
        self.finished_good_sku_edit.clear()
        self.finished_good_name_edit.clear()
        
        self.quantity_ordered_spin.setValue(1.0)
        self.quantity_produced_spin.setValue(0.0)
        
        self.order_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setDate(QDate.currentDate().addDays(7))
        self.completion_date_edit.setDate(QDate.currentDate())
        
        self.estimated_hours_spin.setValue(0.0)
        self.actual_hours_spin.setValue(0.0)
        self.yield_spin.setValue(100.0)
        
        self.notes_edit.clear()
        
        self.quality_status_combo.setCurrentText('Pending')
        self.inspector_edit.clear()
        self.inspection_date_edit.setDate(QDate.currentDate())
        self.quality_notes_edit.clear()
    
    def refresh_data(self) -> None:
        """Refresh work orders data."""
        self.load_work_orders()
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.new_work_order()
    
    def save(self) -> None:
        """Handle save action."""
        self.save_work_order()
    
    def search(self) -> None:
        """Handle search action."""
        if self.work_orders_table:
            self.work_orders_table.search_input.setFocus()
            self.work_orders_table.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save."""
        # Could implement auto-save functionality here
        pass
