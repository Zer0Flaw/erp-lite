"""
Production Recording view for XPanda ERP-Lite.
Handles production output logging and yield tracking.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSizePolicy,
    QComboBox, QLineEdit, QTextEdit, QGridLayout,
    QGroupBox, QSpacerItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QDoubleSpinBox, QTabWidget,
    QFormLayout, QCheckBox, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete
from modules.shop_floor.controllers.shop_floor_controller import ShopFloorController

logger = logging.getLogger(__name__)


class ProductionRecordingView(QWidget):
    """Production recording view for logging output and tracking yields."""
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        self.controller = ShopFloorController(db_manager)
        
        # UI components
        self.production_table: Optional[DataTableWithFilter] = None
        self.output_type_combo: Optional[QComboBox] = None
        self.work_order_combo: Optional[QComboBox] = None
        self.station_combo: Optional[QComboBox] = None
        
        # Data
        self.output_type_options = []
        self.work_orders = []
        self.stations = []
        self.current_work_order_id: Optional[int] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()
        
        logger.debug("Production recording view initialized")
    
    def setup_ui(self) -> None:
        """Create production recording UI layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self.setup_header(main_layout)
        
        # Content splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Production form
        form_widget = self.create_production_form()
        content_splitter.addWidget(form_widget)
        
        # Right side - Production history
        history_widget = self.create_history_widget()
        content_splitter.addWidget(history_widget)
        
        # Set splitter sizes (40% form, 60% history)
        content_splitter.setSizes([400, 600])
        
        main_layout.addWidget(content_splitter)
    
    def setup_header(self, parent_layout) -> None:
        """Create view header."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Production Recording")
        title.setProperty("class", "page-header")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Action buttons
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.load_production_history)
        header_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("Export")
        export_btn.setProperty("class", "accent")
        export_btn.clicked.connect(self.export_production_data)
        header_layout.addWidget(export_btn)
        
        parent_layout.addWidget(header_widget)
    
    def create_production_form(self) -> QWidget:
        """Create production input form."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
        # Production input form
        form_frame = QFrame()
        form_frame.setProperty("class", "form-section")
        form_frame_layout = QVBoxLayout(form_frame)
        
        # Title
        form_title = QLabel("Record Production Output")
        form_title.setProperty("class", "section-header")
        form_frame_layout.addWidget(form_title)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_group.setProperty("class", "form-group")
        basic_layout = QFormLayout(basic_group)
        
        # Work order
        self.work_order_combo = QComboBox()
        self.work_order_combo.setProperty("class", "form-select")
        basic_layout.addRow("Work Order *:", self.work_order_combo)
        
        # Output type
        self.output_type_combo = QComboBox()
        self.output_type_combo.setProperty("class", "form-select")
        self.output_type_combo.currentTextChanged.connect(self.on_output_type_changed)
        basic_layout.addRow("Output Type *:", self.output_type_combo)
        
        # Station
        self.station_combo = QComboBox()
        self.station_combo.setProperty("class", "form-select")
        basic_layout.addRow("Station:", self.station_combo)
        
        form_frame_layout.addWidget(basic_group)
        
        # Quantity information
        quantity_group = QGroupBox("Quantity Information")
        quantity_group.setProperty("class", "form-group")
        quantity_layout = QFormLayout(quantity_group)
        
        self.quantity_produced_spin = QDoubleSpinBox()
        self.quantity_produced_spin.setRange(0, 999999)
        self.quantity_produced_spin.setDecimals(2)
        self.quantity_produced_spin.setProperty("class", "form-input")
        quantity_layout.addRow("Quantity Produced *:", self.quantity_produced_spin)
        
        self.quantity_scrapped_spin = QDoubleSpinBox()
        self.quantity_scrapped_spin.setRange(0, 999999)
        self.quantity_scrapped_spin.setDecimals(2)
        self.quantity_scrapped_spin.setValue(0)
        self.quantity_scrapped_spin.setProperty("class", "form-input")
        quantity_layout.addRow("Quantity Scrapped:", self.quantity_scrapped_spin)
        
        self.theoretical_yield_spin = QDoubleSpinBox()
        self.theoretical_yield_spin.setRange(0, 999999)
        self.theoretical_yield_spin.setDecimals(2)
        self.theoretical_yield_spin.setProperty("class", "form-input")
        quantity_layout.addRow("Theoretical Yield:", self.theoretical_yield_spin)
        
        form_frame_layout.addWidget(quantity_group)
        
        # Foam block specific fields (shown when foam block is selected)
        self.foam_block_group = QGroupBox("Foam Block Specifications")
        self.foam_block_group.setProperty("class", "form-group")
        self.foam_block_group.setVisible(False)
        
        foam_layout = QGridLayout(self.foam_block_group)
        
        foam_layout.addWidget(QLabel("Length (in):"), 0, 0)
        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0, 999)
        self.length_spin.setDecimals(2)
        self.length_spin.setProperty("class", "form-input")
        foam_layout.addWidget(self.length_spin, 0, 1)
        
        foam_layout.addWidget(QLabel("Width (in):"), 0, 2)
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0, 999)
        self.width_spin.setDecimals(2)
        self.width_spin.setProperty("class", "form-input")
        foam_layout.addWidget(self.width_spin, 0, 3)
        
        foam_layout.addWidget(QLabel("Height (in):"), 1, 0)
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0, 999)
        self.height_spin.setDecimals(2)
        self.height_spin.setProperty("class", "form-input")
        foam_layout.addWidget(self.height_spin, 1, 1)
        
        foam_layout.addWidget(QLabel("Density (lb/ft³):"), 1, 2)
        self.density_spin = QDoubleSpinBox()
        self.density_spin.setRange(0, 100)
        self.density_spin.setDecimals(2)
        self.density_spin.setProperty("class", "form-input")
        foam_layout.addWidget(self.density_spin, 1, 3)
        
        form_frame_layout.addWidget(self.foam_block_group)
        
        # Traceability fields
        traceability_group = QGroupBox("Traceability")
        traceability_group.setProperty("class", "form-group")
        traceability_layout = QFormLayout(traceability_group)
        
        self.lot_number_input = QLineEdit()
        self.lot_number_input.setPlaceholderText("Auto-generated if empty")
        self.lot_number_input.setProperty("class", "form-input")
        traceability_layout.addRow("Lot Number:", self.lot_number_input)
        
        self.bead_batch_input = QLineEdit()
        self.bead_batch_input.setPlaceholderText("Bead batch number")
        self.bead_batch_input.setProperty("class", "form-input")
        traceability_layout.addRow("Bead Batch:", self.bead_batch_input)
        
        self.bead_lot_input = QLineEdit()
        self.bead_lot_input.setPlaceholderText("Raw bead lot number")
        self.bead_lot_input.setProperty("class", "form-input")
        traceability_layout.addRow("Bead Lot:", self.bead_lot_input)
        
        self.expansion_batch_input = QLineEdit()
        self.expansion_batch_input.setPlaceholderText("Expansion batch number")
        self.expansion_batch_input.setProperty("class", "form-input")
        traceability_layout.addRow("Expansion Batch:", self.expansion_batch_input)
        
        self.mold_id_input = QLineEdit()
        self.mold_id_input.setPlaceholderText("Mold identifier")
        self.mold_id_input.setProperty("class", "form-input")
        traceability_layout.addRow("Mold ID:", self.mold_id_input)
        
        form_frame_layout.addWidget(traceability_group)
        
        # Operator and notes
        operator_group = QGroupBox("Additional Information")
        operator_group.setProperty("class", "form-group")
        operator_layout = QFormLayout(operator_group)
        
        self.operator_input = QLineEdit()
        self.operator_input.setPlaceholderText("Operator name/ID")
        self.operator_input.setProperty("class", "form-input")
        operator_layout.addRow("Operator *:", self.operator_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any notes...")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setProperty("class", "form-input")
        operator_layout.addRow("Notes:", self.notes_input)
        
        form_frame_layout.addWidget(operator_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.record_btn = QPushButton("Record Production")
        self.record_btn.setProperty("class", "primary")
        self.record_btn.clicked.connect(self.record_production)
        button_layout.addWidget(self.record_btn)
        
        self.clear_btn = QPushButton("Clear Form")
        self.clear_btn.setProperty("class", "secondary")
        self.clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_btn)
        
        form_frame_layout.addLayout(button_layout)
        
        form_layout.addWidget(form_frame)
        
        # Yield summary (shown after recording)
        self.yield_summary_group = QGroupBox("Yield Summary")
        self.yield_summary_group.setProperty("class", "form-section")
        self.yield_summary_group.setVisible(False)
        
        yield_layout = QVBoxLayout(self.yield_summary_group)
        
        self.yield_label = QLabel()
        self.yield_label.setProperty("class", "card-value")
        yield_layout.addWidget(self.yield_label)
        
        self.yield_progress = QProgressBar()
        self.yield_progress.setProperty("class", "progress-bar")
        yield_layout.addWidget(self.yield_progress)
        
        form_layout.addWidget(self.yield_summary_group)
        
        form_layout.addStretch()
        
        return form_widget
    
    def create_history_widget(self) -> QWidget:
        """Create production history widget."""
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setSpacing(15)
        
        # History frame
        history_frame = QFrame()
        history_frame.setProperty("class", "form-section")
        history_frame_layout = QVBoxLayout(history_frame)
        
        # Title
        history_title = QLabel("Production History")
        history_title.setProperty("class", "section-header")
        history_frame_layout.addWidget(history_title)
        
        # Production table
        self.production_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'timestamp', 'title': 'Date/Time', 'width': 150},
            {'key': 'work_order_id', 'title': 'Work Order', 'width': 80},
            {'key': 'output_type', 'title': 'Type', 'width': 120},
            {'key': 'quantity_produced', 'title': 'Produced', 'width': 100},
            {'key': 'quantity_scrapped', 'title': 'Scrapped', 'width': 100},
            {'key': 'yield_percentage', 'title': 'Yield %', 'width': 80},
            {'key': 'operator_name', 'title': 'Operator', 'width': 120},
            {'key': 'lot_number', 'title': 'Lot #', 'width': 100}
        ]
        
        self.production_table.set_columns(columns)
        history_frame_layout.addWidget(self.production_table)
        
        history_layout.addWidget(history_frame)
        
        return history_widget
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Setup callbacks
        self.controller.register_data_changed_callback(self.on_data_changed)
        self.controller.register_status_message_callback(self.on_status_message)
        
        # Work order selection
        self.work_order_combo.currentIndexChanged.connect(self.on_work_order_changed)
    
    def load_initial_data(self) -> None:
        """Load initial data."""
        try:
            # Load output type options
            self.output_type_options = self.controller.get_output_type_options()
            self.output_type_combo.clear()
            self.output_type_combo.addItem("Select Output Type...", "")
            for option in self.output_type_options:
                self.output_type_combo.addItem(option['label'], option['value'])
            
            # Load available stations
            try:
                available_stations = self.controller.get_available_stations()
                self.station_combo.clear()
                self.station_combo.addItem("Select Station...", "")
                for station in available_stations:
                    self.station_combo.addItem(f"{station.station_id} - {station.name}", station.station_id)
            except Exception as e:
                logger.warning(f"Could not load stations: {e}")
                self.station_combo.clear()
                self.station_combo.addItem("No stations available", "")
            
            # Load work orders (placeholder - would load from database)
            self.load_work_orders()
            
            # Load production history
            self.load_production_history()
            
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
    
    def load_work_orders(self) -> None:
        """Load work orders."""
        try:
            # Placeholder work orders - in real implementation would load from database
            self.work_orders = [
                {'id': 1, 'number': 'WO-001', 'description': 'EPS Block Production'},
                {'id': 2, 'number': 'WO-002', 'description': 'Custom Fabrication'},
                {'id': 3, 'number': 'WO-003', 'description': 'Large Block Run'}
            ]
            
            self.work_order_combo.clear()
            self.work_order_combo.addItem("Select Work Order...", "")
            for wo in self.work_orders:
                self.work_order_combo.addItem(f"{wo['number']} - {wo['description']}", wo['id'])
                
        except Exception as e:
            logger.error(f"Error loading work orders: {e}")
    
    def load_production_history(self) -> None:
        """Load production history."""
        try:
            # Get today's production
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)  # Last 7 days
            
            # Placeholder data - in real implementation would load from database
            history_data = [
                {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'work_order_id': 'WO-001',
                    'output_type': 'Foam Block',
                    'quantity_produced': 25.5,
                    'quantity_scrapped': 1.2,
                    'yield_percentage': 95.3,
                    'operator_name': 'J. Smith',
                    'lot_number': 'EXP-20260417-001'
                },
                {
                    'timestamp': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
                    'work_order_id': 'WO-002',
                    'output_type': 'Fabricated Part',
                    'quantity_produced': 150,
                    'quantity_scrapped': 5,
                    'yield_percentage': 96.7,
                    'operator_name': 'M. Johnson',
                    'lot_number': 'FAB-20260417-001'
                }
            ]
            
            self.production_table.set_data(history_data)
            
        except Exception as e:
            logger.error(f"Error loading production history: {e}")
    
    def on_output_type_changed(self) -> None:
        """Handle output type selection change."""
        output_type = self.output_type_combo.currentData()
        
        # Show/hide foam block specific fields
        is_foam_block = output_type == 'foam_block'
        self.foam_block_group.setVisible(is_foam_block)
        
        # Update field requirements based on output type
        if is_foam_block:
            # For foam blocks, dimensions are typically required
            self.length_spin.setRequired(True)
            self.width_spin.setRequired(True)
            self.height_spin.setRequired(True)
            self.density_spin.setRequired(True)
        else:
            self.length_spin.setRequired(False)
            self.width_spin.setRequired(False)
            self.height_spin.setRequired(False)
            self.density_spin.setRequired(False)
    
    def on_work_order_changed(self) -> None:
        """Handle work order selection change."""
        work_order_id = self.work_order_combo.currentData()
        self.current_work_order_id = work_order_id
        
        # Could auto-fill theoretical yield based on work order
        if work_order_id:
            # Placeholder - would calculate from work order BOM
            self.theoretical_yield_spin.setValue(100.0)
        else:
            self.theoretical_yield_spin.setValue(0.0)
    
    def record_production(self) -> None:
        """Record production output."""
        try:
            # Validate required fields
            work_order_id = self.work_order_combo.currentData()
            if not work_order_id:
                show_error("Please select a work order")
                return
            
            output_type = self.output_type_combo.currentData()
            if not output_type:
                show_error("Please select an output type")
                return
            
            quantity_produced = self.quantity_produced_spin.value()
            if quantity_produced <= 0:
                show_error("Quantity produced must be greater than 0")
                return
            
            operator_name = self.operator_input.text().strip()
            if not operator_name:
                show_error("Please enter operator name")
                return
            
            # Gather form data
            station_id = self.station_combo.currentData() or None
            quantity_scrapped = self.quantity_scrapped_spin.value()
            theoretical_yield = self.theoretical_yield_spin.value() if self.theoretical_yield_spin.value() > 0 else None
            
            # Foam block specific data
            length = self.length_spin.value() if self.foam_block_group.isVisible() else None
            width = self.width_spin.value() if self.foam_block_group.isVisible() else None
            height = self.height_spin.value() if self.foam_block_group.isVisible() else None
            density = self.density_spin.value() if self.foam_block_group.isVisible() else None
            
            # Traceability data
            lot_number = self.lot_number_input.text().strip() or None
            bead_batch = self.bead_batch_input.text().strip() or None
            bead_lot_number = self.bead_lot_input.text().strip() or None
            expansion_batch = self.expansion_batch_input.text().strip() or None
            mold_id = self.mold_id_input.text().strip() or None
            
            notes = self.notes_input.toPlainText().strip() or None
            
            # Record production
            self.controller.record_production_output(
                work_order_id=work_order_id,
                output_type=output_type,
                quantity_produced=quantity_produced,
                operator_id=operator_name,  # Would use actual ID in real system
                operator_name=operator_name,
                station_id=station_id,
                quantity_scrapped=quantity_scrapped if quantity_scrapped > 0 else None,
                theoretical_yield=theoretical_yield,
                length=Decimal(str(length)) if length else None,
                width=Decimal(str(width)) if width else None,
                height=Decimal(str(height)) if height else None,
                density=Decimal(str(density)) if density else None,
                lot_number=lot_number,
                bead_batch=bead_batch,
                bead_lot_number=bead_lot_number,
                expansion_batch=expansion_batch,
                mold_id=mold_id,
                notes=notes
            )
            
            # Show yield summary if theoretical yield was provided
            if theoretical_yield and theoretical_yield > 0:
                actual_yield = quantity_produced - quantity_scrapped
                yield_percentage = (actual_yield / theoretical_yield * 100) if theoretical_yield > 0 else 0
                
                self.yield_label.setText(f"Yield: {actual_yield:.2f} / {theoretical_yield:.2f} ({yield_percentage:.1f}%)")
                self.yield_progress.setValue(int(yield_percentage))
                self.yield_summary_group.setVisible(True)
            
            # Clear form for next entry
            self.clear_form()
            
        except Exception as e:
            logger.error(f"Error recording production: {e}")
            show_error(f"Error recording production: {str(e)}")
    
    def clear_form(self) -> None:
        """Clear the production form."""
        self.work_order_combo.setCurrentIndex(0)
        self.output_type_combo.setCurrentIndex(0)
        self.station_combo.setCurrentIndex(0)
        self.quantity_produced_spin.setValue(0)
        self.quantity_scrapped_spin.setValue(0)
        self.theoretical_yield_spin.setValue(0)
        self.length_spin.setValue(0)
        self.width_spin.setValue(0)
        self.height_spin.setValue(0)
        self.density_spin.setValue(0)
        self.lot_number_input.clear()
        self.bead_batch_input.clear()
        self.bead_lot_input.clear()
        self.expansion_batch_input.clear()
        self.mold_id_input.clear()
        self.operator_input.clear()
        self.notes_input.clear()
        self.yield_summary_group.setVisible(False)
    
    def export_production_data(self) -> None:
        """Export production data."""
        try:
            # Placeholder for export functionality
            show_info("Export functionality would be implemented here")
        except Exception as e:
            logger.error(f"Error exporting production data: {e}")
            show_error(f"Error exporting data: {str(e)}")
    
    def on_data_changed(self) -> None:
        """Handle data change notifications."""
        self.load_production_history()
    
    def on_status_message(self, message: str, timeout: int) -> None:
        """Handle status message notifications."""
        logger.info(f"Status: {message}")
