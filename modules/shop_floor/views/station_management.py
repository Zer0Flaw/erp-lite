"""
Station Management view for XPanda ERP-Lite.
Handles production stations and equipment status tracking.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame,
    QComboBox, QLineEdit, QTextEdit,
    QGroupBox, QFormLayout,
    QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete
from modules.shop_floor.controllers.shop_floor_controller import ShopFloorController

logger = logging.getLogger(__name__)

# Status display labels
STATUS_LABELS = {
    'available':   'Available',
    'running':     'Running',
    'maintenance': 'Maintenance',
    'offline':     'Offline',
    'cleanup':     'Cleanup',
}


class StationManagementView(QWidget):
    """Station management view for production stations and equipment tracking."""

    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)

        self.db_manager = db_manager
        self.settings = settings
        self.controller = ShopFloorController(db_manager)

        self.station_table: Optional[DataTableWithFilter] = None
        self.maintenance_table: Optional[DataTableWithFilter] = None

        # In-memory station rows, keyed by station_id for fast lookup
        self._station_rows: List[Dict[str, Any]] = []
        self.current_station_id: Optional[str] = None

        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()

        logger.debug("Station management view initialized")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self._build_header(main_layout)
        self._build_station_tab(main_layout)

    def _build_header(self, parent_layout) -> None:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Station Management")
        title.setProperty("class", "page-header")
        layout.addWidget(title)
        layout.addStretch()

        seed_btn = QPushButton("Seed Default Stations")
        seed_btn.setProperty("class", "secondary")
        seed_btn.setToolTip("Pre-populate XPanda floor layout (only adds stations if none exist)")
        seed_btn.clicked.connect(self.seed_default_stations)
        layout.addWidget(seed_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)

        parent_layout.addWidget(header)

    def _build_station_tab(self, parent_layout) -> None:
        """Build the main station management area (form left, list right)."""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        form_widget = self._build_station_form()
        list_widget = self._build_station_list()

        splitter.addWidget(form_widget)
        splitter.addWidget(list_widget)
        splitter.setSizes([420, 680])

        parent_layout.addWidget(splitter, stretch=1)

    # ---------- Left panel: Add / Edit form ----------

    def _build_station_form(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 8, 0)

        # Section title
        self._form_title = QLabel("Add Station")
        self._form_title.setProperty("class", "section-header")
        layout.addWidget(self._form_title)

        # Basic info
        basic_group = QGroupBox("Basic Information")
        basic_group.setProperty("class", "form-group")
        basic_layout = QFormLayout(basic_group)

        self.station_id_input = QLineEdit()
        self.station_id_input.setPlaceholderText("e.g. PRE-EXP-01")
        self.station_id_input.setProperty("class", "form-input")
        basic_layout.addRow("Station ID *:", self.station_id_input)

        self.station_name_input = QLineEdit()
        self.station_name_input.setPlaceholderText("e.g. Pre-Expander")
        self.station_name_input.setProperty("class", "form-input")
        basic_layout.addRow("Name *:", self.station_name_input)

        self.station_type_combo = QComboBox()
        self.station_type_combo.setProperty("class", "form-select")
        basic_layout.addRow("Station Type *:", self.station_type_combo)

        self.station_status_combo = QComboBox()
        self.station_status_combo.setProperty("class", "form-select")
        basic_layout.addRow("Status:", self.station_status_combo)

        layout.addWidget(basic_group)

        # Location
        loc_group = QGroupBox("Location & Capacity")
        loc_group.setProperty("class", "form-group")
        loc_layout = QFormLayout(loc_group)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g. Production Floor")
        self.location_input.setProperty("class", "form-input")
        loc_layout.addRow("Location:", self.location_input)

        self.department_input = QLineEdit()
        self.department_input.setPlaceholderText("e.g. Manufacturing")
        self.department_input.setProperty("class", "form-input")
        loc_layout.addRow("Department:", self.department_input)

        self.capacity_input = QLineEdit()
        self.capacity_input.setPlaceholderText("Units per hour (number)")
        self.capacity_input.setProperty("class", "form-input")
        loc_layout.addRow("Capacity/Hour:", self.capacity_input)

        layout.addWidget(loc_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_group.setProperty("class", "form-group")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Optional notes...")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setProperty("class", "form-input")
        notes_layout.addWidget(self.notes_input)

        layout.addWidget(notes_group)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.save_station_btn = QPushButton("Save Station")
        self.save_station_btn.setProperty("class", "primary")
        self.save_station_btn.clicked.connect(self.save_station)
        btn_layout.addWidget(self.save_station_btn)

        self.clear_form_btn = QPushButton("Clear")
        self.clear_form_btn.setProperty("class", "secondary")
        self.clear_form_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.clear_form_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    # ---------- Right panel: Station list ----------

    def _build_station_list(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header row: title + status filter
        header_row = QHBoxLayout()

        list_title = QLabel("Stations")
        list_title.setProperty("class", "section-header")
        header_row.addWidget(list_title)
        header_row.addStretch()

        filter_label = QLabel("Filter:")
        header_row.addWidget(filter_label)

        self.station_filter_combo = QComboBox()
        self.station_filter_combo.setProperty("class", "form-select")
        self.station_filter_combo.addItem("All Stations", "")
        for val, label in STATUS_LABELS.items():
            self.station_filter_combo.addItem(label, val)
        self.station_filter_combo.currentIndexChanged.connect(self.load_station_list)
        header_row.addWidget(self.station_filter_combo)

        layout.addLayout(header_row)

        # Table
        self.station_table = DataTableWithFilter()
        columns = [
            {'key': 'station_id',           'title': 'Station ID',   'width': 110},
            {'key': 'name',                  'title': 'Name',         'width': 150},
            {'key': 'station_type',          'title': 'Type',         'width': 120},
            {'key': 'status',                'title': 'Status',       'width': 100},
            {'key': 'location',              'title': 'Location',     'width': 120},
            {'key': 'current_operator_name', 'title': 'Operator',     'width': 110},
            {'key': 'capacity_per_hour',     'title': 'Cap/Hr',       'width': 70},
        ]
        self.station_table.set_columns(columns)
        layout.addWidget(self.station_table, stretch=1)

        # Row action panel (visible when a row is selected)
        self.row_action_panel = self._build_row_action_panel()
        layout.addWidget(self.row_action_panel)

        return container

    def _build_row_action_panel(self) -> QFrame:
        """Panel shown below the table for acting on the selected row."""
        panel = QFrame()
        panel.setProperty("class", "form-section")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self.selected_station_label = QLabel("No station selected")
        self.selected_station_label.setProperty("class", "secondary-text")
        layout.addWidget(self.selected_station_label)

        layout.addStretch()

        status_label = QLabel("Set Status:")
        layout.addWidget(status_label)

        self.quick_status_combo = QComboBox()
        self.quick_status_combo.setProperty("class", "form-select")
        for val, label in STATUS_LABELS.items():
            self.quick_status_combo.addItem(label, val)
        self.quick_status_combo.setEnabled(False)
        layout.addWidget(self.quick_status_combo)

        self.apply_status_btn = QPushButton("Apply")
        self.apply_status_btn.setProperty("class", "accent")
        self.apply_status_btn.setEnabled(False)
        self.apply_status_btn.clicked.connect(self.apply_quick_status)
        layout.addWidget(self.apply_status_btn)

        edit_btn = QPushButton("Edit in Form")
        edit_btn.setProperty("class", "secondary")
        edit_btn.setEnabled(False)
        edit_btn.clicked.connect(self.load_selected_into_form)
        self._edit_btn = edit_btn
        layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("class", "danger")
        delete_btn.setEnabled(False)
        delete_btn.clicked.connect(self.delete_selected_station)
        self._delete_btn = delete_btn
        layout.addWidget(delete_btn)

        return panel

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def setup_connections(self) -> None:
        self.controller.register_data_changed_callback(self.on_data_changed)
        self.controller.register_status_message_callback(self.on_status_message)

        if self.station_table:
            self.station_table.selection_changed.connect(self.on_station_selected)

    def load_initial_data(self) -> None:
        try:
            # Populate station type combo
            type_options = self.controller.get_station_type_options()
            self.station_type_combo.clear()
            self.station_type_combo.addItem("Select type...", "")
            for opt in type_options:
                self.station_type_combo.addItem(opt['label'], opt['value'])

            # Populate status combo
            status_options = self.controller.get_station_status_options()
            self.station_status_combo.clear()
            for opt in status_options:
                self.station_status_combo.addItem(opt['label'], opt['value'])
            self.station_status_combo.setCurrentText("Available")

            self.load_station_list()

        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
            show_error("Load Error", f"Error loading station data: {str(e)}", parent=self)

    def load_station_list(self) -> None:
        """Reload station table from DB, applying any active status filter."""
        try:
            status_filter = self.station_filter_combo.currentData() or None
            self._station_rows = self.controller.get_all_stations(status_filter)

            display_rows = []
            for s in self._station_rows:
                display_rows.append({
                    'station_id':           s['station_id'],
                    'name':                 s['name'],
                    'station_type':         s['station_type'].replace('_', ' ').title(),
                    'status':               STATUS_LABELS.get(s['status'], s['status']),
                    'location':             s['location'],
                    'current_operator_name': s['current_operator_name'],
                    'capacity_per_hour':    f"{s['capacity_per_hour']:.0f}" if s['capacity_per_hour'] else '',
                })

            if self.station_table:
                self.station_table.load_data(display_rows)

            self._clear_row_actions()

        except Exception as e:
            logger.error(f"Error loading station list: {e}")

    # ------------------------------------------------------------------
    # Row selection & row action panel
    # ------------------------------------------------------------------

    def on_station_selected(self, selected_data: list) -> None:
        """Handle row selection — update row-action panel and store current id."""
        try:
            if not selected_data:
                self._clear_row_actions()
                return

            # selected_data contains display-formatted dicts; use station_id to get raw data
            display_row = selected_data[0]
            station_id = display_row.get('station_id')
            station = next((s for s in self._station_rows if s['station_id'] == station_id), None)
            if not station:
                self._clear_row_actions()
                return

            self.current_station_id = station['station_id']

            self.selected_station_label.setText(
                f"Selected: {station['station_id']} — {station['name']}"
            )

            # Sync quick-status combo to current status
            idx = self.quick_status_combo.findData(station['status'])
            if idx >= 0:
                self.quick_status_combo.setCurrentIndex(idx)

            self.quick_status_combo.setEnabled(True)
            self.apply_status_btn.setEnabled(True)
            self._edit_btn.setEnabled(True)
            self._delete_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"Error handling station selection: {e}")

    def _clear_row_actions(self) -> None:
        self.current_station_id = None
        self.selected_station_label.setText("No station selected")
        self.quick_status_combo.setEnabled(False)
        self.apply_status_btn.setEnabled(False)
        self._edit_btn.setEnabled(False)
        self._delete_btn.setEnabled(False)

    def apply_quick_status(self) -> None:
        """Apply status from the row-action panel to the currently selected station."""
        if not self.current_station_id:
            return
        try:
            new_status = self.quick_status_combo.currentData()
            self.controller.update_station_status(
                station_id=self.current_station_id,
                status=new_status
            )
            self.load_station_list()
        except Exception as e:
            logger.error(f"Error applying status: {e}")
            show_error("Status Error", f"Error updating status: {str(e)}", parent=self)

    def load_selected_into_form(self) -> None:
        """Populate the left form with the currently selected station's data."""
        if not self.current_station_id:
            return
        station = next(
            (s for s in self._station_rows if s['station_id'] == self.current_station_id),
            None
        )
        if not station:
            return

        self._form_title.setText(f"Edit Station — {station['station_id']}")
        self.station_id_input.setText(station['station_id'])
        self.station_id_input.setEnabled(False)   # ID is immutable once created
        self.station_name_input.setText(station['name'])

        idx = self.station_type_combo.findData(station['station_type'])
        if idx >= 0:
            self.station_type_combo.setCurrentIndex(idx)

        status_idx = self.station_status_combo.findData(station['status'])
        if status_idx >= 0:
            self.station_status_combo.setCurrentIndex(status_idx)

        self.location_input.setText(station['location'])
        self.department_input.setText(station['department'])
        cap = station['capacity_per_hour']
        self.capacity_input.setText(str(int(cap)) if cap else '')
        self.notes_input.setPlainText(station['notes'])

        self.save_station_btn.setText("Update Station")

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    def save_station(self) -> None:
        """Create or update a station depending on edit mode."""
        station_id = self.station_id_input.text().strip()
        station_name = self.station_name_input.text().strip()
        station_type = self.station_type_combo.currentData()

        if not station_id:
            show_error("Validation Error", "Station ID is required.", parent=self)
            return
        if not station_name:
            show_error("Validation Error", "Station Name is required.", parent=self)
            return
        if not station_type:
            show_error("Validation Error", "Please select a Station Type.", parent=self)
            return

        status = self.station_status_combo.currentData() or 'available'
        location = self.location_input.text().strip() or None
        department = self.department_input.text().strip() or None
        notes = self.notes_input.toPlainText().strip() or None

        cap_text = self.capacity_input.text().strip()
        capacity = None
        if cap_text:
            try:
                capacity = Decimal(cap_text)
            except Exception:
                show_error("Validation Error", "Capacity/Hour must be a number.", parent=self)
                return

        editing = not self.station_id_input.isEnabled()   # ID field disabled = edit mode

        try:
            if editing:
                self.controller.update_station(
                    station_id=station_id,
                    name=station_name,
                    station_type=station_type,
                    status=status,
                    location=location,
                    department=department,
                    capacity_per_hour=capacity,
                    notes=notes,
                )
            else:
                self.controller.create_station(
                    station_id=station_id,
                    name=station_name,
                    station_type=station_type,
                    location=location,
                    department=department,
                    capacity_per_hour=capacity,
                    notes=notes,
                )

            self.clear_form()
            self.load_station_list()

        except Exception as e:
            logger.error(f"Error saving station: {e}")
            show_error("Save Error", f"Error saving station: {str(e)}", parent=self)

    def delete_selected_station(self) -> None:
        """Hard-delete the selected station after confirmation."""
        if not self.current_station_id:
            return
        if not confirm_delete(
            f"Delete station {self.current_station_id}?",
            parent=self
        ):
            return
        try:
            with self.db_manager.get_session() as session:
                from database.models.shop_floor import ProductionStation
                station = session.query(ProductionStation).filter(
                    ProductionStation.station_id == self.current_station_id
                ).first()
                if station:
                    session.delete(station)
                    session.commit()
            self.clear_form()
            self.load_station_list()
        except Exception as e:
            logger.error(f"Error deleting station: {e}")
            show_error("Delete Error", f"Error deleting station: {str(e)}", parent=self)

    def seed_default_stations(self) -> None:
        """Pre-populate XPanda default stations (no-op if stations already exist)."""
        try:
            count = self.controller.seed_default_stations()
            if count > 0:
                show_info("Seed Complete", f"Added {count} default stations.", parent=self)
                self.load_station_list()
            else:
                show_info(
                    "Already Seeded",
                    "Stations already exist — seed skipped.\n"
                    "Delete all stations first to re-seed.",
                    parent=self
                )
        except Exception as e:
            logger.error(f"Error seeding stations: {e}")
            show_error("Seed Error", f"Error seeding stations: {str(e)}", parent=self)

    def clear_form(self) -> None:
        self._form_title.setText("Add Station")
        self.station_id_input.clear()
        self.station_id_input.setEnabled(True)
        self.station_name_input.clear()
        self.station_type_combo.setCurrentIndex(0)
        self.station_status_combo.setCurrentText("Available")
        self.location_input.clear()
        self.department_input.clear()
        self.capacity_input.clear()
        self.notes_input.clear()
        self.save_station_btn.setText("Save Station")

    # ------------------------------------------------------------------
    # Callbacks & refresh
    # ------------------------------------------------------------------

    def refresh_data(self) -> None:
        self.load_station_list()

    def on_data_changed(self) -> None:
        self.load_station_list()

    def on_status_message(self, message: str, timeout: int) -> None:
        logger.info(f"Status: {message}")
