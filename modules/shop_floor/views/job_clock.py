"""
Job Clock view for XPanda ERP-Lite.
Touch-friendly interface for shop floor time tracking.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSizePolicy,
    QComboBox, QLineEdit, QTextEdit, QGridLayout,
    QGroupBox, QSpacerItem, QListWidget, QListWidgetItem,
    QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete
from modules.shop_floor.controllers.shop_floor_controller import ShopFloorController

logger = logging.getLogger(__name__)


class LiveTimerThread(QThread):
    """Thread for updating live timers."""
    update_timer = pyqtSignal(dict)
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = True
        self.active_entries = []
    
    def run(self):
        while self.running:
            try:
                # Get active time entries
                active_entries = self.controller.get_active_time_entries()
                
                # Calculate elapsed times
                timer_data = {}
                for entry in active_entries:
                    elapsed = self.controller.time_entry_service.calculate_elapsed_time(entry)
                    timer_data[entry.id] = {
                        'employee_name': entry.employee_name,
                        'operation': entry.operation,
                        'elapsed_hours': elapsed['elapsed_hours'],
                        'elapsed_minutes': elapsed['elapsed_minutes'],
                        'elapsed_seconds': elapsed['elapsed_seconds'],
                        'start_time': elapsed['start_time']
                    }
                
                self.update_timer.emit(timer_data)
                self.active_entries = active_entries
                
                # Update every second
                self.msleep(1000)
                
            except Exception as e:
                logger.error(f"Error in timer thread: {e}")
                self.msleep(5000)  # Wait 5 seconds on error
    
    def stop(self):
        self.running = False


class JobClockView(QWidget):
    """Main job clock view with touch-friendly interface."""
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        self.controller = ShopFloorController(db_manager)
        
        # UI components
        self.timer_thread = LiveTimerThread(self.controller)
        self.timer_thread.update_timer.connect(self.update_live_timers)
        
        # Data
        self.active_timers = {}  # Store timer data
        self.operation_options = []
        self.station_options = []
        
        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()
        
        # Start timer thread
        self.timer_thread.start()
        
        logger.debug("Job clock view initialized")
    
    def setup_ui(self) -> None:
        """Create touch-friendly UI layout."""
        # Main layout with larger spacing for touch
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self.setup_header(main_layout)
        
        # Clock in/out section
        self.setup_clock_section(main_layout)
        
        # Active jobs section
        self.setup_active_jobs_section(main_layout)
        
        # Recent activity section
        self.setup_recent_activity_section(main_layout)
    
    def setup_header(self, parent_layout) -> None:
        """Create view header."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Job Clock")
        title.setProperty("class", "page-header")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Current time display
        self.time_label = QLabel()
        self.time_label.setProperty("class", "page-header")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(self.time_label)
        
        parent_layout.addWidget(header_widget)
    
    def setup_clock_section(self, parent_layout) -> None:
        """Create clock in/out section with large touch targets."""
        # Clock in/out form
        clock_frame = QFrame()
        clock_frame.setProperty("class", "form-section")
        clock_layout = QVBoxLayout(clock_frame)
        clock_layout.setSpacing(15)
        
        # Title
        form_title = QLabel("Clock In / Out")
        form_title.setProperty("class", "section-header")
        clock_layout.addWidget(form_title)
        
        # Employee info section
        employee_layout = QHBoxLayout()
        
        # Employee ID/Name input
        employee_group = QGroupBox("Employee")
        employee_group.setProperty("class", "form-group")
        employee_group_layout = QVBoxLayout(employee_group)
        
        self.employee_input = QLineEdit()
        self.employee_input.setPlaceholderText("Enter Employee ID or Name")
        self.employee_input.setMinimumHeight(50)  # Large touch target
        self.employee_input.setProperty("class", "form-input")
        employee_group_layout.addWidget(self.employee_input)
        
        employee_layout.addWidget(employee_group)
        
        # Work order input
        work_order_group = QGroupBox("Work Order (Optional)")
        work_order_group.setProperty("class", "form-group")
        work_order_group_layout = QVBoxLayout(work_order_group)
        
        self.work_order_input = QLineEdit()
        self.work_order_input.setPlaceholderText("Enter Work Order #")
        self.work_order_input.setMinimumHeight(50)
        self.work_order_input.setProperty("class", "form-input")
        work_order_group_layout.addWidget(self.work_order_input)
        
        employee_layout.addWidget(work_order_group)
        
        clock_layout.addLayout(employee_layout)
        
        # Operation and station selection
        selection_layout = QHBoxLayout()
        
        # Operation dropdown
        operation_group = QGroupBox("Operation")
        operation_group.setProperty("class", "form-group")
        operation_group_layout = QVBoxLayout(operation_group)
        
        self.operation_combo = QComboBox()
        self.operation_combo.setMinimumHeight(50)
        self.operation_combo.setProperty("class", "form-select")
        operation_group_layout.addWidget(self.operation_combo)
        
        selection_layout.addWidget(operation_group)
        
        # Station dropdown
        station_group = QGroupBox("Station (Optional)")
        station_group.setProperty("class", "form-group")
        station_group_layout = QVBoxLayout(station_group)
        
        self.station_combo = QComboBox()
        self.station_combo.setMinimumHeight(50)
        self.station_combo.setProperty("class", "form-select")
        station_group_layout.addWidget(self.station_combo)
        
        selection_layout.addWidget(station_group)
        
        clock_layout.addLayout(selection_layout)
        
        # Notes section
        notes_group = QGroupBox("Notes (Optional)")
        notes_group.setProperty("class", "form-group")
        notes_group_layout = QVBoxLayout(notes_group)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any notes...")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setProperty("class", "form-input")
        notes_group_layout.addWidget(self.notes_input)
        
        clock_layout.addWidget(notes_group)
        
        # Large clock in/out buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        self.clock_in_btn = QPushButton("CLOCK IN")
        self.clock_in_btn.setMinimumHeight(80)  # Very large touch target
        self.clock_in_btn.setProperty("class", "primary")
        self.clock_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.clock_in_btn)
        
        self.clock_out_btn = QPushButton("CLOCK OUT")
        self.clock_out_btn.setMinimumHeight(80)
        self.clock_out_btn.setProperty("class", "accent")
        self.clock_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clock_out_btn.setEnabled(False)
        button_layout.addWidget(self.clock_out_btn)
        
        clock_layout.addLayout(button_layout)
        
        parent_layout.addWidget(clock_frame)
    
    def setup_active_jobs_section(self, parent_layout) -> None:
        """Create active jobs section with live timers."""
        # Active jobs frame
        active_frame = QFrame()
        active_frame.setProperty("class", "form-section")
        active_layout = QVBoxLayout(active_frame)
        active_layout.setSpacing(15)
        
        # Title
        active_title = QLabel("Active Jobs")
        active_title.setProperty("class", "section-header")
        active_layout.addWidget(active_title)
        
        # Active jobs list with timers
        self.active_jobs_list = QListWidget()
        self.active_jobs_list.setMinimumHeight(200)
        self.active_jobs_list.setProperty("class", "data-list")
        active_layout.addWidget(self.active_jobs_list)
        
        parent_layout.addWidget(active_frame)
    
    def setup_recent_activity_section(self, parent_layout) -> None:
        """Create recent activity section."""
        # Recent activity frame
        recent_frame = QFrame()
        recent_frame.setProperty("class", "form-section")
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setSpacing(15)
        
        # Title
        recent_title = QLabel("Recent Activity")
        recent_title.setProperty("class", "section-header")
        recent_layout.addWidget(recent_title)
        
        # Recent activity table
        self.recent_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'employee_name', 'title': 'Employee', 'width': 150},
            {'key': 'operation', 'title': 'Operation', 'width': 120},
            {'key': 'start_time', 'title': 'Start Time', 'width': 150},
            {'key': 'end_time', 'title': 'End Time', 'width': 150},
            {'key': 'total_hours', 'title': 'Hours', 'width': 80},
            {'key': 'status', 'title': 'Status', 'width': 100}
        ]
        
        self.recent_table.set_columns(columns)
        self.recent_table.data_table.setMaximumHeight(250)
        
        recent_layout.addWidget(self.recent_table)
        parent_layout.addWidget(recent_frame)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        self.clock_in_btn.clicked.connect(self.clock_in)
        self.clock_out_btn.clicked.connect(self.clock_out)
        
        # Enable/disable clock out button based on active entries
        self.employee_input.textChanged.connect(self.update_button_states)
        self.operation_combo.currentTextChanged.connect(self.update_button_states)
        
        # Setup callbacks
        self.controller.register_data_changed_callback(self.on_data_changed)
        self.controller.register_status_message_callback(self.on_status_message)
        
        # Update current time every second
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_current_time)
        self.time_timer.start(1000)
        self.update_current_time()
    
    def load_initial_data(self) -> None:
        """Load initial data."""
        try:
            # Load operation options
            self.operation_options = self.controller.get_operation_options()
            self.operation_combo.clear()
            self.operation_combo.addItem("Select Operation...", "")
            for option in self.operation_options:
                self.operation_combo.addItem(option['label'], option['value'])
            
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
            
            # Load recent activity
            self.load_recent_activity()
            
            # Load active jobs
            self.load_active_jobs()
            
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
    
    def clock_in(self) -> None:
        """Handle clock in action."""
        try:
            employee_id = self.employee_input.text().strip()
            if not employee_id:
                show_error("Please enter employee ID or name")
                return
            
            operation_data = self.operation_combo.currentData()
            if not operation_data:
                show_error("Please select an operation")
                return
            
            # Parse work order if provided
            work_order_id = None
            work_order_text = self.work_order_input.text().strip()
            if work_order_text:
                try:
                    work_order_id = int(work_order_text)
                except ValueError:
                    show_error("Invalid work order number")
                    return
            
            # Get station if selected
            station_id = self.station_combo.currentData() or None
            
            # Get notes
            notes = self.notes_input.toPlainText().strip()
            
            # Clock in
            self.controller.clock_in_operator(
                employee_id=employee_id,
                employee_name=employee_id,  # In a real app, would look up full name
                work_order_id=work_order_id,
                operation=operation_data,
                station_id=station_id,
                notes=notes
            )
            
            # Clear form
            self.clear_form()
            
        except Exception as e:
            logger.error(f"Error clocking in: {e}")
            show_error(f"Error clocking in: {str(e)}")
    
    def clock_out(self) -> None:
        """Handle clock out action."""
        try:
            employee_id = self.employee_input.text().strip()
            if not employee_id:
                show_error("Please enter employee ID to clock out")
                return
            
            # Get active entries for this employee
            active_entries = self.controller.get_active_time_entries(employee_id)
            
            if not active_entries:
                show_error("No active time entries found for this employee")
                return
            
            if len(active_entries) == 1:
                # Clock out the single entry
                entry = active_entries[0]
                self.controller.clock_out_operator(entry.id)
            else:
                # Multiple entries - show selection dialog
                # For now, clock out the most recent one
                entry = active_entries[0]  # Most recent
                self.controller.clock_out_operator(entry.id)
            
            # Clear form
            self.clear_form()
            
        except Exception as e:
            logger.error(f"Error clocking out: {e}")
            show_error(f"Error clocking out: {str(e)}")
    
    def clear_form(self) -> None:
        """Clear the clock form."""
        self.employee_input.clear()
        self.work_order_input.clear()
        self.operation_combo.setCurrentIndex(0)
        self.station_combo.setCurrentIndex(0)
        self.notes_input.clear()
        self.update_button_states()
    
    def update_button_states(self) -> None:
        """Update button enabled states."""
        employee_filled = bool(self.employee_input.text().strip())
        operation_selected = bool(self.operation_combo.currentData())
        
        # Clock in requires employee and operation
        self.clock_in_btn.setEnabled(employee_filled and operation_selected)
        
        # Clock out requires employee with active entries
        if employee_filled:
            try:
                active_entries = self.controller.get_active_time_entries(self.employee_input.text().strip())
                self.clock_out_btn.setEnabled(len(active_entries) > 0)
            except:
                self.clock_out_btn.setEnabled(False)
        else:
            self.clock_out_btn.setEnabled(False)
    
    def update_current_time(self) -> None:
        """Update current time display."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
    
    @pyqtSlot(dict)
    def update_live_timers(self, timer_data: Dict[str, Any]) -> None:
        """Update live timers for active jobs."""
        self.active_timers = timer_data
        self.refresh_active_jobs_display()
    
    def refresh_active_jobs_display(self) -> None:
        """Refresh the active jobs list with timer data."""
        self.active_jobs_list.clear()
        
        for entry_id, data in self.active_timers.items():
            # Create list item with timer display
            item_text = f"{data['employee_name']} - {data['operation']}\n"
            item_text += f"Time: {data['elapsed_hours']:.2f}h ({data['elapsed_minutes']}m)\n"
            item_text += f"Started: {data['start_time'].strftime('%H:%M:%S')}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, entry_id)
            self.active_jobs_list.addItem(item)
    
    def load_active_jobs(self) -> None:
        """Load active jobs from controller."""
        try:
            active_entries = self.controller.get_active_time_entries()
            
            # Update timer data
            for entry in active_entries:
                elapsed = self.controller.time_entry_service.calculate_elapsed_time(entry)
                self.active_timers[entry.id] = {
                    'employee_name': entry.employee_name,
                    'operation': entry.operation,
                    'elapsed_hours': elapsed['elapsed_hours'],
                    'elapsed_minutes': elapsed['elapsed_minutes'],
                    'elapsed_seconds': elapsed['elapsed_seconds'],
                    'start_time': elapsed['start_time']
                }
            
            self.refresh_active_jobs_display()
            
        except Exception as e:
            logger.error(f"Error loading active jobs: {e}")
    
    def load_recent_activity(self) -> None:
        """Load recent time entries."""
        try:
            # Get entries from last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # For now, we'll use placeholder data
            # In a real implementation, would call controller method
            recent_data = []
            
            self.recent_table.set_data(recent_data)
            
        except Exception as e:
            logger.error(f"Error loading recent activity: {e}")
    
    def on_data_changed(self) -> None:
        """Handle data change notifications."""
        self.load_active_jobs()
        self.load_recent_activity()
        self.update_button_states()
    
    def on_status_message(self, message: str, timeout: int) -> None:
        """Handle status message notifications."""
        logger.info(f"Status: {message}")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.timer_thread:
            self.timer_thread.stop()
            self.timer_thread.wait()
        
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()
