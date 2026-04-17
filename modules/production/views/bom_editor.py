"""
BOM Editor view for XPanda ERP-Lite.
Provides interface for creating and editing Bills of Materials.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit,
    QFormLayout, QScrollArea, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete

logger = logging.getLogger(__name__)


class BOMEditor(QWidget):
    """BOM editor widget for creating and editing Bills of Materials."""
    
    # Signals
    bom_saved = pyqtSignal(str)
    bom_cancelled = pyqtSignal()
    line_added = pyqtSignal()
    line_removed = pyqtSignal(int)
    
    def __init__(self, db_manager, settings, bom_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        self.bom_data = bom_data or {}
        self.is_editing = bool(bom_data)
        
        # UI components
        self.bom_lines_table: Optional[DataTableWithFilter] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_bom_data()
        
        logger.debug("BOM editor initialized")
    
    def setup_ui(self) -> None:
        """Create and layout BOM editor components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title = "Edit Bill of Materials" if self.is_editing else "New Bill of Materials"
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setProperty("class", "header")
        main_layout.addWidget(title_label)
        
        # Create splitter for form and lines
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - BOM form
        form_widget = self.create_bom_form()
        splitter.addWidget(form_widget)
        
        # Right side - BOM lines
        lines_widget = self.create_bom_lines_widget()
        splitter.addWidget(lines_widget)
        
        # Set splitter sizes (40% form, 60% lines)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
        # Bottom buttons
        self.create_action_buttons(main_layout)
        
        # Styling is now handled by centralized StyleManager
    
    def create_bom_form(self) -> QWidget:
        """Create BOM information form."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 10, 0)
        
        # BOM Information section
        info_frame = QFrame()
        info_frame.setProperty("class", "form-section")
        info_layout = QFormLayout(info_frame)
        
        # Basic fields
        self.bom_code_edit = QLineEdit()
        self.bom_code_edit.setPlaceholderText("e.g., BOM-001")
        info_layout.addRow("BOM Code *:", self.bom_code_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., EPS Block 24x24x96")
        info_layout.addRow("Name *:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Optional description...")
        info_layout.addRow("Description:", self.description_edit)
        
        self.version_edit = QLineEdit()
        self.version_edit.setText("1.0")
        info_layout.addRow("Version:", self.version_edit)
        
        # Product information
        self.finished_good_sku_edit = QLineEdit()
        self.finished_good_sku_edit.setPlaceholderText("e.g., EPS-BLOCK-001")
        info_layout.addRow("Finished Good SKU *:", self.finished_good_sku_edit)
        
        self.finished_good_name_edit = QLineEdit()
        self.finished_good_name_edit.setPlaceholderText("e.g., EPS Block 24x24x96")
        info_layout.addRow("Finished Good Name *:", self.finished_good_name_edit)
        
        self.standard_quantity_spin = QDoubleSpinBox()
        self.standard_quantity_spin.setRange(0.0001, 999999.9999)
        self.standard_quantity_spin.setDecimals(4)
        self.standard_quantity_spin.setValue(1.0)
        self.standard_quantity_spin.setSuffix(" EA")
        info_layout.addRow("Standard Quantity:", self.standard_quantity_spin)
        
        self.uom_combo = QComboBox()
        self.uom_combo.addItems(['EA', 'LB', 'KG', 'FT', 'M', 'GAL', 'L'])
        info_layout.addRow("Unit of Measure:", self.uom_combo)
        
        form_layout.addWidget(info_frame)
        
        # Production Information section
        prod_frame = QFrame()
        prod_frame.setProperty("class", "form-section")
        prod_layout = QFormLayout(prod_frame)
        
        self.cycle_time_spin = QDoubleSpinBox()
        self.cycle_time_spin.setRange(0, 999999.99)
        self.cycle_time_spin.setDecimals(2)
        self.cycle_time_spin.setSuffix(" min")
        prod_layout.addRow("Cycle Time:", self.cycle_time_spin)
        
        self.setup_time_spin = QDoubleSpinBox()
        self.setup_time_spin.setRange(0, 999999.99)
        self.setup_time_spin.setDecimals(2)
        self.setup_time_spin.setSuffix(" min")
        prod_layout.addRow("Setup Time:", self.setup_time_spin)
        
        self.yield_spin = QDoubleSpinBox()
        self.yield_spin.setRange(0, 100)
        self.yield_spin.setDecimals(2)
        self.yield_spin.setValue(100.0)
        self.yield_spin.setSuffix(" %")
        prod_layout.addRow("Yield %:", self.yield_spin)
        
        form_layout.addWidget(prod_frame)
        
        # Status and Dates section
        status_frame = QFrame()
        status_frame.setProperty("class", "form-section")
        status_layout = QFormLayout(status_frame)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Draft', 'Active', 'Inactive', 'Archived'])
        status_layout.addRow("Status:", self.status_combo)
        
        self.effective_date_edit = QDateEdit()
        self.effective_date_edit.setCalendarPopup(True)
        self.effective_date_edit.setDate(QDate.currentDate())
        status_layout.addRow("Effective Date:", self.effective_date_edit)
        
        self.expiry_date_edit = QDateEdit()
        self.expiry_date_edit.setCalendarPopup(True)
        self.expiry_date_edit.setDate(QDate.currentDate().addYears(5))
        status_layout.addRow("Expiry Date:", self.expiry_date_edit)
        
        form_layout.addWidget(status_frame)
        
        form_layout.addStretch()
        
        return form_widget
    
    def create_bom_lines_widget(self) -> QWidget:
        """Create BOM lines table widget."""
        lines_widget = QWidget()
        lines_layout = QVBoxLayout(lines_widget)
        lines_layout.setContentsMargins(10, 0, 0, 0)
        
        # Header
        header_label = QLabel("BOM Components")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setProperty("class", "section-header")
        lines_layout.addWidget(header_label)
        
        # Action buttons for lines
        lines_buttons_layout = QHBoxLayout()
        
        self.add_line_button = QPushButton("Add Component")
        self.add_line_button.setProperty("class", "primary")
        lines_buttons_layout.addWidget(self.add_line_button)
        
        self.remove_line_button = QPushButton("Remove Selected")
        self.remove_line_button.setProperty("class", "danger")
        self.remove_line_button.setEnabled(False)
        lines_buttons_layout.addWidget(self.remove_line_button)
        
        lines_buttons_layout.addStretch()
        lines_layout.addLayout(lines_buttons_layout)
        
        # BOM lines table
        self.bom_lines_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'material_sku', 'title': 'Material SKU', 'width': 120},
            {'key': 'material_name', 'title': 'Material Name', 'resizable': True},
            {'key': 'quantity_required', 'title': 'Quantity', 'width': 80},
            {'key': 'unit_of_measure', 'title': 'UOM', 'width': 60},
            {'key': 'unit_cost', 'title': 'Unit Cost', 'width': 80},
            {'key': 'waste_percentage', 'title': 'Waste %', 'width': 70},
            {'key': 'is_optional', 'title': 'Optional', 'width': 70},
            {'key': 'line_cost', 'title': 'Line Cost', 'width': 80}
        ]
        
        self.bom_lines_table.set_columns(columns)
        lines_layout.addWidget(self.bom_lines_table)
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setProperty("class", "form-section")
        summary_layout = QHBoxLayout(summary_frame)
        
        self.total_cost_label = QLabel("Total Cost: $0.00")
        self.total_cost_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.total_cost_label)
        
        summary_layout.addStretch()
        
        lines_layout.addWidget(summary_frame)
        
        return lines_widget
    
    def create_action_buttons(self, parent_layout) -> None:
        """Create action buttons at the bottom."""
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("class", "secondary")
        buttons_layout.addWidget(self.cancel_button)
        
        # Save button
        self.save_button = QPushButton("Save BOM")
        self.save_button.setProperty("class", "primary")
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        parent_layout.addLayout(buttons_layout)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Form field changes
        self.bom_code_edit.textChanged.connect(self.on_form_changed)
        self.name_edit.textChanged.connect(self.on_form_changed)
        self.finished_good_sku_edit.textChanged.connect(self.on_form_changed)
        self.finished_good_name_edit.textChanged.connect(self.on_form_changed)
        
        # BOM lines table
        if self.bom_lines_table:
            self.bom_lines_table.selection_changed.connect(self.on_line_selection_changed)
        
        # Buttons
        self.add_line_button.clicked.connect(self.add_bom_line)
        self.remove_line_button.clicked.connect(self.remove_selected_line)
        self.save_button.clicked.connect(self.save_bom)
        self.cancel_button.clicked.connect(self.cancel_bom)
    
    def load_bom_data(self) -> None:
        """Load BOM data into form."""
        if not self.bom_data:
            return
        
        # Load basic information
        self.bom_code_edit.setText(self.bom_data.get('bom_code', ''))
        self.name_edit.setText(self.bom_data.get('name', ''))
        self.description_edit.setPlainText(self.bom_data.get('description', ''))
        self.version_edit.setText(self.bom_data.get('version', '1.0'))
        
        # Load product information
        self.finished_good_sku_edit.setText(self.bom_data.get('finished_good_sku', ''))
        self.finished_good_name_edit.setText(self.bom_data.get('finished_good_name', ''))
        self.standard_quantity_spin.setValue(float(self.bom_data.get('standard_quantity', 1.0)))
        self.uom_combo.setCurrentText(self.bom_data.get('unit_of_measure', 'EA'))
        
        # Load production information
        self.cycle_time_spin.setValue(float(self.bom_data.get('standard_cycle_time', 0)))
        self.setup_time_spin.setValue(float(self.bom_data.get('setup_time', 0)))
        self.yield_spin.setValue(float(self.bom_data.get('yield_percentage', 100)))
        
        # Load status and dates
        self.status_combo.setCurrentText(self.bom_data.get('status', 'Draft'))
        
        # Load BOM lines
        bom_lines = self.bom_data.get('bom_lines', [])
        if self.bom_lines_table:
            self.bom_lines_table.load_data(bom_lines)
        
        self.update_total_cost()
    
    def on_form_changed(self) -> None:
        """Handle form field changes."""
        # Auto-generate BOM code if name is entered but code is empty
        if not self.bom_code_edit.text().strip() and self.name_edit.text().strip():
            name = self.name_edit.text().strip()
            # Simple auto-generation: take first 3 letters, make uppercase
            code = f"BOM-{name[:3].upper()}-{str(len(name)).zfill(3)}"
            self.bom_code_edit.setText(code)
    
    def on_line_selection_changed(self, selected_data: List[Dict[str, Any]]) -> None:
        """Handle line selection changes."""
        self.remove_line_button.setEnabled(bool(selected_data))
    
    def add_bom_line(self) -> None:
        """Add a new BOM line."""
        # This would open a dialog to select material and enter quantity
        # For now, add a placeholder line
        new_line = {
            'material_sku': '',
            'material_name': '',
            'quantity_required': 1.0,
            'unit_of_measure': 'EA',
            'unit_cost': 0.0,
            'waste_percentage': 0.0,
            'is_optional': False,
            'line_cost': 0.0
        }
        
        if self.bom_lines_table:
            current_data = self.bom_lines_table.data_table.filtered_data
            current_data.append(new_line)
            self.bom_lines_table.load_data(current_data)
        
        self.line_added.emit()
    
    def remove_selected_line(self) -> None:
        """Remove selected BOM line."""
        if not self.bom_lines_table:
            return
        
        selected_data = self.bom_lines_table.get_selected_data()
        if not selected_data:
            return
        
        # Confirm deletion
        if confirm_delete("BOM Line", f"{len(selected_data)} selected line(s)"):
            # Remove selected lines
            current_data = self.bom_lines_table.data_table.filtered_data
            for line in selected_data:
                if line in current_data:
                    current_data.remove(line)
            
            self.bom_lines_table.load_data(current_data)
            self.update_total_cost()
            self.line_removed.emit(len(selected_data))
    
    def update_total_cost(self) -> None:
        """Update total cost display."""
        if not self.bom_lines_table:
            return
        
        current_data = self.bom_lines_table.data_table.filtered_data
        total_cost = sum(float(line.get('line_cost', 0)) for line in current_data)
        self.total_cost_label.setText(f"Total Cost: ${total_cost:,.2f}")
    
    def validate_form(self) -> tuple[bool, List[str]]:
        """Validate BOM form data."""
        errors = []
        
        # Required fields
        if not self.bom_code_edit.text().strip():
            errors.append("BOM Code is required")
        
        if not self.name_edit.text().strip():
            errors.append("Name is required")
        
        if not self.finished_good_sku_edit.text().strip():
            errors.append("Finished Good SKU is required")
        
        if not self.finished_good_name_edit.text().strip():
            errors.append("Finished Good Name is required")
        
        # Validate BOM lines
        if self.bom_lines_table:
            current_data = self.bom_lines_table.data_table.filtered_data
            if not current_data:
                errors.append("At least one BOM line is required")
            
            for i, line in enumerate(current_data):
                if not line.get('material_sku'):
                    errors.append(f"Line {i+1}: Material SKU is required")
                
                if not line.get('quantity_required') or line.get('quantity_required') <= 0:
                    errors.append(f"Line {i+1}: Quantity must be greater than 0")
        
        return len(errors) == 0, errors
    
    def get_bom_data(self) -> Dict[str, Any]:
        """Get BOM data from form."""
        bom_data = {
            'bom_code': self.bom_code_edit.text().strip(),
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'version': self.version_edit.text().strip(),
            'finished_good_sku': self.finished_good_sku_edit.text().strip(),
            'finished_good_name': self.finished_good_name_edit.text().strip(),
            'standard_quantity': self.standard_quantity_spin.value(),
            'unit_of_measure': self.uom_combo.currentText(),
            'standard_cycle_time': self.cycle_time_spin.value(),
            'setup_time': self.setup_time_spin.value(),
            'yield_percentage': self.yield_spin.value(),
            'status': self.status_combo.currentText(),
            'effective_date': self.effective_date_edit.date().toString('yyyy-MM-dd'),
            'expiry_date': self.expiry_date_edit.date().toString('yyyy-MM-dd'),
            'created_by': 'System'  # Would get from user session
        }
        
        # Add BOM lines
        if self.bom_lines_table:
            bom_data['bom_lines'] = self.bom_lines_table.data_table.filtered_data
        
        return bom_data
    
    def save_bom(self) -> None:
        """Save BOM data."""
        # Validate form
        is_valid, errors = self.validate_form()
        
        if not is_valid:
            error_text = "Please correct the following errors:\n\n" + "\n".join(f"· {error}" for error in errors)
            show_error("Validation Error", error_text)
            return
        
        # Get BOM data
        bom_data = self.get_bom_data()
        
        # Save BOM (this would call the service/controller)
        try:
            # Placeholder for actual save logic
            logger.info(f"Saving BOM: {bom_data['bom_code']}")
            
            # Show success message
            show_info("Success", f"BOM '{bom_data['bom_code']}' saved successfully!")
            
            # Emit signal
            self.bom_saved.emit(bom_data['bom_code'])
            
        except Exception as e:
            logger.error(f"Error saving BOM: {e}")
            show_error("Error", f"Failed to save BOM: {e}")
    
    def cancel_bom(self) -> None:
        """Cancel BOM editing."""
        self.bom_cancelled.emit()
    
    def refresh_data(self) -> None:
        """Refresh BOM data (not applicable to editor)."""
        pass
    
    def new_record(self) -> None:
        """Handle new record action."""
        # Clear form for new BOM
        self.bom_code_edit.clear()
        self.name_edit.clear()
        self.description_edit.clear()
        self.version_edit.setText("1.0")
        self.finished_good_sku_edit.clear()
        self.finished_good_name_edit.clear()
        self.standard_quantity_spin.setValue(1.0)
        self.uom_combo.setCurrentText("EA")
        self.cycle_time_spin.setValue(0)
        self.setup_time_spin.setValue(0)
        self.yield_spin.setValue(100)
        self.status_combo.setCurrentText("Draft")
        
        if self.bom_lines_table:
            self.bom_lines_table.load_data([])
        
        self.update_total_cost()
    
    def save(self) -> None:
        """Handle save action."""
        self.save_bom()
    
    def search(self) -> None:
        """Handle search action."""
        # Not applicable to BOM editor
        pass
    
    def auto_save(self) -> None:
        """Handle auto-save."""
        # Could implement auto-save functionality here
        pass
