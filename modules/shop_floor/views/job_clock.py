"""
Job Clock view for XPanda ERP-Lite.
Touch-friendly interface for shop floor time tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame,
    QComboBox, QLineEdit, QTextEdit,
    QGroupBox, QListWidget, QListWidgetItem,
    QDialog, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error
from modules.shop_floor.controllers.shop_floor_controller import ShopFloorController

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_hms(total_seconds: int) -> str:
    """Format a duration in seconds as HH:MM:SS."""
    total_seconds = max(0, int(total_seconds))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _readable_operation(raw: str) -> str:
    return raw.replace('_', ' ').title()


# ---------------------------------------------------------------------------
# Clock-out selection dialog (shown when employee has multiple active entries)
# ---------------------------------------------------------------------------

class ActiveEntrySelectionDialog(QDialog):
    """Let the employee pick which active job to clock out."""

    def __init__(self, entries: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.selected_entry_id: Optional[int] = None
        self._entries = entries
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Select Job to Clock Out")
        self.setModal(True)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        lbl = QLabel("Multiple active jobs found. Pick which one to clock out:")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self._list = QListWidget()
        self._list.setMinimumHeight(160)
        now = datetime.now()
        for e in self._entries:
            elapsed = int((now - e['start_time']).total_seconds())
            parts = [
                _readable_operation(e['operation']),
                f"Elapsed: {_format_hms(elapsed)}",
                f"Since: {e['start_time'].strftime('%H:%M')}",
            ]
            if e.get('station_id'):
                parts.append(f"Station: {e['station_id']}")
            item = QListWidgetItem("  |  ".join(parts))
            item.setData(Qt.ItemDataRole.UserRole, e['id'])
            self._list.addItem(item)
        self._list.setCurrentRow(0)
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("Clock Out Selected")
        ok_btn.setProperty("class", "primary")
        ok_btn.setMinimumHeight(48)
        ok_btn.clicked.connect(self._accept_selection)
        btn_row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(48)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _accept_selection(self) -> None:
        item = self._list.currentItem()
        if item:
            self.selected_entry_id = item.data(Qt.ItemDataRole.UserRole)
            self.accept()


# ---------------------------------------------------------------------------
# Background timer thread
# ---------------------------------------------------------------------------

class LiveTimerThread(QThread):
    """Polls active entries every second and emits serialized data with elapsed seconds."""
    tick = pyqtSignal(list)   # list of entry dicts, each with 'elapsed_seconds' added

    def __init__(self, controller: ShopFloorController):
        super().__init__()
        self.controller = controller
        self._running = True

    def run(self) -> None:
        while self._running:
            try:
                entries = self.controller.get_active_entries_for_display()
                now = datetime.now()
                for e in entries:
                    e['elapsed_seconds'] = int((now - e['start_time']).total_seconds())
                self.tick.emit(entries)
                self.msleep(1000)
            except Exception as ex:
                logger.error(f"LiveTimerThread error: {ex}")
                self.msleep(5000)

    def stop(self) -> None:
        self._running = False


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------

class JobClockView(QWidget):
    """Touch-friendly job clock for shop floor time tracking."""

    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)

        self.db_manager = db_manager
        self.settings = settings
        self.controller = ShopFloorController(db_manager)

        # Live data
        self._active_entries: List[Dict[str, Any]] = []

        # Debounce timer for clock-out button state (avoids DB hit on every keypress)
        self._clock_out_check_timer = QTimer()
        self._clock_out_check_timer.setSingleShot(True)
        self._clock_out_check_timer.setInterval(450)
        self._clock_out_check_timer.timeout.connect(self._check_clock_out_eligibility)

        # Background timer thread
        self._timer_thread = LiveTimerThread(self.controller)
        self._timer_thread.tick.connect(self._on_timer_tick)

        self._build_ui()
        self._connect_signals()
        self._load_initial_data()

        self._timer_thread.start()
        logger.debug("Job clock view initialized")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        self._build_header(layout)
        self._build_clock_section(layout)
        self._build_active_jobs_section(layout)
        self._build_recent_activity_section(layout)

    def _build_header(self, parent_layout) -> None:
        row = QWidget()
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Job Clock")
        title.setProperty("class", "page-header")
        hl.addWidget(title)
        hl.addStretch()

        self._clock_label = QLabel()
        self._clock_label.setProperty("class", "page-header")
        self._clock_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        hl.addWidget(self._clock_label)

        parent_layout.addWidget(row)

    def _build_clock_section(self, parent_layout) -> None:
        frame = QFrame()
        frame.setProperty("class", "form-section")
        fl = QVBoxLayout(frame)
        fl.setSpacing(12)

        sec_title = QLabel("Clock In / Out")
        sec_title.setProperty("class", "section-header")
        fl.addWidget(sec_title)

        # Row 1: Employee + Work Order
        row1 = QHBoxLayout()

        emp_group = QGroupBox("Employee Name / ID")
        emp_group.setProperty("class", "form-group")
        eg_layout = QVBoxLayout(emp_group)
        self._employee_input = QLineEdit()
        self._employee_input.setPlaceholderText("Enter your name or badge ID")
        self._employee_input.setMinimumHeight(50)
        self._employee_input.setProperty("class", "form-input")
        eg_layout.addWidget(self._employee_input)
        row1.addWidget(emp_group)

        wo_group = QGroupBox("Work Order # (optional)")
        wo_group.setProperty("class", "form-group")
        wo_layout = QVBoxLayout(wo_group)
        self._work_order_input = QLineEdit()
        self._work_order_input.setPlaceholderText("e.g. 1042")
        self._work_order_input.setMinimumHeight(50)
        self._work_order_input.setProperty("class", "form-input")
        wo_layout.addWidget(self._work_order_input)
        row1.addWidget(wo_group)

        fl.addLayout(row1)

        # Row 2: Operation + Station
        row2 = QHBoxLayout()

        op_group = QGroupBox("Operation")
        op_group.setProperty("class", "form-group")
        op_layout = QVBoxLayout(op_group)
        self._operation_combo = QComboBox()
        self._operation_combo.setMinimumHeight(50)
        self._operation_combo.setProperty("class", "form-select")
        op_layout.addWidget(self._operation_combo)
        row2.addWidget(op_group)

        st_group = QGroupBox("Station (optional)")
        st_group.setProperty("class", "form-group")
        st_layout = QVBoxLayout(st_group)
        self._station_combo = QComboBox()
        self._station_combo.setMinimumHeight(50)
        self._station_combo.setProperty("class", "form-select")
        st_layout.addWidget(self._station_combo)
        row2.addWidget(st_group)

        fl.addLayout(row2)

        # Notes
        notes_group = QGroupBox("Notes (optional)")
        notes_group.setProperty("class", "form-group")
        notes_layout = QVBoxLayout(notes_group)
        self._notes_input = QTextEdit()
        self._notes_input.setPlaceholderText("Any notes for this job...")
        self._notes_input.setMaximumHeight(72)
        self._notes_input.setProperty("class", "form-input")
        notes_layout.addWidget(self._notes_input)
        fl.addWidget(notes_group)

        # Big buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self._clock_in_btn = QPushButton("CLOCK IN")
        self._clock_in_btn.setMinimumHeight(80)
        self._clock_in_btn.setProperty("class", "primary")
        self._clock_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clock_in_btn.setEnabled(False)
        btn_row.addWidget(self._clock_in_btn)

        self._clock_out_btn = QPushButton("CLOCK OUT")
        self._clock_out_btn.setMinimumHeight(80)
        self._clock_out_btn.setProperty("class", "accent")
        self._clock_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clock_out_btn.setEnabled(False)
        btn_row.addWidget(self._clock_out_btn)

        fl.addLayout(btn_row)
        parent_layout.addWidget(frame)

    def _build_active_jobs_section(self, parent_layout) -> None:
        frame = QFrame()
        frame.setProperty("class", "form-section")
        fl = QVBoxLayout(frame)
        fl.setSpacing(8)

        hdr = QHBoxLayout()
        title = QLabel("Active Jobs")
        title.setProperty("class", "section-header")
        hdr.addWidget(title)
        hdr.addStretch()

        self._active_count_label = QLabel("0 active")
        self._active_count_label.setProperty("class", "secondary-text")
        hdr.addWidget(self._active_count_label)
        fl.addLayout(hdr)

        self._active_jobs_list = QListWidget()
        self._active_jobs_list.setMinimumHeight(160)
        self._active_jobs_list.setProperty("class", "data-list")
        fl.addWidget(self._active_jobs_list)

        parent_layout.addWidget(frame)

    def _build_recent_activity_section(self, parent_layout) -> None:
        frame = QFrame()
        frame.setProperty("class", "form-section")
        fl = QVBoxLayout(frame)
        fl.setSpacing(8)

        hdr = QHBoxLayout()
        title = QLabel("Recent Activity (last 24 h)")
        title.setProperty("class", "section-header")
        hdr.addWidget(title)
        hdr.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self._load_recent_activity)
        hdr.addWidget(refresh_btn)
        fl.addLayout(hdr)

        self._recent_table = DataTableWithFilter()
        self._recent_table.set_columns([
            {'key': 'employee_name', 'title': 'Employee',  'width': 130},
            {'key': 'operation',     'title': 'Operation', 'width': 110},
            {'key': 'station_id',    'title': 'Station',   'width': 90},
            {'key': 'start_time',    'title': 'Start',     'width': 65},
            {'key': 'end_time',      'title': 'End',       'width': 65},
            {'key': 'total_hours',   'title': 'Hours',     'width': 65},
            {'key': 'status',        'title': 'Status',    'width': 85},
        ])
        self._recent_table.data_table.setMaximumHeight(220)
        fl.addWidget(self._recent_table)

        parent_layout.addWidget(frame)

    # ------------------------------------------------------------------
    # Signals & initial load
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._clock_in_btn.clicked.connect(self._clock_in)
        self._clock_out_btn.clicked.connect(self._clock_out)

        self._employee_input.textChanged.connect(self._on_employee_changed)
        self._operation_combo.currentIndexChanged.connect(self._refresh_clock_in_btn)

        self.controller.register_data_changed_callback(self._on_data_changed)
        self.controller.register_status_message_callback(self._on_status_message)

        # Wall-clock display
        self._wall_clock_timer = QTimer()
        self._wall_clock_timer.timeout.connect(self._update_wall_clock)
        self._wall_clock_timer.start(1000)
        self._update_wall_clock()

    def _load_initial_data(self) -> None:
        try:
            # Operation dropdown
            ops = self.controller.get_operation_options()
            self._operation_combo.clear()
            self._operation_combo.addItem("Select operation...", "")
            for opt in ops:
                self._operation_combo.addItem(opt['label'], opt['value'])

            # Station dropdown
            self._reload_station_combo()

            # Tables
            self._load_active_jobs()
            self._load_recent_activity()

        except Exception as ex:
            logger.error(f"Error loading initial data: {ex}")

    def _reload_station_combo(self) -> None:
        """Refresh the station dropdown from DB (available + running stations)."""
        try:
            stations = self.controller.get_stations_for_clock_in()
            self._station_combo.clear()
            self._station_combo.addItem("No station", "")
            for s in stations:
                label = f"{s['station_id']} — {s['name']}"
                self._station_combo.addItem(label, s['station_id'])
        except Exception as ex:
            logger.warning(f"Could not load station list: {ex}")
            self._station_combo.clear()
            self._station_combo.addItem("No stations available", "")

    # ------------------------------------------------------------------
    # Clock In
    # ------------------------------------------------------------------

    def _clock_in(self) -> None:
        employee = self._employee_input.text().strip()
        if not employee:
            show_error("Missing Field", "Please enter your name or ID.", parent=self)
            return

        operation = self._operation_combo.currentData()
        if not operation:
            show_error("Missing Field", "Please select an operation.", parent=self)
            return

        # Optional work order
        work_order_id = None
        wo_text = self._work_order_input.text().strip()
        if wo_text:
            try:
                work_order_id = int(wo_text)
            except ValueError:
                show_error("Invalid Input", "Work Order # must be a number.", parent=self)
                return

        station_id = self._station_combo.currentData() or None
        notes = self._notes_input.toPlainText().strip() or None

        try:
            self.controller.clock_in_operator(
                employee_id=employee,
                employee_name=employee,
                work_order_id=work_order_id,
                operation=operation,
                station_id=station_id,
                notes=notes,
            )
            self._clear_form()
            self._reload_station_combo()
        except Exception as ex:
            logger.error(f"Clock-in error: {ex}")
            show_error("Clock In Error", str(ex), parent=self)

    # ------------------------------------------------------------------
    # Clock Out
    # ------------------------------------------------------------------

    def _clock_out(self) -> None:
        employee = self._employee_input.text().strip()
        if not employee:
            show_error("Missing Field", "Please enter your name or ID.", parent=self)
            return

        try:
            active = self.controller.get_active_entries_for_display(employee)
        except Exception as ex:
            show_error("Lookup Error", str(ex), parent=self)
            return

        if not active:
            show_error("Not Clocked In", f"No active jobs found for '{employee}'.", parent=self)
            return

        if len(active) == 1:
            entry_id = active[0]['id']
        else:
            dlg = ActiveEntrySelectionDialog(active, parent=self)
            if dlg.exec() != QDialog.DialogCode.Accepted or dlg.selected_entry_id is None:
                return
            entry_id = dlg.selected_entry_id

        try:
            self.controller.clock_out_operator(entry_id)
            self._clear_form()
        except Exception as ex:
            logger.error(f"Clock-out error: {ex}")
            show_error("Clock Out Error", str(ex), parent=self)

    # ------------------------------------------------------------------
    # Form helpers
    # ------------------------------------------------------------------

    def _clear_form(self) -> None:
        self._employee_input.clear()
        self._work_order_input.clear()
        self._operation_combo.setCurrentIndex(0)
        self._station_combo.setCurrentIndex(0)
        self._notes_input.clear()

    # ------------------------------------------------------------------
    # Button state management
    # ------------------------------------------------------------------

    def _on_employee_changed(self) -> None:
        self._refresh_clock_in_btn()
        # Debounce the DB-hitting clock-out check
        self._clock_out_check_timer.stop()
        if self._employee_input.text().strip():
            self._clock_out_check_timer.start()
        else:
            self._clock_out_btn.setEnabled(False)

    def _refresh_clock_in_btn(self) -> None:
        has_employee = bool(self._employee_input.text().strip())
        has_operation = bool(self._operation_combo.currentData())
        self._clock_in_btn.setEnabled(has_employee and has_operation)

    def _check_clock_out_eligibility(self) -> None:
        """DB lookup to see whether the typed employee has active entries."""
        employee = self._employee_input.text().strip()
        if not employee:
            self._clock_out_btn.setEnabled(False)
            return
        try:
            active = self.controller.get_active_entries_for_display(employee)
            self._clock_out_btn.setEnabled(len(active) > 0)
        except Exception:
            self._clock_out_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Live timer display
    # ------------------------------------------------------------------

    @pyqtSlot(list)
    def _on_timer_tick(self, entries: list) -> None:
        """Receive updated active entries from LiveTimerThread every second."""
        self._active_entries = entries
        self._refresh_active_jobs_display()

    def _refresh_active_jobs_display(self) -> None:
        self._active_jobs_list.clear()
        self._active_count_label.setText(f"{len(self._active_entries)} active")

        for e in self._active_entries:
            elapsed_str = _format_hms(e.get('elapsed_seconds', 0))
            station_part = f"  |  {e['station_id']}" if e.get('station_id') else ''
            line1 = f"{e['employee_name']}  —  {_readable_operation(e['operation'])}{station_part}"
            line2 = f"  Elapsed: {elapsed_str}  |  Started: {e['start_time'].strftime('%H:%M:%S')}"
            item = QListWidgetItem(f"{line1}\n{line2}")
            item.setData(Qt.ItemDataRole.UserRole, e['id'])
            self._active_jobs_list.addItem(item)

    def _load_active_jobs(self) -> None:
        """Initial load of active jobs (before the timer thread fires)."""
        try:
            entries = self.controller.get_active_entries_for_display()
            now = datetime.now()
            for e in entries:
                e['elapsed_seconds'] = int((now - e['start_time']).total_seconds())
            self._active_entries = entries
            self._refresh_active_jobs_display()
        except Exception as ex:
            logger.error(f"Error loading active jobs: {ex}")

    # ------------------------------------------------------------------
    # Recent activity
    # ------------------------------------------------------------------

    def _load_recent_activity(self) -> None:
        try:
            rows = self.controller.get_recent_completed_entries(hours=24)
            self._recent_table.load_data(rows)
        except Exception as ex:
            logger.error(f"Error loading recent activity: {ex}")

    # ------------------------------------------------------------------
    # Wall clock
    # ------------------------------------------------------------------

    def _update_wall_clock(self) -> None:
        self._clock_label.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_data_changed(self) -> None:
        self._load_active_jobs()
        self._load_recent_activity()
        # Re-check clock-out eligibility if employee is typed
        if self._employee_input.text().strip():
            self._check_clock_out_eligibility()

    def _on_status_message(self, message: str, timeout: int) -> None:
        logger.info(f"Status: {message}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        self._timer_thread.stop()
        self._timer_thread.wait()
        self._wall_clock_timer.stop()
        self._clock_out_check_timer.stop()
