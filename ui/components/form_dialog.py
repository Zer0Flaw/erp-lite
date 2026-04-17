"""
Reusable form dialog component for XPanda ERP-Lite.
Provides a standardized dialog for creating and editing records.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QSizePolicy,
    QMessageBox, QDateEdit, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QValidator

logger = logging.getLogger(__name__)


class FormField:
    """Represents a form field with its configuration."""
    
    def __init__(self, 
                 key: str, 
                 label: str, 
                 field_type: str = 'text',
                 required: bool = False,
                 default_value: Any = None,
                 options: Optional[List[str]] = None,
                 validator: Optional[QValidator] = None,
                 placeholder: Optional[str] = None,
                 help_text: Optional[str] = None,
                 min_value: Optional[float] = None,
                 max_value: Optional[float] = None,
                 decimals: int = 2):
        self.key = key
        self.label = label
        self.field_type = field_type
        self.required = required
        self.default_value = default_value
        self.options = options or []
        self.validator = validator
        self.placeholder = placeholder
        self.help_text = help_text
        self.min_value = min_value
        self.max_value = max_value
        self.decimals = decimals
        self.widget = None


class FormDialog(QDialog):
    """
    Standardized form dialog for creating and editing records.
    """
    
    def __init__(self, title: str, fields: List[FormField], parent=None):
        super().__init__(parent)
        
        self.title = title
        self.fields = fields
        self.field_widgets: Dict[str, QWidget] = {}
        self.validation_errors: Dict[str, str] = {}
        
        self.setup_ui()
        self.setup_connections()
        self.set_default_values()
    
    def setup_ui(self) -> None:
        """Create dialog UI."""
        self.setWindowTitle(self.title)
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Scroll area for form content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Form container
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        self.form_layout.setSpacing(15)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Create form fields
        self.create_form_fields()
        
        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area)
        
        # Error display
        self.error_label = QLabel()
        self.error_label.setProperty("class", "error")
        self.error_label.setVisible(False)
        self.error_label.setWordWrap(True)
        main_layout.addWidget(self.error_label)
        
        # Dialog buttons
        self.create_buttons(main_layout)
        
        # Styling
        self.setStyleSheet("""
            QLabel[class="error"] {
                color: #E74C3C;
                font-weight: bold;
                padding: 10px;
                background-color: #FADBD8;
                border: 1px solid #E74C3C;
                border-radius: 4px;
            }
            
            QLabel[class="help"] {
                color: #7F8C8D;
                font-size: 11px;
                font-style: italic;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #DEE2E6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def create_form_fields(self) -> None:
        """Create form field widgets."""
        for field in self.fields:
            widget = self.create_field_widget(field)
            if widget:
                self.field_widgets[field.key] = widget
                
                # Create field layout with optional help text
                field_container = QWidget()
                field_layout = QVBoxLayout(field_container)
                field_layout.setContentsMargins(0, 0, 0, 0)
                field_layout.setSpacing(5)
                
                # Add the main widget
                field_layout.addWidget(widget)
                
                # Add help text if provided
                if field.help_text:
                    help_label = QLabel(field.help_text)
                    help_label.setProperty("class", "help")
                    field_layout.addWidget(help_label)
                
                # Add to form layout
                self.form_layout.addRow(field.label + ":", field_container)
                
                # Mark required fields
                if field.required:
                    label = self.form_layout.labelForField(field_container)
                    if label:
                        label.setText(label.text() + " *")
    
    def create_field_widget(self, field: FormField) -> Optional[QWidget]:
        """Create appropriate widget for field type."""
        try:
            if field.field_type == 'text':
                widget = QLineEdit()
                if field.placeholder:
                    widget.setPlaceholderText(field.placeholder)
                if field.validator:
                    widget.setValidator(field.validator)
                field.widget = widget
                
            elif field.field_type == 'textarea':
                widget = QTextEdit()
                widget.setMaximumHeight(100)
                if field.placeholder:
                    widget.setPlaceholderText(field.placeholder)
                field.widget = widget
                
            elif field.field_type == 'select':
                widget = QComboBox()
                widget.setEditable(False)
                widget.addItems(field.options)
                field.widget = widget
                
            elif field.field_type == 'multiselect':
                widget = QComboBox()
                widget.setEditable(True)
                # For multiselect, we'd need a custom widget or use QListWidget
                widget.addItems(field.options)
                field.widget = widget
                
            elif field.field_type == 'number':
                widget = QDoubleSpinBox()
                widget.setDecimals(field.decimals)
                if field.min_value is not None:
                    widget.setMinimum(field.min_value)
                if field.max_value is not None:
                    widget.setMaximum(field.max_value)
                widget.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
                field.widget = widget
                
            elif field.field_type == 'integer':
                widget = QSpinBox()
                if field.min_value is not None:
                    widget.setMinimum(int(field.min_value))
                if field.max_value is not None:
                    widget.setMaximum(int(field.max_value))
                field.widget = widget
                
            elif field.field_type == 'checkbox':
                widget = QCheckBox()
                field.widget = widget
                
            elif field.field_type == 'date':
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
                field.widget = widget
                
            elif field.field_type == 'readonly':
                widget = QLineEdit()
                widget.setReadOnly(True)
                field.widget = widget
                
            else:
                logger.warning(f"Unknown field type: {field.field_type}")
                return None
            
            return widget
            
        except Exception as e:
            logger.error(f"Error creating field widget for {field.key}: {e}")
            return None
    
    def create_buttons(self, parent_layout) -> None:
        """Create dialog buttons."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("class", "secondary")
        button_layout.addWidget(self.cancel_button)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setProperty("class", "success")
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)
        
        parent_layout.addLayout(button_layout)
    
    def setup_connections(self) -> None:
        """Connect signals."""
        self.save_button.clicked.connect(self.accept_form)
        self.cancel_button.clicked.connect(self.reject)
        
        # Connect field validation
        for field in self.fields:
            if field.widget and hasattr(field.widget, 'textChanged'):
                field.widget.textChanged.connect(lambda: self.validate_field(field.key))
    
    def set_default_values(self) -> None:
        """Set default values for all fields."""
        for field in self.fields:
            if field.default_value is not None and field.key in self.field_widgets:
                self.set_field_value(field.key, field.default_value)
    
    def set_field_value(self, key: str, value: Any) -> None:
        """Set value for a specific field."""
        if key not in self.field_widgets:
            return
        
        widget = self.field_widgets[key]
        field = next((f for f in self.fields if f.key == key), None)
        
        if not field:
            return
        
        try:
            if field.field_type in ['text', 'readonly']:
                widget.setText(str(value))
            elif field.field_type == 'textarea':
                widget.setPlainText(str(value))
            elif field.field_type in ['select', 'multiselect']:
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif field.field_type in ['number', 'integer']:
                widget.setValue(float(value))
            elif field.field_type == 'checkbox':
                widget.setChecked(bool(value))
            elif field.field_type == 'date':
                if isinstance(value, str):
                    date = QDate.fromString(value, 'yyyy-MM-dd')
                    if date.isValid():
                        widget.setDate(date)
                elif isinstance(value, QDate):
                    widget.setDate(value)
        except Exception as e:
            logger.error(f"Error setting field value for {key}: {e}")
    
    def get_field_value(self, key: str) -> Any:
        """Get value from a specific field."""
        if key not in self.field_widgets:
            return None
        
        widget = self.field_widgets[key]
        field = next((f for f in self.fields if f.key == key), None)
        
        if not field:
            return None
        
        try:
            if field.field_type in ['text', 'readonly']:
                return widget.text().strip()
            elif field.field_type == 'textarea':
                return widget.toPlainText().strip()
            elif field.field_type in ['select', 'multiselect']:
                return widget.currentText()
            elif field.field_type == 'number':
                return widget.value()
            elif field.field_type == 'integer':
                return widget.value()
            elif field.field_type == 'checkbox':
                return widget.isChecked()
            elif field.field_type == 'date':
                return widget.date().toString('yyyy-MM-dd')
        except Exception as e:
            logger.error(f"Error getting field value for {key}: {e}")
            return None
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get all form data as dictionary."""
        data = {}
        
        for field in self.fields:
            value = self.get_field_value(field.key)
            
            # Handle empty values for required fields
            if field.required and not value:
                self.validation_errors[field.key] = f"{field.label} is required"
            else:
                data[field.key] = value
        
        return data
    
    def set_form_data(self, data: Dict[str, Any]) -> None:
        """Set form data from dictionary."""
        for key, value in data.items():
            self.set_field_value(key, value)
    
    def validate_field(self, field_key: str) -> bool:
        """Validate a specific field."""
        if field_key not in self.field_widgets:
            return True
        
        field = next((f for f in self.fields if f.key == field_key), None)
        if not field:
            return True
        
        value = self.get_field_value(field_key)
        
        # Check required fields
        if field.required and not value:
            self.validation_errors[field_key] = f"{field.label} is required"
            return False
        
        # Clear previous error if validation passes
        if field_key in self.validation_errors:
            del self.validation_errors[field_key]
        
        return True
    
    def validate_form(self) -> Tuple[bool, List[str]]:
        """Validate all form fields."""
        self.validation_errors.clear()
        errors = []
        
        # Validate all fields
        for field in self.fields:
            if not self.validate_field(field.key):
                errors.append(self.validation_errors[field.key])
        
        return len(errors) == 0, errors
    
    def show_errors(self, errors: List[str]) -> None:
        """Display validation errors."""
        if errors:
            error_text = "Please correct the following errors:\n\n" + "\n".join(f"· {error}" for error in errors)
            self.error_label.setText(error_text)
            self.error_label.setVisible(True)
        else:
            self.error_label.clear()
            self.error_label.setVisible(False)
    
    def accept_form(self) -> None:
        """Handle form acceptance."""
        # Validate form
        is_valid, errors = self.validate_form()
        
        if not is_valid:
            self.show_errors(errors)
            return
        
        # Get form data
        form_data = self.get_form_data()
        
        # Emit accepted signal with form data
        self.form_data = form_data
        super().accept()
    
    def reject(self) -> None:
        """Handle form cancellation."""
        # Clear errors
        self.error_label.clear()
        self.error_label.setVisible(False)
        
        # Call parent reject
        super().reject()


class MaterialFormDialog(FormDialog):
    """Specialized form dialog for material records."""
    
    def __init__(self, material_data: Optional[Dict[str, Any]] = None, parent=None):
        # Define material form fields
        fields = [
            FormField('sku', 'SKU', 'text', required=True, placeholder='e.g., EPS-BEAD-001'),
            FormField('name', 'Material Name', 'text', required=True, placeholder='e.g., EPS Beads - Standard'),
            FormField('description', 'Description', 'textarea'),
            FormField('category', 'Category', 'select', required=True, 
                     options=['Raw Material', 'Finished Good', 'Consumable', 'Packaging']),
            FormField('unit_of_measure', 'Unit of Measure', 'select', required=True,
                     options=['EA', 'LB', 'KG', 'FT', 'M', 'GAL', 'L']),
            FormField('weight_per_unit', 'Weight per Unit (lbs)', 'number', min_value=0, decimals=4),
            FormField('dimensions', 'Dimensions', 'text', placeholder='e.g., 24x24x96'),
            FormField('reorder_point', 'Reorder Point', 'number', min_value=0, decimals=4),
            FormField('max_stock_level', 'Max Stock Level', 'number', min_value=0, decimals=4),
            FormField('preferred_supplier', 'Preferred Supplier', 'text'),
            FormField('storage_location', 'Storage Location', 'text', placeholder='e.g., Aisle 1, Rack 2'),
            FormField('standard_cost', 'Standard Cost', 'number', min_value=0, decimals=4),
            FormField('average_cost', 'Average Cost', 'number', min_value=0, decimals=4, default_value=0),
            FormField('last_cost', 'Last Cost', 'number', min_value=0, decimals=4),
            FormField('expansion_ratio', 'Expansion Ratio', 'number', min_value=0, decimals=4),
            FormField('density_target', 'Density Target (lb/ft³)', 'number', min_value=0, decimals=4),
            FormField('mold_id', 'Mold ID', 'text'),
            FormField('notes', 'Notes', 'textarea'),
        ]
        
        title = "Edit Material" if material_data else "New Material"
        super().__init__(title, fields, parent)
        
        # Set existing data if editing
        if material_data:
            self.set_form_data(material_data)
    
    def get_material_data(self) -> Dict[str, Any]:
        """Get material-specific form data."""
        data = self.get_form_data()
        
        # Convert numeric fields appropriately
        numeric_fields = ['weight_per_unit', 'reorder_point', 'max_stock_level', 
                         'standard_cost', 'average_cost', 'last_cost', 
                         'expansion_ratio', 'density_target']
        
        for field in numeric_fields:
            if field in data and data[field] is not None:
                try:
                    data[field] = float(data[field])
                except (ValueError, TypeError):
                    data[field] = None
        
        return data
