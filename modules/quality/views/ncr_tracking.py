"""
NCR Tracking view for XPanda ERP-Lite.
Provides interface for creating and managing Non-Conformance Reports.
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


class NCRTracking(QWidget):
    """NCR tracking widget for non-conformance report management."""
    
    # Signals
    ncr_saved = pyqtSignal(str)
    ncr_cancelled = pyqtSignal()
    ncr_selected = pyqtSignal(str)
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        
        # UI components
        self.ncrs_table: Optional[DataTableWithFilter] = None
        self.ncr_form: Optional[QWidget] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_ncrs()
        
        logger.debug("NCR tracking initialized")
    
    def setup_ui(self) -> None:
        """Create and layout NCR tracking components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("NCR Tracking")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setProperty("class", "header")
        main_layout.addWidget(title_label)
        
        # Create splitter for table and form
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - NCRs table
        table_widget = self.create_ncrs_table()
        splitter.addWidget(table_widget)
        
        # Right side - NCR form
        form_widget = self.create_ncr_form()
        splitter.addWidget(form_widget)
        
        # Set splitter sizes (50% table, 50% form)
        splitter.setSizes([500, 500])
        
        main_layout.addWidget(splitter)
        
        # Styling is now handled by centralized StyleManager
    
    def create_ncrs_table(self) -> QWidget:
        """Create NCRs table widget."""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 10, 0)
        
        # Header
        header_label = QLabel("Non-Conformance Reports")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setProperty("class", "section-header")
        table_layout.addWidget(header_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.new_ncr_button = QPushButton("New NCR")
        self.new_ncr_button.setProperty("class", "primary")
        buttons_layout.addWidget(self.new_ncr_button)
        
        self.investigate_button = QPushButton("Investigate")
        self.investigate_button.setProperty("class", "success")
        self.investigate_button.setEnabled(False)
        buttons_layout.addWidget(self.investigate_button)
        
        self.disposition_button = QPushButton("Disposition")
        self.disposition_button.setProperty("class", "success")
        self.disposition_button.setEnabled(False)
        buttons_layout.addWidget(self.disposition_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.setProperty("class", "success")
        self.close_button.setEnabled(False)
        buttons_layout.addWidget(self.close_button)
        
        buttons_layout.addStretch()
        table_layout.addLayout(buttons_layout)
        
        # NCRs table
        self.ncrs_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'ncr_number', 'title': 'NCR #', 'width': 80},
            {'key': 'severity', 'title': 'Severity', 'width': 80},
            {'key': 'status', 'title': 'Status', 'width': 120},
            {'key': 'material_sku', 'title': 'Material SKU', 'width': 120},
            {'key': 'batch_number', 'title': 'Batch', 'width': 80},
            {'key': 'discovery_date', 'title': 'Discovery Date', 'width': 120},
            {'key': 'reported_by', 'title': 'Reported By', 'width': 100},
            {'key': 'days_open', 'title': 'Days Open', 'width': 80}
        ]
        
        self.ncrs_table.set_columns(columns)
        table_layout.addWidget(self.ncrs_table)
        
        return table_widget
    
    def create_ncr_form(self) -> QWidget:
        """Create NCR form widget."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(10, 0, 0, 0)
        
        # Form tabs
        self.form_tabs = QTabWidget()
        
        # Basic Information tab
        basic_tab = self.create_basic_info_tab()
        self.form_tabs.addTab(basic_tab, "Basic Info")
        
        # Investigation tab
        investigation_tab = self.create_investigation_tab()
        self.form_tabs.addTab(investigation_tab, "Investigation")
        
        # Disposition tab
        disposition_tab = self.create_disposition_tab()
        self.form_tabs.addTab(disposition_tab, "Disposition")
        
        form_layout.addWidget(self.form_tabs)
        
        # Form action buttons
        self.create_form_buttons(form_layout)
        
        return form_widget
    
    def create_basic_info_tab(self) -> QWidget:
        """Create basic information tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # NCR Information
        info_frame = QFrame()
        info_frame.setProperty("class", "form-section")
        info_layout = QFormLayout(info_frame)
        
        self.ncr_number_edit = QLineEdit()
        self.ncr_number_edit.setPlaceholderText("e.g., NCR-001")
        self.ncr_number_edit.setReadOnly(True)
        info_layout.addRow("NCR Number:", self.ncr_number_edit)
        
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(['Minor', 'Major', 'Critical'])
        info_layout.addRow("Severity *:", self.severity_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Open', 'Under Investigation', 'Disposition Required', 'Closed', 'Cancelled'])
        info_layout.addRow("Status:", self.status_combo)
        
        # Related entities
        self.inspection_combo = QComboBox()
        self.inspection_combo.setEditable(False)
        # Will be populated with available inspections
        info_layout.addRow("Related Inspection:", self.inspection_combo)
        
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
        
        # Issue details
        self.discovery_date_edit = QDateEdit()
        self.discovery_date_edit.setCalendarPopup(True)
        self.discovery_date_edit.setDate(QDate.currentDate())
        info_layout.addRow("Discovery Date:", self.discovery_date_edit)
        
        self.reported_by_edit = QLineEdit()
        self.reported_by_edit.setPlaceholderText("Reporter name")
        info_layout.addRow("Reported By *:", self.reported_by_edit)
        
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Location of issue")
        info_layout.addRow("Location:", self.location_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Detailed description of the non-conformance...")
        info_layout.addRow("Description *:", self.description_edit)
        
        tab_layout.addWidget(info_frame)
        tab_layout.addStretch()
        
        return tab_widget
    
    def create_investigation_tab(self) -> QWidget:
        """Create investigation tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Investigation Information
        investigation_frame = QFrame()
        investigation_frame.setProperty("class", "form-section")
        investigation_layout = QFormLayout(investigation_frame)
        
        self.investigation_date_edit = QDateEdit()
        self.investigation_date_edit.setCalendarPopup(True)
        investigation_layout.addRow("Investigation Date:", self.investigation_date_edit)
        
        self.investigator_edit = QLineEdit()
        self.investigator_edit.setPlaceholderText("Investigator name")
        investigation_layout.addRow("Investigator:", self.investigator_edit)
        
        self.investigation_summary_edit = QTextEdit()
        self.investigation_summary_edit.setMaximumHeight(100)
        self.investigation_summary_edit.setPlaceholderText("Summary of investigation findings...")
        investigation_layout.addRow("Investigation Summary:", self.investigation_summary_edit)
        
        self.root_cause_edit = QTextEdit()
        self.root_cause_edit.setMaximumHeight(100)
        self.root_cause_edit.setPlaceholderText("Root cause analysis...")
        investigation_layout.addRow("Root Cause:", self.root_cause_edit)
        
        tab_layout.addWidget(investigation_frame)
        tab_layout.addStretch()
        
        return tab_widget
    
    def create_disposition_tab(self) -> QWidget:
        """Create disposition tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Disposition Information
        disposition_frame = QFrame()
        disposition_frame.setProperty("class", "form-section")
        disposition_layout = QFormLayout(disposition_frame)
        
        self.disposition_combo = QComboBox()
        self.disposition_combo.addItems(['Use As Is', 'Rework', 'Repair', 'Scrap', 'Return to Vendor'])
        disposition_layout.addRow("Disposition:", self.disposition_combo)
        
        self.disposition_date_edit = QDateEdit()
        self.disposition_date_edit.setCalendarPopup(True)
        disposition_layout.addRow("Disposition Date:", self.disposition_date_edit)
        
        self.disposition_by_edit = QLineEdit()
        self.disposition_by_edit.setPlaceholderText("Disposition authority")
        disposition_layout.addRow("Disposition By:", self.disposition_by_edit)
        
        self.disposition_notes_edit = QTextEdit()
        self.disposition_notes_edit.setMaximumHeight(100)
        self.disposition_notes_edit.setPlaceholderText("Disposition notes and instructions...")
        disposition_layout.addRow("Disposition Notes:", self.disposition_notes_edit)
        
        # Closure Information
        closure_layout = QFormLayout()
        
        self.closure_date_edit = QDateEdit()
        self.closure_date_edit.setCalendarPopup(True)
        closure_layout.addRow("Closure Date:", self.closure_date_edit)
        
        self.closed_by_edit = QLineEdit()
        self.closed_by_edit.setPlaceholderText("Closed by")
        closure_layout.addRow("Closed By:", self.closed_by_edit)
        
        self.closure_notes_edit = QTextEdit()
        self.closure_notes_edit.setMaximumHeight(100)
        self.closure_notes_edit.setPlaceholderText("Closure notes...")
        closure_layout.addRow("Closure Notes:", self.closure_notes_edit)
        
        tab_layout.addWidget(disposition_frame)
        tab_layout.addLayout(closure_layout)
        
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
        self.save_button = QPushButton("Save NCR")
        self.save_button.setProperty("class", "primary")
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        parent_layout.addLayout(buttons_layout)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Table selection
        if self.ncrs_table:
            self.ncrs_table.selection_changed.connect(self.on_ncr_selection_changed)
            self.ncrs_table.row_double_clicked.connect(self.on_ncr_double_clicked)
        
        # Buttons
        self.new_ncr_button.clicked.connect(self.new_ncr)
        self.investigate_button.clicked.connect(self.investigate_ncr)
        self.disposition_button.clicked.connect(self.disposition_ncr)
        self.close_button.clicked.connect(self.close_ncr)
        
        # Form buttons
        self.save_button.clicked.connect(self.save_ncr)
        self.clear_form_button.clicked.connect(self.clear_form)
    
    def load_ncrs(self) -> None:
        """Load NCRs into table."""
        if not self.ncrs_table:
            return
        
        try:
            # Placeholder data - will be replaced with actual database query
            ncrs_data = [
                {
                    'ncr_number': 'NCR-001',
                    'severity': 'Major',
                    'status': 'Open',
                    'material_sku': 'EPS-BLOCK-002',
                    'batch_number': 'BATCH-002',
                    'discovery_date': '2024-04-16',
                    'reported_by': 'Jane Doe',
                    'days_open': 1
                },
                {
                    'ncr_number': 'NCR-002',
                    'severity': 'Critical',
                    'status': 'Under Investigation',
                    'material_sku': 'EPS-BLOCK-003',
                    'batch_number': 'BATCH-004',
                    'discovery_date': '2024-04-15',
                    'reported_by': 'John Smith',
                    'days_open': 2
                },
                {
                    'ncr_number': 'NCR-003',
                    'severity': 'Minor',
                    'status': 'Closed',
                    'material_sku': 'EPS-BEAD-001',
                    'batch_number': 'BATCH-005',
                    'discovery_date': '2024-04-14',
                    'reported_by': 'Bob Wilson',
                    'days_open': 3
                }
            ]
            
            # Load into table
            self.ncrs_table.load_data(ncrs_data)
            
        except Exception as e:
            logger.error(f"Error loading NCRs: {e}")
    
    def on_ncr_selection_changed(self, selected_data: List[Dict[str, Any]]) -> None:
        """Handle NCR selection changes."""
        has_selection = bool(selected_data)
        
        # Enable/disable action buttons based on selection and status
        if has_selection:
            ncr = selected_data[0]
            status = ncr.get('status', '')
            
            self.investigate_button.setEnabled(status == 'Open')
            self.disposition_button.setEnabled(status in ['Under Investigation', 'Disposition Required'])
            self.close_button.setEnabled(status in ['Disposition Required', 'Closed'])
            
            # Load NCR data into form
            self.load_ncr_into_form(ncr)
        else:
            self.investigate_button.setEnabled(False)
            self.disposition_button.setEnabled(False)
            self.close_button.setEnabled(False)
    
    def on_ncr_double_clicked(self, row: int) -> None:
        """Handle double-click on NCR."""
        if self.ncrs_table:
            selected_data = self.ncrs_table.get_selected_data()
            if selected_data:
                ncr = selected_data[0]
                self.ncr_selected.emit(ncr.get('ncr_number', ''))
    
    def load_ncr_into_form(self, ncr: Dict[str, Any]) -> None:
        """Load NCR data into form."""
        # Load basic information
        self.ncr_number_edit.setText(ncr.get('ncr_number', ''))
        self.severity_combo.setCurrentText(ncr.get('severity', 'Minor'))
        self.status_combo.setCurrentText(ncr.get('status', 'Open'))
        
        self.inspection_combo.setCurrentText(ncr.get('inspection', ''))
        self.work_order_combo.setCurrentText(ncr.get('work_order', ''))
        self.material_sku_edit.setText(ncr.get('material_sku', ''))
        self.batch_number_edit.setText(ncr.get('batch_number', ''))
        
        # Load issue details
        if ncr.get('discovery_date'):
            self.discovery_date_edit.setDate(QDate.fromString(ncr['discovery_date'], 'yyyy-MM-dd'))
        
        self.reported_by_edit.setText(ncr.get('reported_by', ''))
        self.location_edit.setText(ncr.get('location', ''))
        
        self.description_edit.setPlainText(ncr.get('description', ''))
        
        # Load investigation information
        if ncr.get('investigation_date'):
            self.investigation_date_edit.setDate(QDate.fromString(ncr['investigation_date'], 'yyyy-MM-dd'))
        
        self.investigator_edit.setText(ncr.get('investigator', ''))
        self.investigation_summary_edit.setPlainText(ncr.get('investigation_summary', ''))
        self.root_cause_edit.setPlainText(ncr.get('root_cause', ''))
        
        # Load disposition information
        self.disposition_combo.setCurrentText(ncr.get('disposition', ''))
        
        if ncr.get('disposition_date'):
            self.disposition_date_edit.setDate(QDate.fromString(ncr['disposition_date'], 'yyyy-MM-dd'))
        
        self.disposition_by_edit.setText(ncr.get('disposition_by', ''))
        self.disposition_notes_edit.setPlainText(ncr.get('disposition_notes', ''))
        
        # Load closure information
        if ncr.get('closure_date'):
            self.closure_date_edit.setDate(QDate.fromString(ncr['closure_date'], 'yyyy-MM-dd'))
        
        self.closed_by_edit.setText(ncr.get('closed_by', ''))
        self.closure_notes_edit.setPlainText(ncr.get('closure_notes', ''))
    
    def new_ncr(self) -> None:
        """Create new NCR."""
        self.clear_form()
        
        # Generate NCR number
        ncr_number = f"NCR-{str(len(self.ncrs_table.data_table.filtered_data) + 1).zfill(3)}"
        self.ncr_number_edit.setText(ncr_number)
        
        # Set default values
        self.severity_combo.setCurrentText('Minor')
        self.status_combo.setCurrentText('Open')
        self.discovery_date_edit.setDate(QDate.currentDate())
        
        # Focus on first field
        self.reported_by_edit.setFocus()
    
    def investigate_ncr(self) -> None:
        """Investigate selected NCR."""
        selected_data = self.ncrs_table.get_selected_data()
        if not selected_data:
            return
        
        ncr = selected_data[0]
        ncr_number = ncr.get('ncr_number', '')
        
        if confirm_delete("Investigate NCR", f"Start investigation for NCR {ncr_number}?"):
            # Update status to 'Under Investigation'
            ncr['status'] = 'Under Investigation'
            ncr['investigation_date'] = QDate.currentDate().toString('yyyy-MM-dd')
            
            # Refresh table
            self.load_ncrs()
            
            show_info("Success", f"NCR {ncr_number} investigation started successfully!")
    
    def disposition_ncr(self) -> None:
        """Disposition selected NCR."""
        selected_data = self.ncrs_table.get_selected_data()
        if not selected_data:
            return
        
        ncr = selected_data[0]
        ncr_number = ncr.get('ncr_number', '')
        
        if confirm_delete("Disposition NCR", f"Finalize disposition for NCR {ncr_number}?"):
            # Update status to 'Disposition Required'
            ncr['status'] = 'Disposition Required'
            ncr['disposition_date'] = QDate.currentDate().toString('yyyy-MM-dd')
            
            # Refresh table
            self.load_ncrs()
            
            show_info("Success", f"NCR {ncr_number} disposition finalized successfully!")
    
    def close_ncr(self) -> None:
        """Close selected NCR."""
        selected_data = self.ncrs_table.get_selected_data()
        if not selected_data:
            return
        
        ncr = selected_data[0]
        ncr_number = ncr.get('ncr_number', '')
        
        if confirm_delete("Close NCR", f"Close NCR {ncr_number}? This action cannot be undone."):
            # Update status to 'Closed'
            ncr['status'] = 'Closed'
            ncr['closure_date'] = QDate.currentDate().toString('yyyy-MM-dd')
            
            # Refresh table
            self.load_ncrs()
            
            show_info("Success", f"NCR {ncr_number} closed successfully!")
    
    def save_ncr(self) -> None:
        """Save NCR data."""
        # Validate form
        is_valid, errors = self.validate_form()
        
        if not is_valid:
            error_text = "Please correct the following errors:\n\n" + "\n".join(f"· {error}" for error in errors)
            show_error("Validation Error", error_text)
            return
        
        # Get NCR data
        ncr_data = self.get_ncr_data()
        
        # Save NCR (this would call the service/controller)
        try:
            # Placeholder for actual save logic
            logger.info(f"Saving NCR: {ncr_data['ncr_number']}")
            
            # Show success message
            show_info("Success", f"NCR '{ncr_data['ncr_number']}' saved successfully!")
            
            # Refresh table
            self.load_ncrs()
            
            # Emit signal
            self.ncr_saved.emit(ncr_data['ncr_number'])
            
        except Exception as e:
            logger.error(f"Error saving NCR: {e}")
            show_error("Error", f"Failed to save NCR: {e}")
    
    def validate_form(self) -> tuple[bool, List[str]]:
        """Validate NCR form data."""
        errors = []
        
        # Required fields
        if not self.reported_by_edit.text().strip():
            errors.append("Reported By is required")
        
        if not self.description_edit.toPlainText().strip():
            errors.append("Description is required")
        
        return len(errors) == 0, errors
    
    def get_ncr_data(self) -> Dict[str, Any]:
        """Get NCR data from form."""
        ncr_data = {
            'ncr_number': self.ncr_number_edit.text().strip(),
            'severity': self.severity_combo.currentText(),
            'status': self.status_combo.currentText(),
            'inspection': self.inspection_combo.currentText(),
            'work_order': self.work_order_combo.currentText(),
            'material_sku': self.material_sku_edit.text().strip(),
            'batch_number': self.batch_number_edit.text().strip(),
            'discovery_date': self.discovery_date_edit.date().toString('yyyy-MM-dd'),
            'reported_by': self.reported_by_edit.text().strip(),
            'location': self.location_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'investigation_date': self.investigation_date_edit.date().toString('yyyy-MM-dd'),
            'investigator': self.investigator_edit.text().strip(),
            'investigation_summary': self.investigation_summary_edit.toPlainText().strip(),
            'root_cause': self.root_cause_edit.toPlainText().strip(),
            'disposition': self.disposition_combo.currentText(),
            'disposition_date': self.disposition_date_edit.date().toString('yyyy-MM-dd'),
            'disposition_by': self.disposition_by_edit.text().strip(),
            'disposition_notes': self.disposition_notes_edit.toPlainText().strip(),
            'closure_date': self.closure_date_edit.date().toString('yyyy-MM-dd'),
            'closed_by': self.closed_by_edit.text().strip(),
            'closure_notes': self.closure_notes_edit.toPlainText().strip(),
            'created_by': 'System'  # Would get from user session
        }
        
        return ncr_data
    
    def clear_form(self) -> None:
        """Clear NCR form."""
        # Clear basic information
        self.ncr_number_edit.clear()
        self.severity_combo.setCurrentText('Minor')
        self.status_combo.setCurrentText('Open')
        
        self.inspection_combo.setCurrentText('')
        self.work_order_combo.setCurrentText('')
        self.material_sku_edit.clear()
        self.batch_number_edit.clear()
        
        # Clear issue details
        self.discovery_date_edit.setDate(QDate.currentDate())
        self.reported_by_edit.clear()
        self.location_edit.clear()
        
        self.description_edit.clear()
        
        # Clear investigation information
        self.investigation_date_edit.setDate(QDate.currentDate())
        self.investigator_edit.clear()
        self.investigation_summary_edit.clear()
        self.root_cause_edit.clear()
        
        # Clear disposition information
        self.disposition_combo.setCurrentText('')
        self.disposition_date_edit.setDate(QDate.currentDate())
        self.disposition_by_edit.clear()
        self.disposition_notes_edit.clear()
        
        # Clear closure information
        self.closure_date_edit.setDate(QDate.currentDate())
        self.closed_by_edit.clear()
        self.closure_notes_edit.clear()
    
    def refresh_data(self) -> None:
        """Refresh NCRs data."""
        self.load_ncrs()
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.new_ncr()
    
    def save(self) -> None:
        """Handle save action."""
        self.save_ncr()
    
    def search(self) -> None:
        """Handle search action."""
        if self.ncrs_table:
            self.ncrs_table.search_input.setFocus()
            self.ncrs_table.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save."""
        # Could implement auto-save functionality here
        pass
