"""
Batch Tracking view for XPanda ERP-Lite.
Handles lot traceability and material chain tracking.
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
    QFormLayout, QCheckBox, QProgressBar, QSplitter,
    QTreeWidget, QTreeWidgetItem, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete
from modules.shop_floor.controllers.shop_floor_controller import ShopFloorController

logger = logging.getLogger(__name__)


class BatchTrackingView(QWidget):
    """Batch tracking view for lot traceability and material chain tracking."""
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        self.controller = ShopFloorController(db_manager)
        
        # UI components
        self.batch_table: Optional[DataTableWithFilter] = None
        self.batch_tree: Optional[QTreeWidget] = None
        self.traceability_tree: Optional[QTreeWidget] = None
        
        # Data
        self.batch_type_options = []
        self.station_options = []
        self.current_batch_id: Optional[int] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()
        
        logger.debug("Batch tracking view initialized")
    
    def setup_ui(self) -> None:
        """Create batch tracking UI layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self.setup_header(main_layout)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.setProperty("class", "tab-widget")
        
        # Batch management tab
        batch_tab = self.create_batch_management_tab()
        self.tab_widget.addTab(batch_tab, "Batch Management")
        
        # Traceability tab
        traceability_tab = self.create_traceability_tab()
        self.tab_widget.addTab(traceability_tab, "Traceability")
        
        # Statistics tab
        statistics_tab = self.create_statistics_tab()
        self.tab_widget.addTab(statistics_tab, "Statistics")
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_header(self, parent_layout) -> None:
        """Create view header."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Batch Tracking")
        title.setProperty("class", "page-header")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Action buttons
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("Export")
        export_btn.setProperty("class", "accent")
        export_btn.clicked.connect(self.export_batch_data)
        header_layout.addWidget(export_btn)
        
        parent_layout.addWidget(header_widget)
    
    def create_batch_management_tab(self) -> QWidget:
        """Create batch management tab."""
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setSpacing(20)
        
        # Left side - Batch creation form
        form_widget = self.create_batch_form()
        tab_layout.addWidget(form_widget)
        
        # Right side - Batch list
        list_widget = self.create_batch_list()
        tab_layout.addWidget(list_widget)
        
        # Set splitter sizes (40% form, 60% list)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(form_widget)
        splitter.addWidget(list_widget)
        splitter.setSizes([400, 600])
        
        tab_layout.addWidget(splitter)
        
        return tab_widget
    
    def create_batch_form(self) -> QWidget:
        """Create batch creation form."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
        # Batch creation form
        form_frame = QFrame()
        form_frame.setProperty("class", "form-section")
        form_frame_layout = QVBoxLayout(form_frame)
        
        # Title
        form_title = QLabel("Create New Batch")
        form_title.setProperty("class", "section-header")
        form_frame_layout.addWidget(form_title)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_group.setProperty("class", "form-group")
        basic_layout = QFormLayout(basic_group)
        
        # Batch type
        self.batch_type_combo = QComboBox()
        self.batch_type_combo.setProperty("class", "form-select")
        basic_layout.addRow("Batch Type *:", self.batch_type_combo)
        
        # Station
        self.station_combo = QComboBox()
        self.station_combo.setProperty("class", "form-select")
        basic_layout.addRow("Station:", self.station_combo)
        
        # Work order
        self.work_order_input = QLineEdit()
        self.work_order_input.setPlaceholderText("Work order number (optional)")
        self.work_order_input.setProperty("class", "form-input")
        basic_layout.addRow("Work Order:", self.work_order_input)
        
        form_frame_layout.addWidget(basic_group)
        
        # Material information
        material_group = QGroupBox("Material Information")
        material_group.setProperty("class", "form-group")
        material_layout = QFormLayout(material_group)
        
        # Raw material lot
        self.raw_material_lot_input = QLineEdit()
        self.raw_material_lot_input.setPlaceholderText("Raw material lot number")
        self.raw_material_lot_input.setProperty("class", "form-input")
        material_layout.addRow("Raw Material Lot:", self.raw_material_lot_input)
        
        # Input batch (for chaining)
        self.input_batch_combo = QComboBox()
        self.input_batch_combo.setProperty("class", "form-select")
        material_layout.addRow("Input Batch:", self.input_batch_combo)
        
        # Input quantity
        self.input_quantity_spin = QDoubleSpinBox()
        self.input_quantity_spin.setRange(0, 999999)
        self.input_quantity_spin.setDecimals(2)
        self.input_quantity_spin.setProperty("class", "form-input")
        material_layout.addRow("Input Quantity:", self.input_quantity_spin)
        
        form_frame_layout.addWidget(material_group)
        
        # Operator information
        operator_group = QGroupBox("Operator Information")
        operator_group.setProperty("class", "form-group")
        operator_layout = QFormLayout(operator_group)
        
        self.operator_input = QLineEdit()
        self.operator_input.setPlaceholderText("Operator name/ID")
        self.operator_input.setProperty("class", "form-input")
        operator_layout.addRow("Operator *:", self.operator_input)
        
        form_frame_layout.addWidget(operator_group)
        
        # Process parameters
        params_group = QGroupBox("Process Parameters")
        params_group.setProperty("class", "form-group")
        params_layout = QVBoxLayout(params_group)
        
        self.parameters_input = QPlainTextEdit()
        self.parameters_input.setPlaceholderText("Enter process parameters (JSON format if needed)...")
        self.parameters_input.setMaximumHeight(100)
        self.parameters_input.setProperty("class", "form-input")
        params_layout.addWidget(self.parameters_input)
        
        form_frame_layout.addWidget(params_group)
        
        # Notes
        notes_group = QGroupBox("Notes")
        notes_group.setProperty("class", "form-group")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any notes...")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setProperty("class", "form-input")
        notes_layout.addWidget(self.notes_input)
        
        form_frame_layout.addWidget(notes_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.create_batch_btn = QPushButton("Create Batch")
        self.create_batch_btn.setProperty("class", "primary")
        self.create_batch_btn.clicked.connect(self.create_batch)
        button_layout.addWidget(self.create_batch_btn)
        
        self.complete_batch_btn = QPushButton("Complete Batch")
        self.complete_batch_btn.setProperty("class", "accent")
        self.complete_batch_btn.clicked.connect(self.complete_batch)
        self.complete_batch_btn.setEnabled(False)
        button_layout.addWidget(self.complete_batch_btn)
        
        self.clear_form_btn = QPushButton("Clear Form")
        self.clear_form_btn.setProperty("class", "secondary")
        self.clear_form_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_form_btn)
        
        form_frame_layout.addLayout(button_layout)
        
        form_layout.addWidget(form_frame)
        
        # Batch completion section
        completion_frame = QFrame()
        completion_frame.setProperty("class", "form-section")
        completion_frame_layout = QVBoxLayout(completion_frame)
        
        completion_title = QLabel("Complete Batch")
        completion_title.setProperty("class", "section-header")
        completion_frame_layout.addWidget(completion_title)
        
        completion_form = QFormLayout()
        
        self.output_quantity_spin = QDoubleSpinBox()
        self.output_quantity_spin.setRange(0, 999999)
        self.output_quantity_spin.setDecimals(2)
        self.output_quantity_spin.setProperty("class", "form-input")
        completion_form.addRow("Output Quantity *:", self.output_quantity_spin)
        
        self.scrap_quantity_spin = QDoubleSpinBox()
        self.scrap_quantity_spin.setRange(0, 999999)
        self.scrap_quantity_spin.setDecimals(2)
        self.scrap_quantity_spin.setValue(0)
        self.scrap_quantity_spin.setProperty("class", "form-input")
        completion_form.addRow("Scrap Quantity:", self.scrap_quantity_spin)
        
        self.quality_notes_input = QTextEdit()
        self.quality_notes_input.setPlaceholderText("Quality notes...")
        self.quality_notes_input.setMaximumHeight(60)
        self.quality_notes_input.setProperty("class", "form-input")
        completion_form.addRow("Quality Notes:", self.quality_notes_input)
        
        completion_frame_layout.addLayout(completion_form)
        
        form_layout.addWidget(completion_frame)
        
        form_layout.addStretch()
        
        return form_widget
    
    def create_batch_list(self) -> QWidget:
        """Create batch list widget."""
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setSpacing(15)
        
        # List frame
        list_frame = QFrame()
        list_frame.setProperty("class", "form-section")
        list_frame_layout = QVBoxLayout(list_frame)
        
        # Title and filters
        header_layout = QHBoxLayout()
        
        list_title = QLabel("Active Batches")
        list_title.setProperty("class", "section-header")
        header_layout.addWidget(list_title)
        
        header_layout.addStretch()
        
        # Filter options
        self.batch_filter_combo = QComboBox()
        self.batch_filter_combo.setProperty("class", "form-select")
        self.batch_filter_combo.addItem("All Batches", "")
        self.batch_filter_combo.addItem("Active", "active")
        self.batch_filter_combo.addItem("Completed", "completed")
        self.batch_filter_combo.currentTextChanged.connect(self.filter_batches)
        header_layout.addWidget(self.batch_filter_combo)
        
        list_frame_layout.addLayout(header_layout)
        
        # Batch table
        self.batch_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'batch_number', 'title': 'Batch Number', 'width': 150},
            {'key': 'batch_type', 'title': 'Type', 'width': 100},
            {'key': 'start_time', 'title': 'Start Time', 'width': 150},
            {'key': 'operator_name', 'title': 'Operator', 'width': 120},
            {'key': 'station_id', 'title': 'Station', 'width': 100},
            {'key': 'input_quantity', 'title': 'Input', 'width': 80},
            {'key': 'output_quantity', 'title': 'Output', 'width': 80},
            {'key': 'status', 'title': 'Status', 'width': 100}
        ]
        
        self.batch_table.set_columns(columns)
        list_frame_layout.addWidget(self.batch_table)
        
        list_layout.addWidget(list_frame)
        
        return list_widget
    
    def create_traceability_tab(self) -> QWidget:
        """Create traceability tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(15)
        
        # Traceability search
        search_frame = QFrame()
        search_frame.setProperty("class", "form-section")
        search_layout = QHBoxLayout(search_frame)
        
        search_label = QLabel("Trace Material Lot:")
        search_label.setProperty("class", "subheader")
        search_layout.addWidget(search_label)
        
        self.trace_lot_input = QLineEdit()
        self.trace_lot_input.setPlaceholderText("Enter lot number to trace")
        self.trace_lot_input.setProperty("class", "form-input")
        search_layout.addWidget(self.trace_lot_input)
        
        self.trace_btn = QPushButton("Trace")
        self.trace_btn.setProperty("class", "primary")
        self.trace_btn.clicked.connect(self.trace_material)
        search_layout.addWidget(self.trace_btn)
        
        search_layout.addStretch()
        
        tab_layout.addWidget(search_frame)
        
        # Traceability results
        results_frame = QFrame()
        results_frame.setProperty("class", "form-section")
        results_layout = QVBoxLayout(results_frame)
        
        results_title = QLabel("Traceability Results")
        results_title.setProperty("class", "section-header")
        results_layout.addWidget(results_title)
        
        # Traceability tree
        self.traceability_tree = QTreeWidget()
        self.traceability_tree.setHeaderLabels(["Batch Number", "Type", "Operator", "Date", "Quantity"])
        self.traceability_tree.setProperty("class", "data-tree")
        results_layout.addWidget(self.traceability_tree)
        
        tab_layout.addWidget(results_frame)
        
        return tab_widget
    
    def create_statistics_tab(self) -> QWidget:
        """Create statistics tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(15)
        
        # Statistics frame
        stats_frame = QFrame()
        stats_frame.setProperty("class", "form-section")
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_title = QLabel("Batch Statistics")
        stats_title.setProperty("class", "section-header")
        stats_layout.addWidget(stats_title)
        
        # Date range selection
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("Date Range:"))
        
        self.start_date_input = QLineEdit()
        self.start_date_input.setPlaceholderText("Start date (YYYY-MM-DD)")
        self.start_date_input.setProperty("class", "form-input")
        date_layout.addWidget(self.start_date_input)
        
        date_layout.addWidget(QLabel("to"))
        
        self.end_date_input = QLineEdit()
        self.end_date_input.setPlaceholderText("End date (YYYY-MM-DD)")
        self.end_date_input.setProperty("class", "form-input")
        date_layout.addWidget(self.end_date_input)
        
        self.calculate_stats_btn = QPushButton("Calculate")
        self.calculate_stats_btn.setProperty("class", "primary")
        self.calculate_stats_btn.clicked.connect(self.calculate_statistics)
        date_layout.addWidget(self.calculate_stats_btn)
        
        date_layout.addStretch()
        
        stats_layout.addLayout(date_layout)
        
        # Statistics display
        self.stats_display = QPlainTextEdit()
        self.stats_display.setReadOnly(True)
        self.stats_display.setProperty("class", "form-output")
        self.stats_display.setMaximumHeight(400)
        stats_layout.addWidget(self.stats_display)
        
        tab_layout.addWidget(stats_frame)
        
        return tab_widget
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Setup callbacks
        self.controller.register_data_changed_callback(self.on_data_changed)
        self.controller.register_status_message_callback(self.on_status_message)
        
        # Batch table selection
        if self.batch_table:
            self.batch_table.row_selected.connect(self.on_batch_selected)
    
    def load_initial_data(self) -> None:
        """Load initial data."""
        try:
            # Load batch type options
            self.batch_type_options = self.controller.get_batch_type_options()
            self.batch_type_combo.clear()
            self.batch_type_combo.addItem("Select Batch Type...", "")
            for option in self.batch_type_options:
                self.batch_type_combo.addItem(option['label'], option['value'])
            
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
            
            # Load active batches
            self.load_active_batches()
            
            # Set default date range for statistics
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            self.start_date_input.setText(week_ago.strftime('%Y-%m-%d'))
            self.end_date_input.setText(today.strftime('%Y-%m-%d'))
            
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
    
    def load_active_batches(self) -> None:
        """Load active batches."""
        try:
            active_batches = self.controller.get_active_batches()
            
            batch_data = []
            for batch in active_batches:
                batch_data.append({
                    'id': batch.id,
                    'batch_number': batch.batch_number,
                    'batch_type': batch.batch_type,
                    'start_time': batch.start_time.strftime('%Y-%m-%d %H:%M'),
                    'operator_name': batch.operator_name,
                    'station_id': batch.station_id or '',
                    'input_quantity': float(batch.input_quantity or 0),
                    'output_quantity': float(batch.output_quantity or 0),
                    'status': batch.status
                })
            
            if self.batch_table:
                self.batch_table.set_data(batch_data)
            
        except Exception as e:
            logger.error(f"Error loading active batches: {e}")
    
    def create_batch(self) -> None:
        """Create a new production batch."""
        try:
            # Validate required fields
            batch_type = self.batch_type_combo.currentData()
            if not batch_type:
                show_error("Please select a batch type")
                return
            
            operator_name = self.operator_input.text().strip()
            if not operator_name:
                show_error("Please enter operator name")
                return
            
            # Gather form data
            station_id = self.station_combo.currentData() or None
            raw_material_lot = self.raw_material_lot_input.text().strip() or None
            input_batch_id = None  # Would populate from combo
            work_order_id = None
            work_order_text = self.work_order_input.text().strip()
            if work_order_text:
                try:
                    work_order_id = int(work_order_text)
                except ValueError:
                    show_error("Invalid work order number")
                    return
            
            input_quantity = self.input_quantity_spin.value() if self.input_quantity_spin.value() > 0 else None
            parameters = self.parameters_input.toPlainText().strip() or None
            notes = self.notes_input.toPlainText().strip() or None
            
            # Create batch
            batch = self.controller.create_production_batch(
                batch_type=batch_type,
                operator_id=operator_name,  # Would use actual ID
                operator_name=operator_name,
                station_id=station_id,
                raw_material_lot=raw_material_lot,
                input_batch_id=input_batch_id,
                work_order_id=work_order_id,
                parameters={'parameters': parameters} if parameters else None,
                input_quantity=Decimal(str(input_quantity)) if input_quantity else None,
                notes=notes
            )
            
            # Store current batch ID for completion
            self.current_batch_id = batch.id
            self.complete_batch_btn.setEnabled(True)
            
            # Clear form
            self.clear_form()
            
            # Refresh batch list
            self.load_active_batches()
            
        except Exception as e:
            logger.error(f"Error creating batch: {e}")
            show_error(f"Error creating batch: {str(e)}")
    
    def complete_batch(self) -> None:
        """Complete the current batch."""
        try:
            if not self.current_batch_id:
                show_error("No batch selected for completion")
                return
            
            output_quantity = self.output_quantity_spin.value()
            if output_quantity <= 0:
                show_error("Output quantity must be greater than 0")
                return
            
            scrap_quantity = self.scrap_quantity_spin.value()
            quality_notes = self.quality_notes_input.toPlainText().strip() or None
            
            # Complete batch
            self.controller.complete_batch(
                batch_id=self.current_batch_id,
                output_quantity=output_quantity,
                scrap_quantity=scrap_quantity if scrap_quantity > 0 else None,
                quality_notes=quality_notes
            )
            
            # Reset completion form
            self.output_quantity_spin.setValue(0)
            self.scrap_quantity_spin.setValue(0)
            self.quality_notes_input.clear()
            
            # Disable complete button
            self.complete_batch_btn.setEnabled(False)
            self.current_batch_id = None
            
            # Refresh batch list
            self.load_active_batches()
            
        except Exception as e:
            logger.error(f"Error completing batch: {e}")
            show_error(f"Error completing batch: {str(e)}")
    
    def clear_form(self) -> None:
        """Clear the batch creation form."""
        self.batch_type_combo.setCurrentIndex(0)
        self.station_combo.setCurrentIndex(0)
        self.work_order_input.clear()
        self.raw_material_lot_input.clear()
        self.input_batch_combo.setCurrentIndex(0)
        self.input_quantity_spin.setValue(0)
        self.operator_input.clear()
        self.parameters_input.clear()
        self.notes_input.clear()
    
    def on_batch_selected(self, row: int) -> None:
        """Handle batch selection in table."""
        try:
            # Get selected batch data
            if self.batch_table and self.batch_table.data_table.rowCount() > row:
                batch_id = self.batch_table.data_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                self.current_batch_id = batch_id
                self.complete_batch_btn.setEnabled(True)
                
                # Load batch details for completion form
                # In a real implementation, would populate form with batch data
                
        except Exception as e:
            logger.error(f"Error selecting batch: {e}")
    
    def trace_material(self) -> None:
        """Trace material lot through production chain."""
        try:
            lot_number = self.trace_lot_input.text().strip()
            if not lot_number:
                show_error("Please enter a lot number to trace")
                return
            
            # Get traceability data
            trace_results = self.controller.trace_material_to_outputs(lot_number)
            
            # Populate traceability tree
            self.traceability_tree.clear()
            
            for batch_result in trace_results:
                # Create batch item
                batch_item = QTreeWidgetItem(self.traceability_tree)
                batch_item.setText(0, batch_result['batch_number'])
                batch_item.setText(1, batch_result['batch_type'])
                batch_item.setText(2, batch_result['operator_name'])
                batch_item.setText(3, batch_result['start_time'].strftime('%Y-%m-%d %H:%M'))
                batch_item.setText(4, str(batch_result.get('output_quantity', 0)))
                
                # Add outputs as children
                for output in batch_result['outputs']:
                    output_item = QTreeWidgetItem(batch_item)
                    output_item.setText(0, f"Output: {output['lot_number'] or 'N/A'}")
                    output_item.setText(1, output['output_type'])
                    output_item.setText(2, output['operator_name'])
                    output_item.setText(3, output['timestamp'].strftime('%Y-%m-%d %H:%M'))
                    output_item.setText(4, str(output['quantity_produced']))
            
            # Expand all items
            self.traceability_tree.expandAll()
            
        except Exception as e:
            logger.error(f"Error tracing material: {e}")
            show_error(f"Error tracing material: {str(e)}")
    
    def calculate_statistics(self) -> None:
        """Calculate batch statistics."""
        try:
            start_date_str = self.start_date_input.text().strip()
            end_date_str = self.end_date_input.text().strip()
            
            if not start_date_str or not end_date_str:
                show_error("Please enter both start and end dates")
                return
            
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # Make end_date inclusive
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                show_error("Invalid date format. Use YYYY-MM-DD")
                return
            
            # Get batch statistics
            stats = self.controller.batch_tracking_service.get_batch_statistics(start_date, end_date)
            
            # Format statistics display
            stats_text = f"Batch Statistics for {start_date_str} to {end_date_str}\n"
            stats_text += "=" * 60 + "\n\n"
            
            stats_text += f"Total Batches: {stats['total_batches']}\n"
            stats_text += f"Completed Batches: {stats['completed_batches']}\n"
            stats_text += f"Active Batches: {stats['active_batches']}\n"
            stats_text += f"Average Duration: {stats['average_duration_minutes']:.1f} minutes\n\n"
            
            stats_text += f"Total Input Quantity: {stats['total_input_quantity']:.2f}\n"
            stats_text += f"Total Output Quantity: {stats['total_output_quantity']:.2f}\n"
            stats_text += f"Total Scrap Quantity: {stats['total_scrap_quantity']:.2f}\n"
            stats_text += f"Overall Yield: {stats['overall_yield_percentage']:.2f}%\n\n"
            
            stats_text += "Breakdown by Batch Type:\n"
            stats_text += "-" * 30 + "\n"
            for batch_type, type_stats in stats['type_breakdown'].items():
                stats_text += f"{batch_type}:\n"
                stats_text += f"  Count: {type_stats['count']}\n"
                stats_text += f"  Completed: {type_stats['completed']}\n"
                stats_text += f"  Input: {type_stats['input_quantity']:.2f}\n"
                stats_text += f"  Output: {type_stats['output_quantity']:.2f}\n"
                stats_text += f"  Scrap: {type_stats['scrap_quantity']:.2f}\n\n"
            
            self.stats_display.setPlainText(stats_text)
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            show_error(f"Error calculating statistics: {str(e)}")
    
    def filter_batches(self) -> None:
        """Filter batches by status."""
        try:
            status_filter = self.batch_filter_combo.currentData()
            
            # Reload batches with filter
            # In a real implementation, would apply filter to data loading
            self.load_active_batches()
            
        except Exception as e:
            logger.error(f"Error filtering batches: {e}")
    
    def refresh_data(self) -> None:
        """Refresh all data."""
        try:
            self.load_active_batches()
            self.load_initial_data()
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
    
    def export_batch_data(self) -> None:
        """Export batch data."""
        try:
            # Placeholder for export functionality
            show_info("Export functionality would be implemented here")
        except Exception as e:
            logger.error(f"Error exporting batch data: {e}")
            show_error(f"Error exporting data: {str(e)}")
    
    def on_data_changed(self) -> None:
        """Handle data change notifications."""
        self.load_active_batches()
    
    def on_status_message(self, message: str, timeout: int) -> None:
        """Handle status message notifications."""
        logger.info(f"Status: {message}")
