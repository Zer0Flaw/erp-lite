"""
Station Management view for XPanda ERP-Lite.
Handles production stations and equipment status tracking.
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
    QTreeWidget, QTreeWidgetItem, QPlainTextEdit, QDateEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QPalette, QColor

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete
from modules.shop_floor.controllers.shop_floor_controller import ShopFloorController

logger = logging.getLogger(__name__)


class StationManagementView(QWidget):
    """Station management view for production stations and equipment tracking."""
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        self.controller = ShopFloorController(db_manager)
        
        # UI components
        self.station_table: Optional[DataTableWithFilter] = None
        self.maintenance_table: Optional[DataTableWithFilter] = None
        
        # Data
        self.station_type_options = []
        self.station_status_options = []
        self.current_station_id: Optional[str] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()
        
        logger.debug("Station management view initialized")
    
    def setup_ui(self) -> None:
        """Create station management UI layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self.setup_header(main_layout)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.setProperty("class", "tab-widget")
        
        # Station management tab
        station_tab = self.create_station_management_tab()
        self.tab_widget.addTab(station_tab, "Station Management")
        
        # Maintenance tab
        maintenance_tab = self.create_maintenance_tab()
        self.tab_widget.addTab(maintenance_tab, "Maintenance")
        
        # Utilization tab
        utilization_tab = self.create_utilization_tab()
        self.tab_widget.addTab(utilization_tab, "Utilization")
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_header(self, parent_layout) -> None:
        """Create view header."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Station Management")
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
        export_btn.clicked.connect(self.export_station_data)
        header_layout.addWidget(export_btn)
        
        parent_layout.addWidget(header_widget)
    
    def create_station_management_tab(self) -> QWidget:
        """Create station management tab."""
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setSpacing(20)
        
        # Left side - Station creation/edit form
        form_widget = self.create_station_form()
        tab_layout.addWidget(form_widget)
        
        # Right side - Station list
        list_widget = self.create_station_list()
        tab_layout.addWidget(list_widget)
        
        # Set splitter sizes (40% form, 60% list)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(form_widget)
        splitter.addWidget(list_widget)
        splitter.setSizes([400, 600])
        
        tab_layout.addWidget(splitter)
        
        return tab_widget
    
    def create_station_form(self) -> QWidget:
        """Create station creation/edit form."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
        # Station form
        form_frame = QFrame()
        form_frame.setProperty("class", "form-section")
        form_frame_layout = QVBoxLayout(form_frame)
        
        # Title
        form_title = QLabel("Station Information")
        form_title.setProperty("class", "section-header")
        form_frame_layout.addWidget(form_title)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_group.setProperty("class", "form-group")
        basic_layout = QFormLayout(basic_group)
        
        # Station ID
        self.station_id_input = QLineEdit()
        self.station_id_input.setPlaceholderText("Unique station identifier")
        self.station_id_input.setProperty("class", "form-input")
        basic_layout.addRow("Station ID *:", self.station_id_input)
        
        # Station name
        self.station_name_input = QLineEdit()
        self.station_name_input.setPlaceholderText("Station display name")
        self.station_name_input.setProperty("class", "form-input")
        basic_layout.addRow("Station Name *:", self.station_name_input)
        
        # Station type
        self.station_type_combo = QComboBox()
        self.station_type_combo.setProperty("class", "form-select")
        basic_layout.addRow("Station Type *:", self.station_type_combo)
        
        # Status
        self.station_status_combo = QComboBox()
        self.station_status_combo.setProperty("class", "form-select")
        basic_layout.addRow("Status:", self.station_status_combo)
        
        form_frame_layout.addWidget(basic_group)
        
        # Location and capacity
        location_group = QGroupBox("Location & Capacity")
        location_group.setProperty("class", "form-group")
        location_layout = QFormLayout(location_group)
        
        # Location
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Physical location")
        self.location_input.setProperty("class", "form-input")
        location_layout.addRow("Location:", self.location_input)
        
        # Department
        self.department_input = QLineEdit()
        self.department_input.setPlaceholderText("Department")
        self.department_input.setProperty("class", "form-input")
        location_layout.addRow("Department:", self.department_input)
        
        # Capacity per hour
        self.capacity_spin = QDoubleSpinBox()
        self.capacity_spin.setRange(0, 999999)
        self.capacity_spin.setDecimals(2)
        self.capacity_spin.setProperty("class", "form-input")
        location_layout.addRow("Capacity/Hour:", self.capacity_spin)
        
        form_frame_layout.addWidget(location_group)
        
        # Specifications
        specs_group = QGroupBox("Specifications")
        specs_group.setProperty("class", "form-group")
        specs_layout = QFormLayout(specs_group)
        
        # Max block size
        self.max_block_size_input = QLineEdit()
        self.max_block_size_input.setPlaceholderText("e.g., 24x24x96")
        self.max_block_size_input.setProperty("class", "form-input")
        specs_layout.addRow("Max Block Size:", self.max_block_size_input)
        
        # Temperature range
        self.temp_range_input = QLineEdit()
        self.temp_range_input.setPlaceholderText("e.g., 180-200°F")
        self.temp_range_input.setProperty("class", "form-input")
        specs_layout.addRow("Temperature Range:", self.temp_range_input)
        
        form_frame_layout.addWidget(specs_group)
        
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
        
        self.create_station_btn = QPushButton("Create Station")
        self.create_station_btn.setProperty("class", "primary")
        self.create_station_btn.clicked.connect(self.create_station)
        button_layout.addWidget(self.create_station_btn)
        
        self.update_station_btn = QPushButton("Update Station")
        self.update_station_btn.setProperty("class", "accent")
        self.update_station_btn.clicked.connect(self.update_station)
        self.update_station_btn.setEnabled(False)
        button_layout.addWidget(self.update_station_btn)
        
        self.clear_form_btn = QPushButton("Clear Form")
        self.clear_form_btn.setProperty("class", "secondary")
        self.clear_form_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_form_btn)
        
        form_frame_layout.addLayout(button_layout)
        
        # Work assignment section
        assignment_frame = QFrame()
        assignment_frame.setProperty("class", "form-section")
        assignment_frame_layout = QVBoxLayout(assignment_frame)
        
        assignment_title = QLabel("Work Assignment")
        assignment_title.setProperty("class", "section-header")
        assignment_frame_layout.addWidget(assignment_title)
        
        assignment_form = QFormLayout()
        
        self.work_order_input = QLineEdit()
        self.work_order_input.setPlaceholderText("Work order number")
        self.work_order_input.setProperty("class", "form-input")
        assignment_form.addRow("Work Order:", self.work_order_input)
        
        self.operator_input = QLineEdit()
        self.operator_input.setPlaceholderText("Operator name/ID")
        self.operator_input.setProperty("class", "form-input")
        assignment_form.addRow("Operator:", self.operator_input)
        
        self.assign_work_btn = QPushButton("Assign Work")
        self.assign_work_btn.setProperty("class", "primary")
        self.assign_work_btn.clicked.connect(self.assign_work)
        assignment_form.addRow("", self.assign_work_btn)
        
        self.release_work_btn = QPushButton("Release Work")
        self.release_work_btn.setProperty("class", "danger")
        self.release_work_btn.clicked.connect(self.release_work)
        assignment_form.addRow("", self.release_work_btn)
        
        assignment_frame_layout.addLayout(assignment_form)
        
        form_layout.addWidget(form_frame)
        form_layout.addWidget(assignment_frame)
        
        form_layout.addStretch()
        
        return form_widget
    
    def create_station_list(self) -> QWidget:
        """Create station list widget."""
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setSpacing(15)
        
        # List frame
        list_frame = QFrame()
        list_frame.setProperty("class", "form-section")
        list_frame_layout = QVBoxLayout(list_frame)
        
        # Title and filters
        header_layout = QHBoxLayout()
        
        list_title = QLabel("Station List")
        list_title.setProperty("class", "section-header")
        header_layout.addWidget(list_title)
        
        header_layout.addStretch()
        
        # Filter options
        self.station_filter_combo = QComboBox()
        self.station_filter_combo.setProperty("class", "form-select")
        self.station_filter_combo.addItem("All Stations", "")
        self.station_filter_combo.addItem("Available", "available")
        self.station_filter_combo.addItem("Running", "running")
        self.station_filter_combo.addItem("Maintenance", "maintenance")
        self.station_filter_combo.addItem("Offline", "offline")
        self.station_filter_combo.currentTextChanged.connect(self.filter_stations)
        header_layout.addWidget(self.station_filter_combo)
        
        list_frame_layout.addLayout(header_layout)
        
        # Station table
        self.station_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'station_id', 'title': 'Station ID', 'width': 120},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'station_type', 'title': 'Type', 'width': 120},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'location', 'title': 'Location', 'width': 100},
            {'key': 'current_operator_name', 'title': 'Operator', 'width': 120},
            {'key': 'capacity_per_hour', 'title': 'Capacity/Hr', 'width': 100},
            {'key': 'total_runtime_hours', 'title': 'Runtime', 'width': 80}
        ]
        
        self.station_table.set_columns(columns)
        list_frame_layout.addWidget(self.station_table)
        
        list_layout.addWidget(list_frame)
        
        return list_widget
    
    def create_maintenance_tab(self) -> QWidget:
        """Create maintenance tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(15)
        
        # Maintenance frame
        maintenance_frame = QFrame()
        maintenance_frame.setProperty("class", "form-section")
        maintenance_frame_layout = QVBoxLayout(maintenance_frame)
        
        # Title
        maintenance_title = QLabel("Maintenance Schedule")
        maintenance_title.setProperty("class", "section-header")
        maintenance_frame_layout.addWidget(maintenance_title)
        
        # Maintenance table
        self.maintenance_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'station_id', 'title': 'Station ID', 'width': 120},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'last_maintenance_date', 'title': 'Last Maintenance', 'width': 120},
            {'key': 'next_maintenance_date', 'title': 'Next Maintenance', 'width': 120},
            {'key': 'days_until_maintenance', 'title': 'Days Until', 'width': 100},
            {'key': 'maintenance_hours', 'title': 'Maintenance Hours', 'width': 120},
            {'key': 'total_runtime_hours', 'title': 'Runtime Hours', 'width': 100}
        ]
        
        self.maintenance_table.set_columns(columns)
        maintenance_frame_layout.addWidget(self.maintenance_table)
        
        # Maintenance actions
        actions_layout = QHBoxLayout()
        
        self.update_maintenance_btn = QPushButton("Update Maintenance")
        self.update_maintenance_btn.setProperty("class", "primary")
        self.update_maintenance_btn.clicked.connect(self.update_maintenance)
        actions_layout.addWidget(self.update_maintenance_btn)
        
        actions_layout.addStretch()
        
        maintenance_frame_layout.addLayout(actions_layout)
        
        tab_layout.addWidget(maintenance_frame)
        
        return tab_widget
    
    def create_utilization_tab(self) -> QWidget:
        """Create utilization tab."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(15)
        
        # Utilization frame
        utilization_frame = QFrame()
        utilization_frame.setProperty("class", "form-section")
        utilization_frame_layout = QVBoxLayout(utilization_frame)
        
        # Title
        utilization_title = QLabel("Station Utilization")
        utilization_title.setProperty("class", "section-header")
        utilization_frame_layout.addWidget(utilization_title)
        
        # Date range selection
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("Date Range:"))
        
        self.util_start_date = QDateEdit()
        self.util_start_date.setCalendarPopup(True)
        self.util_start_date.setDate(QDate.currentDate().addDays(-30))
        self.util_start_date.setProperty("class", "form-input")
        date_layout.addWidget(self.util_start_date)
        
        date_layout.addWidget(QLabel("to"))
        
        self.util_end_date = QDateEdit()
        self.util_end_date.setCalendarPopup(True)
        self.util_end_date.setDate(QDate.currentDate())
        self.util_end_date.setProperty("class", "form-input")
        date_layout.addWidget(self.util_end_date)
        
        self.calculate_util_btn = QPushButton("Calculate")
        self.calculate_util_btn.setProperty("class", "primary")
        self.calculate_util_btn.clicked.connect(self.calculate_utilization)
        date_layout.addWidget(self.calculate_util_btn)
        
        date_layout.addStretch()
        
        utilization_frame_layout.addLayout(date_layout)
        
        # Utilization display
        self.utilization_display = QPlainTextEdit()
        self.utilization_display.setReadOnly(True)
        self.utilization_display.setProperty("class", "form-output")
        self.utilization_display.setMaximumHeight(400)
        utilization_frame_layout.addWidget(self.utilization_display)
        
        tab_layout.addWidget(utilization_frame)
        
        return tab_widget
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Setup callbacks
        self.controller.register_data_changed_callback(self.on_data_changed)
        self.controller.register_status_message_callback(self.on_status_message)
        
        # Station table selection
        if self.station_table:
            self.station_table.row_selected.connect(self.on_station_selected)
    
    def load_initial_data(self) -> None:
        """Load initial data."""
        try:
            # Load station type options
            self.station_type_options = self.controller.get_station_type_options()
            self.station_type_combo.clear()
            self.station_type_combo.addItem("Select Station Type...", "")
            for option in self.station_type_options:
                self.station_type_combo.addItem(option['label'], option['value'])
            
            # Load station status options
            self.station_status_options = self.controller.get_station_status_options()
            self.station_status_combo.clear()
            for option in self.station_status_options:
                self.station_status_combo.addItem(option['label'], option['value'])
            # Default to available
            self.station_status_combo.setCurrentText("Available")
            
            # Load station list
            self.load_station_list()
            
            # Load maintenance schedule
            self.load_maintenance_schedule()
            
            # Calculate utilization for default date range
            self.calculate_utilization()
            
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
    
    def load_station_list(self) -> None:
        """Load station list."""
        try:
            # Get station summary
            summary = self.controller.get_station_summary()
            
            # For now, create placeholder data
            # In a real implementation, would load from database
            station_data = [
                {
                    'station_id': 'EXP-001',
                    'name': 'Pre-Expander 1',
                    'station_type': 'pre_expander',
                    'status': 'running',
                    'location': 'Production Floor',
                    'current_operator_name': 'J. Smith',
                    'capacity_per_hour': 500.0,
                    'total_runtime_hours': 1250.5
                },
                {
                    'station_id': 'MOLD-001',
                    'name': 'Block Mold 1',
                    'station_type': 'block_mold',
                    'status': 'available',
                    'location': 'Production Floor',
                    'current_operator_name': '',
                    'capacity_per_hour': 50.0,
                    'total_runtime_hours': 890.2
                },
                {
                    'station_id': 'CUT-001',
                    'name': 'Hot Wire Cutter',
                    'station_type': 'hot_wire_cutter',
                    'status': 'maintenance',
                    'location': 'Cutting Area',
                    'current_operator_name': '',
                    'capacity_per_hour': 25.0,
                    'total_runtime_hours': 450.8
                }
            ]
            
            if self.station_table:
                self.station_table.set_data(station_data)
            
        except Exception as e:
            logger.error(f"Error loading station list: {e}")
    
    def load_maintenance_schedule(self) -> None:
        """Load maintenance schedule."""
        try:
            # Get maintenance schedule for next 30 days
            maintenance_data = self.controller.get_maintenance_schedule(30)
            
            formatted_data = []
            for item in maintenance_data:
                formatted_data.append({
                    'station_id': item['station_id'],
                    'name': item['name'],
                    'last_maintenance_date': item['last_maintenance_date'].strftime('%Y-%m-%d') if item['last_maintenance_date'] else 'Never',
                    'next_maintenance_date': item['next_maintenance_date'].strftime('%Y-%m-%d') if item['next_maintenance_date'] else 'Not scheduled',
                    'days_until_maintenance': item['days_until_maintenance'],
                    'maintenance_hours': item['maintenance_hours'],
                    'total_runtime_hours': item['total_runtime_hours']
                })
            
            if self.maintenance_table:
                self.maintenance_table.set_data(formatted_data)
            
        except Exception as e:
            logger.error(f"Error loading maintenance schedule: {e}")
    
    def create_station(self) -> None:
        """Create a new station."""
        try:
            # Validate required fields
            station_id = self.station_id_input.text().strip()
            if not station_id:
                show_error("Please enter station ID")
                return
            
            station_name = self.station_name_input.text().strip()
            if not station_name:
                show_error("Please enter station name")
                return
            
            station_type = self.station_type_combo.currentData()
            if not station_type:
                show_error("Please select station type")
                return
            
            # Gather form data
            status = self.station_status_combo.currentData() or 'available'
            location = self.location_input.text().strip() or None
            department = self.department_input.text().strip() or None
            capacity = self.capacity_spin.value() if self.capacity_spin.value() > 0 else None
            max_block_size = self.max_block_size_input.text().strip() or None
            temp_range = self.temp_range_input.text().strip() or None
            notes = self.notes_input.toPlainText().strip() or None
            
            # Create station
            self.controller.create_station(
                station_id=station_id,
                name=station_name,
                station_type=station_type,
                location=location,
                department=department,
                capacity_per_hour=Decimal(str(capacity)) if capacity else None,
                max_block_size=max_block_size,
                temperature_range=temp_range,
                notes=notes
            )
            
            # Clear form
            self.clear_form()
            
            # Refresh station list
            self.load_station_list()
            
        except Exception as e:
            logger.error(f"Error creating station: {e}")
            show_error(f"Error creating station: {str(e)}")
    
    def update_station(self) -> None:
        """Update existing station."""
        try:
            if not self.current_station_id:
                show_error("No station selected for update")
                return
            
            # Update station status
            status = self.station_status_combo.currentData()
            if status:
                self.controller.update_station_status(
                    station_id=self.current_station_id,
                    status=status
                )
            
            # Refresh station list
            self.load_station_list()
            
            # Reset update button
            self.update_station_btn.setEnabled(False)
            self.current_station_id = None
            
        except Exception as e:
            logger.error(f"Error updating station: {e}")
            show_error(f"Error updating station: {str(e)}")
    
    def assign_work(self) -> None:
        """Assign work to station."""
        try:
            if not self.current_station_id:
                show_error("No station selected")
                return
            
            work_order_text = self.work_order_input.text().strip()
            if not work_order_text:
                show_error("Please enter work order number")
                return
            
            try:
                work_order_id = int(work_order_text)
            except ValueError:
                show_error("Invalid work order number")
                return
            
            operator_name = self.operator_input.text().strip()
            if not operator_name:
                show_error("Please enter operator name")
                return
            
            # Assign work
            self.controller.assign_work_to_station(
                station_id=self.current_station_id,
                work_order_id=work_order_id,
                operator_id=operator_name,  # Would use actual ID
                operator_name=operator_name
            )
            
            # Clear work assignment form
            self.work_order_input.clear()
            self.operator_input.clear()
            
            # Refresh station list
            self.load_station_list()
            
        except Exception as e:
            logger.error(f"Error assigning work: {e}")
            show_error(f"Error assigning work: {str(e)}")
    
    def release_work(self) -> None:
        """Release work from station."""
        try:
            if not self.current_station_id:
                show_error("No station selected")
                return
            
            self.controller.release_station_work(self.current_station_id)
            
            # Refresh station list
            self.load_station_list()
            
        except Exception as e:
            logger.error(f"Error releasing work: {e}")
            show_error(f"Error releasing work: {str(e)}")
    
    def clear_form(self) -> None:
        """Clear the station form."""
        self.station_id_input.clear()
        self.station_name_input.clear()
        self.station_type_combo.setCurrentIndex(0)
        self.station_status_combo.setCurrentText("Available")
        self.location_input.clear()
        self.department_input.clear()
        self.capacity_spin.setValue(0)
        self.max_block_size_input.clear()
        self.temp_range_input.clear()
        self.notes_input.clear()
        self.work_order_input.clear()
        self.operator_input.clear()
        
        # Reset update button
        self.update_station_btn.setEnabled(False)
        self.current_station_id = None
    
    def on_station_selected(self, row: int) -> None:
        """Handle station selection in table."""
        try:
            if self.station_table and self.station_table.data_table.rowCount() > row:
                station_id_item = self.station_table.data_table.item(row, 0)
                self.current_station_id = station_id_item.text()
                
                # Load station data into form
                # In a real implementation, would populate form with station data
                self.station_id_input.setText(self.current_station_id)
                self.station_id_input.setEnabled(False)  # Don't allow editing ID
                
                self.update_station_btn.setEnabled(True)
                
        except Exception as e:
            logger.error(f"Error selecting station: {e}")
    
    def update_maintenance(self) -> None:
        """Update maintenance records."""
        try:
            if not self.current_station_id:
                show_error("Please select a station first")
                return
            
            # Placeholder for maintenance update
            # In a real implementation, would show maintenance dialog
            maintenance_hours = 8  # Placeholder
            
            self.controller.update_maintenance(
                station_id=self.current_station_id,
                maintenance_hours=maintenance_hours
            )
            
            # Refresh maintenance schedule
            self.load_maintenance_schedule()
            
        except Exception as e:
            logger.error(f"Error updating maintenance: {e}")
            show_error(f"Error updating maintenance: {str(e)}")
    
    def calculate_utilization(self) -> None:
        """Calculate station utilization."""
        try:
            start_date = self.util_start_date.date().toPython()
            end_date = self.util_end_date.date().toPython()
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Get utilization data
            utilization_data = self.controller.station_management_service.get_station_utilization(
                start_date, end_datetime
            )
            
            # Format utilization display
            util_text = f"Station Utilization Report\n"
            util_text += f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n"
            util_text += "=" * 60 + "\n\n"
            
            util_text += f"Overall Utilization: {utilization_data['overall_utilization_percentage']:.1f}%\n"
            util_text += f"Total Available Hours: {utilization_data['total_available_hours']:.1f}\n"
            util_text += f"Total Running Hours: {utilization_data['total_running_hours']:.1f}\n"
            util_text += f"Station Count: {utilization_data['station_count']}\n\n"
            
            util_text += "Station Breakdown:\n"
            util_text += "-" * 30 + "\n"
            for station in utilization_data['station_breakdown']:
                util_text += f"{station['station_id']} - {station['name']}:\n"
                util_text += f"  Type: {station['station_type']}\n"
                util_text += f"  Status: {station['status']}\n"
                util_text += f"  Utilization: {station['utilization_percentage']:.1f}%\n"
                util_text += f"  Hours: {station['running_hours']:.1f} / {station['total_hours']:.1f}\n\n"
            
            self.utilization_display.setPlainText(util_text)
            
        except Exception as e:
            logger.error(f"Error calculating utilization: {e}")
            show_error(f"Error calculating utilization: {str(e)}")
    
    def filter_stations(self) -> None:
        """Filter stations by status."""
        try:
            status_filter = self.station_filter_combo.currentData()
            
            # Reload stations with filter
            # In a real implementation, would apply filter to data loading
            self.load_station_list()
            
        except Exception as e:
            logger.error(f"Error filtering stations: {e}")
    
    def refresh_data(self) -> None:
        """Refresh all data."""
        try:
            self.load_station_list()
            self.load_maintenance_schedule()
            self.calculate_utilization()
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
    
    def export_station_data(self) -> None:
        """Export station data."""
        try:
            # Placeholder for export functionality
            show_info("Export functionality would be implemented here")
        except Exception as e:
            logger.error(f"Error exporting station data: {e}")
            show_error(f"Error exporting data: {str(e)}")
    
    def on_data_changed(self) -> None:
        """Handle data change notifications."""
        self.load_station_list()
        self.load_maintenance_schedule()
    
    def on_status_message(self, message: str, timeout: int) -> None:
        """Handle status message notifications."""
        logger.info(f"Status: {message}")
