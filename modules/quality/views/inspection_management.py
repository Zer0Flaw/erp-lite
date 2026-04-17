"""
Inspection Management view for XPanda ERP-Lite.
Provides interface for creating and managing quality inspections.
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


class InspectionManagement(QWidget):
    """Inspection management widget for quality control activities."""
    
    # Signals
    inspection_saved = pyqtSignal(str)
    inspection_cancelled = pyqtSignal()
    inspection_selected = pyqtSignal(str)
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        
        # UI components
        self.inspections_table: Optional[DataTableWithFilter] = None
        self.inspection_form: Optional[QWidget] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_inspections()
        
        logger.debug("Inspection management initialized")
    
    def setup_ui(self) -> None:
        """Create and layout inspection management components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Inspection Management")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setProperty("class", "header")
        main_layout.addWidget(title_label)
        
        # Create splitter for table and form
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Inspections table
        table_widget = self.create_inspections_table()
        splitter.addWidget(table_widget)
        
        # Right side - Inspection form
        form_widget = self.create_inspection_form()
        splitter.addWidget(form_widget)
        
        # Set splitter sizes (50% table, 50% form)
        splitter.setSizes([500, 500])
        
        main_layout.addWidget(splitter)
        
        # Styling is now handled by centralized StyleManager
    
    def create_inspections_table(self) -> QWidget:
        """Create inspections table widget."""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 10, 0)
        
        # Header
        header_label = QLabel("Inspections")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setProperty("class", "section-header")
        table_layout.addWidget(header_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.new_inspection_button = QPushButton("New Inspection")
        self.new_inspection_button.setProperty("class", "primary")
        buttons_layout.addWidget(self.new_inspection_button)
        
        self.start_inspection_button = QPushButton("Start Inspection")
        self.start_inspection_button.setProperty("class", "success")
        self.start_inspection_button.setEnabled(False)
        buttons_layout.addWidget(self.start_inspection_button)
        
        self.complete_inspection_button = QPushButton("Complete")
        self.complete_inspection_button.setProperty("class", "success")
        self.complete_inspection_button.setEnabled(False)
        buttons_layout.addWidget(self.complete_inspection_button)
        
        self.cancel_inspection_button = QPushButton("Cancel")
        self.cancel_inspection_button.setProperty("class", "danger")
        self.cancel_inspection_button.setEnabled(False)
        buttons_layout.addWidget(self.cancel_inspection_button)
        
        buttons_layout.addStretch()
        table_layout.addLayout(buttons_layout)
        
        # Inspections table
        self.inspections_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'inspection_number', 'title': 'Inspection #', 'width': 100},
            {'key': 'inspection_type', 'title': 'Type', 'width': 100},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'material_sku', 'title': 'Material SKU', 'width': 120},
            {'key': 'batch_number', 'title': 'Batch', 'width': 80},
            {'key': 'inspector', 'title': 'Inspector', 'width': 100},
            {'key': 'overall_result', 'title': 'Result', 'width': 80},
            {'key': 'inspection_date', 'title': 'Date', 'width': 100}
        ]
        
        self.inspections_table.set_columns(columns)
        table_layout.addWidget(self.inspections_table)
        
        return table_widget
    
    def create_inspection_form(self) -> QWidget:
        """Create inspection form widget."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(10, 0, 0, 0)
        
        # Form tabs
        self.form_tabs = QTabWidget()
        
        # Basic Information tab
        basic_tab = self.create_basic_info_tab()
        self.form_tabs.addTab(basic_tab, "Basic Info")
        
        # Inspection Lines tab
        lines_tab = self.create_inspection_lines_tab()
        self.form_tabs.addTab(lines_tab, "Inspection Lines")
        
        # Results tab
        results_tab = self.create_results_tab()
        self.form_tabs.addTab(results_tab, "Results")
        
        form_layout.addWidget(self.form_tabs)
        
        # Form action buttons
        self.create_form_buttons(form_layout)
        
        return form_widget
    
    def create_basic_info_tab(self) -> QWidget:
        """Create basic information tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Inspection Information
        info_frame = QFrame()
        info_frame.setProperty("class", "form-section")
        info_layout = QFormLayout(info_frame)
        
        self.inspection_number_edit = QLineEdit()
        self.inspection_number_edit.setPlaceholderText("e.g., INSP-001")
        self.inspection_number_edit.setReadOnly(True)
        info_layout.addRow("Inspection Number:", self.inspection_number_edit)
        
        self.inspection_type_combo = QComboBox()
        self.inspection_type_combo.addItems(['Incoming', 'In Process', 'Final', 'Customer Return'])
        info_layout.addRow("Inspection Type *:", self.inspection_type_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Scheduled', 'In Progress', 'Passed', 'Failed', 'Rework Required', 'Cancelled'])
        info_layout.addRow("Status:", self.status_combo)
        
        # Related entities
        self.work_order_combo = QComboBox()
        self.work_order_combo.setEditable(False)
        # Will be populated with available work orders
        info_layout.addRow("Work Order:", self.work_order_combo)
        
        self.material_sku_edit = QLineEdit()
        self.material_sku_edit.setPlaceholderText("e.g., EPS-BLOCK-001")
        info_layout.addRow("Material SKU:", self.material_sku_edit)
        
        self.batch_number_edit = QLineEdit()
        self.batch_number_edit.setPlaceholderText("e.g., BATCH-001")
        info_layout.addRow("Batch Number:", self.batch_number_edit)
        
        # Inspection details
        self.inspection_date_edit = QDateEdit()
        self.inspection_date_edit.setCalendarPopup(True)
        self.inspection_date_edit.setDate(QDate.currentDate())
        info_layout.addRow("Inspection Date:", self.inspection_date_edit)
        
        self.inspector_edit = QLineEdit()
        self.inspector_edit.setPlaceholderText("Inspector name")
        info_layout.addRow("Inspector *:", self.inspector_edit)
        
        self.quantity_inspected_spin = QSpinBox()
        self.quantity_inspected_spin.setRange(1, 999999)
        info_layout.addRow("Quantity Inspected *:", self.quantity_inspected_spin)
        
        # Documentation
        self.inspection_procedure_edit = QLineEdit()
        self.inspection_procedure_edit.setPlaceholderText("Procedure reference")
        info_layout.addRow("Procedure:", self.inspection_procedure_edit)
        
        self.specifications_edit = QLineEdit()
        self.specifications_edit.setPlaceholderText("Specification reference")
        info_layout.addRow("Specifications:", self.specifications_edit)
        
        tab_layout.addWidget(info_frame)
        tab_layout.addStretch()
        
        return tab_widget
    
    def create_inspection_lines_tab(self) -> QWidget:
        """Create inspection lines tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_label = QLabel("Inspection Criteria")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setProperty("class", "section-header")
        tab_layout.addWidget(header_label)
        
        # Action buttons for lines
        lines_buttons_layout = QHBoxLayout()
        
        self.add_line_button = QPushButton("Add Criteria")
        self.add_line_button.setProperty("class", "primary")
        lines_buttons_layout.addWidget(self.add_line_button)
        
        self.remove_line_button = QPushButton("Remove Selected")
        self.remove_line_button.setProperty("class", "danger")
        self.remove_line_button.setEnabled(False)
        lines_buttons_layout.addWidget(self.remove_line_button)
        
        lines_buttons_layout.addStretch()
        tab_layout.addLayout(lines_buttons_layout)
        
        # Inspection lines table
        self.inspection_lines_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'line_number', 'title': 'Line #', 'width': 60},
            {'key': 'characteristic', 'title': 'Characteristic', 'resizable': True},
            {'key': 'specification', 'title': 'Specification', 'resizable': True},
            {'key': 'measured_value', 'title': 'Measured', 'width': 80},
            {'key': 'tolerance_min', 'title': 'Min Tol', 'width': 80},
            {'key': 'tolerance_max', 'title': 'Max Tol', 'width': 80},
            {'key': 'result', 'title': 'Result', 'width': 60},
            {'key': 'deviation', 'title': 'Deviation', 'width': 80}
        ]
        
        self.inspection_lines_table.set_columns(columns)
        tab_layout.addWidget(self.inspection_lines_table)
        
        return tab_widget
    
    def create_results_tab(self) -> QWidget:
        """Create results tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Results Information
        results_frame = QFrame()
        results_frame.setProperty("class", "form-section")
        results_layout = QFormLayout(results_frame)
        
        self.quantity_passed_spin = QSpinBox()
        self.quantity_passed_spin.setRange(0, 999999)
        results_layout.addRow("Quantity Passed:", self.quantity_passed_spin)
        
        self.quantity_failed_spin = QSpinBox()
        self.quantity_failed_spin.setRange(0, 999999)
        results_layout.addRow("Quantity Failed:", self.quantity_failed_spin)
        
        self.quantity_rework_spin = QSpinBox()
        self.quantity_rework_spin.setRange(0, 999999)
        results_layout.addRow("Quantity Rework:", self.quantity_rework_spin)
        
        self.acceptance_rate_spin = QDoubleSpinBox()
        self.acceptance_rate_spin.setRange(0, 100)
        self.acceptance_rate_spin.setDecimals(2)
        self.acceptance_rate_spin.setSuffix(" %")
        results_layout.addRow("Acceptance Rate:", self.acceptance_rate_spin)
        
        self.overall_result_combo = QComboBox()
        self.overall_result_combo.addItems(['', 'PASS', 'FAIL', 'REWORK'])
        results_layout.addRow("Overall Result:", self.overall_result_combo)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Inspection notes...")
        results_layout.addRow("Notes:", self.notes_edit)
        
        tab_layout.addWidget(results_frame)
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
        self.save_button = QPushButton("Save Inspection")
        self.save_button.setProperty("class", "primary")
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        parent_layout.addLayout(buttons_layout)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Table selection
        if self.inspections_table:
            self.inspections_table.selection_changed.connect(self.on_inspection_selection_changed)
            self.inspections_table.row_double_clicked.connect(self.on_inspection_double_clicked)
        
        # Buttons
        self.new_inspection_button.clicked.connect(self.new_inspection)
        self.start_inspection_button.clicked.connect(self.start_inspection)
        self.complete_inspection_button.clicked.connect(self.complete_inspection)
        self.cancel_inspection_button.clicked.connect(self.cancel_inspection)
        
        # Form buttons
        self.save_button.clicked.connect(self.save_inspection)
        self.clear_form_button.clicked.connect(self.clear_form)
        
        # Inspection lines
        if self.inspection_lines_table:
            self.inspection_lines_table.selection_changed.connect(self.on_line_selection_changed)
        
        self.add_line_button.clicked.connect(self.add_inspection_line)
        self.remove_line_button.clicked.connect(self.remove_selected_line)
    
    def load_inspections(self) -> None:
        """Load inspections into table."""
        if not self.inspections_table:
            return
        
        try:
            # Placeholder data - will be replaced with actual database query
            inspections_data = [
                {
                    'inspection_number': 'INSP-001',
                    'inspection_type': 'Incoming',
                    'status': 'Completed',
                    'material_sku': 'EPS-BLOCK-001',
                    'batch_number': 'BATCH-001',
                    'inspector': 'John Smith',
                    'overall_result': 'PASS',
                    'inspection_date': '2024-04-15'
                },
                {
                    'inspection_number': 'INSP-002',
                    'inspection_type': 'In Process',
                    'status': 'In Progress',
                    'material_sku': 'EPS-BLOCK-002',
                    'batch_number': 'BATCH-002',
                    'inspector': 'Jane Doe',
                    'overall_result': 'FAIL',
                    'inspection_date': '2024-04-16'
                },
                {
                    'inspection_number': 'INSP-003',
                    'inspection_type': 'Final',
                    'status': 'Scheduled',
                    'material_sku': 'EPS-BEAD-001',
                    'batch_number': 'BATCH-003',
                    'inspector': 'Bob Wilson',
                    'overall_result': '',
                    'inspection_date': '2024-04-17'
                }
            ]
            
            # Load into table
            self.inspections_table.load_data(inspections_data)
            
        except Exception as e:
            logger.error(f"Error loading inspections: {e}")
    
    def on_inspection_selection_changed(self, selected_data: List[Dict[str, Any]]) -> None:
        """Handle inspection selection changes."""
        has_selection = bool(selected_data)
        
        # Enable/disable action buttons based on selection and status
        if has_selection:
            inspection = selected_data[0]
            status = inspection.get('status', '')
            
            self.start_inspection_button.setEnabled(status == 'Scheduled')
            self.complete_inspection_button.setEnabled(status == 'In Progress')
            self.cancel_inspection_button.setEnabled(status in ['Scheduled', 'In Progress'])
            
            # Load inspection data into form
            self.load_inspection_into_form(inspection)
        else:
            self.start_inspection_button.setEnabled(False)
            self.complete_inspection_button.setEnabled(False)
            self.cancel_inspection_button.setEnabled(False)
    
    def on_inspection_double_clicked(self, row: int) -> None:
        """Handle double-click on inspection."""
        if self.inspections_table:
            selected_data = self.inspections_table.get_selected_data()
            if selected_data:
                inspection = selected_data[0]
                self.inspection_selected.emit(inspection.get('inspection_number', ''))
    
    def load_inspection_into_form(self, inspection: Dict[str, Any]) -> None:
        """Load inspection data into form."""
        # Load basic information
        self.inspection_number_edit.setText(inspection.get('inspection_number', ''))
        self.inspection_type_combo.setCurrentText(inspection.get('inspection_type', 'Incoming'))
        self.status_combo.setCurrentText(inspection.get('status', 'Scheduled'))
        
        self.work_order_combo.setCurrentText(inspection.get('work_order', ''))
        self.material_sku_edit.setText(inspection.get('material_sku', ''))
        self.batch_number_edit.setText(inspection.get('batch_number', ''))
        
        # Load inspection details
        if inspection.get('inspection_date'):
            self.inspection_date_edit.setDate(QDate.fromString(inspection['inspection_date'], 'yyyy-MM-dd'))
        
        self.inspector_edit.setText(inspection.get('inspector', ''))
        self.quantity_inspected_spin.setValue(inspection.get('quantity_inspected', 1))
        
        # Load documentation
        self.inspection_procedure_edit.setText(inspection.get('inspection_procedure', ''))
        self.specifications_edit.setText(inspection.get('specifications', ''))
        
        # Load results
        self.quantity_passed_spin.setValue(inspection.get('quantity_passed', 0))
        self.quantity_failed_spin.setValue(inspection.get('quantity_failed', 0))
        self.quantity_rework_spin.setValue(inspection.get('quantity_rework', 0))
        
        acceptance_rate = inspection.get('acceptance_rate')
        if acceptance_rate is not None:
            self.acceptance_rate_spin.setValue(float(acceptance_rate))
        else:
            self.acceptance_rate_spin.setValue(0)
        
        self.overall_result_combo.setCurrentText(inspection.get('overall_result', ''))
        
        # Load notes
        self.notes_edit.setPlainText(inspection.get('notes', ''))
        
        # Update acceptance rate calculation
        self.update_acceptance_rate()
    
    def on_line_selection_changed(self, selected_data: List[Dict[str, Any]]) -> None:
        """Handle line selection changes."""
        self.remove_line_button.setEnabled(bool(selected_data))
    
    def add_inspection_line(self) -> None:
        """Add a new inspection line."""
        # This would open a dialog to add inspection criteria
        # For now, add a placeholder line
        new_line = {
            'line_number': len(self.inspection_lines_table.data_table.filtered_data) + 1,
            'characteristic': '',
            'specification': '',
            'measured_value': 0.0,
            'tolerance_min': 0.0,
            'tolerance_max': 0.0,
            'result': '',
            'deviation': 0.0
        }
        
        if self.inspection_lines_table:
            current_data = self.inspection_lines_table.data_table.filtered_data
            current_data.append(new_line)
            self.inspection_lines_table.load_data(current_data)
    
    def remove_selected_line(self) -> None:
        """Remove selected inspection line."""
        if not self.inspection_lines_table:
            return
        
        selected_data = self.inspection_lines_table.get_selected_data()
        if not selected_data:
            return
        
        # Confirm deletion
        if confirm_delete("Inspection Line", f"{len(selected_data)} selected line(s)"):
            # Remove selected lines
            current_data = self.inspection_lines_table.data_table.filtered_data
            for line in selected_data:
                if line in current_data:
                    current_data.remove(line)
            
            self.inspection_lines_table.load_data(current_data)
    
    def update_acceptance_rate(self) -> None:
        """Update acceptance rate calculation."""
        total = self.quantity_passed_spin.value() + self.quantity_failed_spin.value() + self.quantity_rework_spin.value()
        
        if total > 0:
            passed = self.quantity_passed_spin.value()
            rate = (passed / total) * 100
            self.acceptance_rate_spin.setValue(rate)
        else:
            self.acceptance_rate_spin.setValue(0)
    
    def new_inspection(self) -> None:
        """Create new inspection."""
        self.clear_form()
        
        # Generate inspection number
        inspection_number = f"INSP-{str(len(self.inspections_table.data_table.filtered_data) + 1).zfill(3)}"
        self.inspection_number_edit.setText(inspection_number)
        
        # Set default values
        self.status_combo.setCurrentText('Scheduled')
        self.inspection_type_combo.setCurrentText('Incoming')
        self.inspection_date_edit.setDate(QDate.currentDate())
        self.quantity_inspected_spin.setValue(1)
        
        # Focus on first field
        self.inspector_edit.setFocus()
    
    def start_inspection(self) -> None:
        """Start selected inspection."""
        selected_data = self.inspections_table.get_selected_data()
        if not selected_data:
            return
        
        inspection = selected_data[0]
        inspection_number = inspection.get('inspection_number', '')
        
        if confirm_delete("Start Inspection", f"Start inspection {inspection_number}? This will change status to 'In Progress'."):
            # Update status to 'In Progress'
            inspection['status'] = 'In Progress'
            
            # Refresh table
            self.load_inspections()
            
            show_info("Success", f"Inspection {inspection_number} started successfully!")
    
    def complete_inspection(self) -> None:
        """Complete selected inspection."""
        selected_data = self.inspections_table.get_selected_data()
        if not selected_data:
            return
        
        inspection = selected_data[0]
        inspection_number = inspection.get('inspection_number', '')
        
        if confirm_delete("Complete Inspection", f"Complete inspection {inspection_number}? This will finalize the results."):
            # Update status to 'Completed'
            inspection['status'] = 'Completed'
            
            # Refresh table
            self.load_inspections()
            
            show_info("Success", f"Inspection {inspection_number} completed successfully!")
    
    def cancel_inspection(self) -> None:
        """Cancel selected inspection."""
        selected_data = self.inspections_table.get_selected_data()
        if not selected_data:
            return
        
        inspection = selected_data[0]
        inspection_number = inspection.get('inspection_number', '')
        
        if confirm_delete("Cancel Inspection", f"Cancel inspection {inspection_number}? This action cannot be undone."):
            # Update status to 'Cancelled'
            inspection['status'] = 'Cancelled'
            
            # Refresh table
            self.load_inspections()
            
            show_info("Success", f"Inspection {inspection_number} cancelled successfully!")
    
    def save_inspection(self) -> None:
        """Save inspection data."""
        # Validate form
        is_valid, errors = self.validate_form()
        
        if not is_valid:
            error_text = "Please correct the following errors:\n\n" + "\n".join(f"· {error}" for error in errors)
            show_error("Validation Error", error_text)
            return
        
        # Get inspection data
        inspection_data = self.get_inspection_data()
        
        # Save inspection (this would call the service/controller)
        try:
            # Placeholder for actual save logic
            logger.info(f"Saving inspection: {inspection_data['inspection_number']}")
            
            # Show success message
            show_info("Success", f"Inspection '{inspection_data['inspection_number']}' saved successfully!")
            
            # Refresh table
            self.load_inspections()
            
            # Emit signal
            self.inspection_saved.emit(inspection_data['inspection_number'])
            
        except Exception as e:
            logger.error(f"Error saving inspection: {e}")
            show_error("Error", f"Failed to save inspection: {e}")
    
    def validate_form(self) -> tuple[bool, List[str]]:
        """Validate inspection form data."""
        errors = []
        
        # Required fields
        if not self.inspector_edit.text().strip():
            errors.append("Inspector is required")
        
        if self.quantity_inspected_spin.value() <= 0:
            errors.append("Quantity Inspected must be greater than 0")
        
        # Validate inspection lines
        if self.inspection_lines_table:
            current_data = self.inspection_lines_table.data_table.filtered_data
            if not current_data:
                errors.append("At least one inspection line is required")
        
        return len(errors) == 0, errors
    
    def get_inspection_data(self) -> Dict[str, Any]:
        """Get inspection data from form."""
        inspection_data = {
            'inspection_number': self.inspection_number_edit.text().strip(),
            'inspection_type': self.inspection_type_combo.currentText(),
            'status': self.status_combo.currentText(),
            'work_order': self.work_order_combo.currentText(),
            'material_sku': self.material_sku_edit.text().strip(),
            'batch_number': self.batch_number_edit.text().strip(),
            'inspection_date': self.inspection_date_edit.date().toString('yyyy-MM-dd'),
            'inspector': self.inspector_edit.text().strip(),
            'quantity_inspected': self.quantity_inspected_spin.value(),
            'quantity_passed': self.quantity_passed_spin.value(),
            'quantity_failed': self.quantity_failed_spin.value(),
            'quantity_rework': self.quantity_rework_spin.value(),
            'acceptance_rate': self.acceptance_rate_spin.value(),
            'overall_result': self.overall_result_combo.currentText(),
            'inspection_procedure': self.inspection_procedure_edit.text().strip(),
            'specifications': self.specifications_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip(),
            'created_by': 'System'  # Would get from user session
        }
        
        # Add inspection lines
        if self.inspection_lines_table:
            inspection_data['inspection_lines'] = self.inspection_lines_table.data_table.filtered_data
        
        return inspection_data
    
    def clear_form(self) -> None:
        """Clear inspection form."""
        # Clear basic information
        self.inspection_number_edit.clear()
        self.inspection_type_combo.setCurrentText('Incoming')
        self.status_combo.setCurrentText('Scheduled')
        
        self.work_order_combo.setCurrentText('')
        self.material_sku_edit.clear()
        self.batch_number_edit.clear()
        
        # Clear inspection details
        self.inspection_date_edit.setDate(QDate.currentDate())
        self.inspector_edit.clear()
        self.quantity_inspected_spin.setValue(1)
        
        # Clear documentation
        self.inspection_procedure_edit.clear()
        self.specifications_edit.clear()
        
        # Clear results
        self.quantity_passed_spin.setValue(0)
        self.quantity_failed_spin.setValue(0)
        self.quantity_rework_spin.setValue(0)
        self.acceptance_rate_spin.setValue(0)
        self.overall_result_combo.setCurrentText('')
        
        # Clear notes
        self.notes_edit.clear()
        
        # Clear inspection lines
        if self.inspection_lines_table:
            self.inspection_lines_table.load_data([])
    
    def refresh_data(self) -> None:
        """Refresh inspections data."""
        self.load_inspections()
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.new_inspection()
    
    def save(self) -> None:
        """Handle save action."""
        self.save_inspection()
    
    def search(self) -> None:
        """Handle search action."""
        if self.inspections_table:
            self.inspections_table.search_input.setFocus()
            self.inspections_table.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save."""
        # Could implement auto-save functionality here
        pass
