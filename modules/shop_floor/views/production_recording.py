"""
Production Recording view for XPanda ERP-Lite.
Handles production output logging and yield tracking.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSplitter,
    QComboBox, QLineEdit, QTextEdit, QGridLayout,
    QGroupBox, QDoubleSpinBox, QFormLayout, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error
from modules.shop_floor.controllers.shop_floor_controller import ShopFloorController

logger = logging.getLogger(__name__)

_OUTPUT_TYPE_FILTER_OPTIONS = [
    ('All Types', ''),
    ('Foam Block', 'foam_block'),
    ('Fabricated Part', 'fabricated_part'),
    ('Scrap', 'scrap'),
    ('Rework', 'rework'),
]


class ProductionRecordingView(QWidget):
    """Production recording view for logging output and tracking yields."""

    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.settings = settings
        self.controller = ShopFloorController(db_manager)

        self._work_orders: List[Dict[str, Any]] = []
        self._materials: List[Dict[str, Any]] = []

        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(400)
        self._debounce_timer.timeout.connect(self._load_filtered_history)

        self._setup_ui()
        self._setup_connections()
        self._load_initial_data()

        logger.debug("ProductionRecordingView initialized")

    # ── UI Construction ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        self._build_header(main_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_inner = self._build_form()
        form_scroll.setWidget(form_inner)
        splitter.addWidget(form_scroll)

        history_widget = self._build_history()
        splitter.addWidget(history_widget)

        splitter.setSizes([420, 580])
        main_layout.addWidget(splitter)

    def _build_header(self, parent_layout) -> None:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Production Recording")
        title.setProperty("class", "page-header")
        layout.addWidget(title)
        layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self._load_filtered_history)
        layout.addWidget(refresh_btn)

        parent_layout.addWidget(header)

    def _build_form(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 8, 0)

        section_label = QLabel("Record Production Output")
        section_label.setProperty("class", "section-header")
        layout.addWidget(section_label)

        # ── Basic Info ──────────────────────────────────────────────────────
        basic_group = QGroupBox("Basic Information")
        basic_group.setProperty("class", "form-group")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(8)

        self.work_order_combo = QComboBox()
        self.work_order_combo.setProperty("class", "form-select")
        self.work_order_combo.setMinimumHeight(36)
        basic_layout.addRow("Work Order *:", self.work_order_combo)

        self.output_type_combo = QComboBox()
        self.output_type_combo.setProperty("class", "form-select")
        self.output_type_combo.setMinimumHeight(36)
        self.output_type_combo.addItem("Select Output Type...", "")
        self.output_type_combo.addItem("Foam Block", "foam_block")
        self.output_type_combo.addItem("Fabricated Part", "fabricated_part")
        self.output_type_combo.addItem("Scrap", "scrap")
        self.output_type_combo.addItem("Rework", "rework")
        basic_layout.addRow("Output Type *:", self.output_type_combo)

        self.station_combo = QComboBox()
        self.station_combo.setProperty("class", "form-select")
        self.station_combo.setMinimumHeight(36)
        basic_layout.addRow("Station:", self.station_combo)

        self.operator_input = QLineEdit()
        self.operator_input.setPlaceholderText("Operator name")
        self.operator_input.setProperty("class", "form-input")
        self.operator_input.setMinimumHeight(36)
        basic_layout.addRow("Operator *:", self.operator_input)

        layout.addWidget(basic_group)

        # ── Quantities ──────────────────────────────────────────────────────
        qty_group = QGroupBox("Quantity Information")
        qty_group.setProperty("class", "form-group")
        qty_layout = QFormLayout(qty_group)
        qty_layout.setSpacing(8)

        self.qty_produced_spin = QDoubleSpinBox()
        self.qty_produced_spin.setRange(0, 999999)
        self.qty_produced_spin.setDecimals(2)
        self.qty_produced_spin.setProperty("class", "form-input")
        self.qty_produced_spin.setMinimumHeight(36)
        qty_layout.addRow("Qty Produced *:", self.qty_produced_spin)

        self.qty_scrapped_spin = QDoubleSpinBox()
        self.qty_scrapped_spin.setRange(0, 999999)
        self.qty_scrapped_spin.setDecimals(2)
        self.qty_scrapped_spin.setProperty("class", "form-input")
        self.qty_scrapped_spin.setMinimumHeight(36)
        qty_layout.addRow("Qty Scrapped:", self.qty_scrapped_spin)

        self.theoretical_yield_spin = QDoubleSpinBox()
        self.theoretical_yield_spin.setRange(0, 999999)
        self.theoretical_yield_spin.setDecimals(2)
        self.theoretical_yield_spin.setProperty("class", "form-input")
        self.theoretical_yield_spin.setMinimumHeight(36)
        qty_layout.addRow("Theoretical Yield:", self.theoretical_yield_spin)

        layout.addWidget(qty_group)

        # ── Foam Block Specs (conditional) ──────────────────────────────────
        self.foam_group = QGroupBox("Foam Block Specifications")
        self.foam_group.setProperty("class", "form-group")
        self.foam_group.setVisible(False)
        foam_layout = QGridLayout(self.foam_group)
        foam_layout.setSpacing(8)

        foam_layout.addWidget(QLabel("Length (in):"), 0, 0)
        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0, 9999)
        self.length_spin.setDecimals(2)
        self.length_spin.setProperty("class", "form-input")
        self.length_spin.setMinimumHeight(36)
        foam_layout.addWidget(self.length_spin, 0, 1)

        foam_layout.addWidget(QLabel("Width (in):"), 0, 2)
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0, 9999)
        self.width_spin.setDecimals(2)
        self.width_spin.setProperty("class", "form-input")
        self.width_spin.setMinimumHeight(36)
        foam_layout.addWidget(self.width_spin, 0, 3)

        foam_layout.addWidget(QLabel("Height (in):"), 1, 0)
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0, 9999)
        self.height_spin.setDecimals(2)
        self.height_spin.setProperty("class", "form-input")
        self.height_spin.setMinimumHeight(36)
        foam_layout.addWidget(self.height_spin, 1, 1)

        foam_layout.addWidget(QLabel("Density (lb/ft³):"), 1, 2)
        self.density_spin = QDoubleSpinBox()
        self.density_spin.setRange(0, 100)
        self.density_spin.setDecimals(2)
        self.density_spin.setProperty("class", "form-input")
        self.density_spin.setMinimumHeight(36)
        foam_layout.addWidget(self.density_spin, 1, 3)

        layout.addWidget(self.foam_group)

        # ── Traceability ────────────────────────────────────────────────────
        trace_group = QGroupBox("Traceability")
        trace_group.setProperty("class", "form-group")
        trace_layout = QFormLayout(trace_group)
        trace_layout.setSpacing(8)

        self.bead_lot_input = QLineEdit()
        self.bead_lot_input.setPlaceholderText("Raw bead lot number")
        self.bead_lot_input.setProperty("class", "form-input")
        self.bead_lot_input.setMinimumHeight(36)
        trace_layout.addRow("Bead Lot:", self.bead_lot_input)

        self.expansion_batch_input = QLineEdit()
        self.expansion_batch_input.setPlaceholderText("Expansion batch number")
        self.expansion_batch_input.setProperty("class", "form-input")
        self.expansion_batch_input.setMinimumHeight(36)
        trace_layout.addRow("Expansion Batch:", self.expansion_batch_input)

        self.mold_id_combo = QComboBox()
        self.mold_id_combo.setProperty("class", "form-select")
        self.mold_id_combo.setMinimumHeight(36)
        trace_layout.addRow("Mold ID:", self.mold_id_combo)

        layout.addWidget(trace_group)

        # ── Material Consumed ───────────────────────────────────────────────
        material_group = QGroupBox("Material Consumed (optional)")
        material_group.setProperty("class", "form-group")
        material_layout = QFormLayout(material_group)
        material_layout.setSpacing(8)

        self.material_combo = QComboBox()
        self.material_combo.setProperty("class", "form-select")
        self.material_combo.setMinimumHeight(36)
        material_layout.addRow("Material:", self.material_combo)

        self.material_qty_spin = QDoubleSpinBox()
        self.material_qty_spin.setRange(0, 999999)
        self.material_qty_spin.setDecimals(3)
        self.material_qty_spin.setProperty("class", "form-input")
        self.material_qty_spin.setMinimumHeight(36)
        material_layout.addRow("Quantity:", self.material_qty_spin)

        layout.addWidget(material_group)

        # ── Notes ───────────────────────────────────────────────────────────
        notes_group = QGroupBox("Notes")
        notes_group.setProperty("class", "form-group")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any additional notes...")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setProperty("class", "form-input")
        notes_layout.addWidget(self.notes_input)

        layout.addWidget(notes_group)

        # ── Yield Summary ───────────────────────────────────────────────────
        self.yield_group = QGroupBox("Yield Summary")
        self.yield_group.setProperty("class", "form-section")
        self.yield_group.setVisible(False)
        yield_layout = QVBoxLayout(self.yield_group)

        self.yield_label = QLabel()
        self.yield_label.setProperty("class", "card-value")
        yield_layout.addWidget(self.yield_label)

        self.yield_progress = QProgressBar()
        self.yield_progress.setProperty("class", "progress-bar")
        self.yield_progress.setMaximumHeight(12)
        yield_layout.addWidget(self.yield_progress)

        layout.addWidget(self.yield_group)

        # ── Action Buttons ──────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.record_btn = QPushButton("Record Production")
        self.record_btn.setProperty("class", "primary")
        self.record_btn.setMinimumHeight(44)
        self.record_btn.clicked.connect(self._record_production)
        btn_layout.addWidget(self.record_btn)

        self.clear_btn = QPushButton("Clear Form")
        self.clear_btn.setProperty("class", "secondary")
        self.clear_btn.setMinimumHeight(44)
        self.clear_btn.clicked.connect(self._clear_form)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        return container

    def _build_history(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 0, 0, 0)

        header_row = QHBoxLayout()
        title = QLabel("Production History")
        title.setProperty("class", "section-header")
        header_row.addWidget(title)
        header_row.addStretch()

        self.filter_wo_input = QLineEdit()
        self.filter_wo_input.setPlaceholderText("Filter by WO...")
        self.filter_wo_input.setProperty("class", "form-input")
        self.filter_wo_input.setMaximumWidth(160)
        self.filter_wo_input.setMinimumHeight(32)
        header_row.addWidget(self.filter_wo_input)

        self.filter_type_combo = QComboBox()
        self.filter_type_combo.setProperty("class", "form-select")
        self.filter_type_combo.setMinimumHeight(32)
        for label, val in _OUTPUT_TYPE_FILTER_OPTIONS:
            self.filter_type_combo.addItem(label, val)
        header_row.addWidget(self.filter_type_combo)

        layout.addLayout(header_row)

        self.history_table = DataTableWithFilter()
        self.history_table.set_columns([
            {'key': 'timestamp', 'title': 'Date/Time', 'width': 130},
            {'key': 'work_order', 'title': 'Work Order', 'width': 100},
            {'key': 'output_type', 'title': 'Type', 'width': 110},
            {'key': 'quantity_produced', 'title': 'Produced', 'width': 80},
            {'key': 'quantity_scrapped', 'title': 'Scrapped', 'width': 80},
            {'key': 'yield_pct', 'title': 'Yield %', 'width': 70},
            {'key': 'density', 'title': 'Density', 'width': 70},
            {'key': 'operator_name', 'title': 'Operator', 'width': 110},
            {'key': 'station_id', 'title': 'Station', 'width': 90},
        ])
        layout.addWidget(self.history_table)

        return container

    # ── Signal Connections ─────────────────────────────────────────────────────

    def _setup_connections(self) -> None:
        self.controller.register_data_changed_callback(self._on_data_changed)
        self.controller.register_status_message_callback(self._on_status_message)

        self.output_type_combo.currentIndexChanged.connect(self._on_output_type_changed)
        self.filter_wo_input.textChanged.connect(self._debounce_timer.start)
        self.filter_type_combo.currentIndexChanged.connect(self._load_filtered_history)

    # ── Data Loading ───────────────────────────────────────────────────────────

    def _load_initial_data(self) -> None:
        self._load_work_orders()
        self._load_stations()
        self._load_mold_ids()
        self._load_materials()
        self._load_filtered_history()

    def _load_work_orders(self) -> None:
        try:
            self._work_orders = self.controller.get_active_work_orders()
            self.work_order_combo.clear()
            self.work_order_combo.addItem("Select Work Order...", "")
            for wo in self._work_orders:
                label = f"{wo['work_order_number']} — {wo['finished_good_name']}" if wo['finished_good_name'] else wo['work_order_number']
                self.work_order_combo.addItem(label, wo['work_order_number'])
        except Exception as e:
            logger.warning(f"Could not load work orders: {e}")
            self.work_order_combo.addItem("No work orders available", "")

    def _load_stations(self) -> None:
        try:
            stations = self.controller.get_stations_for_clock_in()
            self.station_combo.clear()
            self.station_combo.addItem("Select Station...", "")
            for s in stations:
                self.station_combo.addItem(f"{s['station_id']} — {s['name']}", s['station_id'])
        except Exception as e:
            logger.warning(f"Could not load stations: {e}")
            self.station_combo.addItem("No stations available", "")

    def _load_mold_ids(self) -> None:
        try:
            molds = self.controller.get_block_mold_stations()
            self.mold_id_combo.clear()
            self.mold_id_combo.addItem("None / N/A", "")
            for m in molds:
                self.mold_id_combo.addItem(f"{m['station_id']} — {m['name']}", m['station_id'])
        except Exception as e:
            logger.warning(f"Could not load mold stations: {e}")
            self.mold_id_combo.addItem("None / N/A", "")

    def _load_materials(self) -> None:
        try:
            self._materials = self.controller.get_materials_for_production()
            self.material_combo.clear()
            self.material_combo.addItem("None (no deduction)", "")
            for m in self._materials:
                uom = f" [{m['unit_of_measure']}]" if m['unit_of_measure'] else ""
                self.material_combo.addItem(f"{m['name']}{uom}", m['id'])
        except Exception as e:
            logger.warning(f"Could not load materials: {e}")
            self.material_combo.addItem("None", "")

    def _load_filtered_history(self) -> None:
        try:
            wo_filter = self.filter_wo_input.text().strip() or None
            type_filter = self.filter_type_combo.currentData() or None
            rows = self.controller.get_recent_production_outputs(
                days=30, work_order_number=wo_filter, output_type=type_filter
            )
            self.history_table.load_data(rows)
        except Exception as e:
            logger.error(f"Error loading production history: {e}")

    # ── Event Handlers ─────────────────────────────────────────────────────────

    def _on_output_type_changed(self) -> None:
        output_type = self.output_type_combo.currentData()
        self.foam_group.setVisible(output_type == "foam_block")

    def _on_data_changed(self) -> None:
        self._load_filtered_history()

    def _on_status_message(self, message: str, timeout: int) -> None:
        logger.info(f"Status: {message}")

    # ── Record Production ──────────────────────────────────────────────────────

    def _record_production(self) -> None:
        work_order_number = self.work_order_combo.currentData()
        if not work_order_number:
            show_error("Validation Error", "Please select a work order.", parent=self)
            return

        output_type = self.output_type_combo.currentData()
        if not output_type:
            show_error("Validation Error", "Please select an output type.", parent=self)
            return

        qty_produced = self.qty_produced_spin.value()
        if qty_produced <= 0:
            show_error("Validation Error", "Quantity produced must be greater than 0.", parent=self)
            return

        operator_name = self.operator_input.text().strip()
        if not operator_name:
            show_error("Validation Error", "Please enter the operator name.", parent=self)
            return

        qty_scrapped = self.qty_scrapped_spin.value()
        theoretical_yield = self.theoretical_yield_spin.value() or None
        station_id = self.station_combo.currentData() or None

        length = width = height = density = None
        if output_type == "foam_block":
            length = Decimal(str(self.length_spin.value())) if self.length_spin.value() else None
            width = Decimal(str(self.width_spin.value())) if self.width_spin.value() else None
            height = Decimal(str(self.height_spin.value())) if self.height_spin.value() else None
            density = Decimal(str(self.density_spin.value())) if self.density_spin.value() else None

        bead_lot_number = self.bead_lot_input.text().strip() or None
        expansion_batch = self.expansion_batch_input.text().strip() or None
        mold_id = self.mold_id_combo.currentData() or None
        notes = self.notes_input.toPlainText().strip() or None

        material_id = self.material_combo.currentData() or None
        material_qty = self.material_qty_spin.value() if material_id else 0

        try:
            self.controller.record_production_output(
                work_order_number=work_order_number,
                output_type=output_type,
                quantity_produced=qty_produced,
                operator_id=operator_name,
                operator_name=operator_name,
                station_id=station_id,
                quantity_scrapped=Decimal(str(qty_scrapped)),
                theoretical_yield=Decimal(str(theoretical_yield)) if theoretical_yield else None,
                length=length,
                width=width,
                height=height,
                density=density,
                bead_lot_number=bead_lot_number,
                expansion_batch=expansion_batch,
                mold_id=mold_id,
                notes=notes,
                material_id=material_id,
                material_quantity=material_qty,
            )
        except Exception as e:
            show_error("Save Failed", str(e), parent=self)
            return

        if theoretical_yield and theoretical_yield > 0:
            actual = qty_produced - qty_scrapped
            pct = (actual / theoretical_yield * 100)
            self.yield_label.setText(f"Yield: {actual:.2f} / {theoretical_yield:.2f} ({pct:.1f}%)")
            self.yield_progress.setValue(min(100, int(pct)))
            self.yield_group.setVisible(True)
        else:
            self.yield_group.setVisible(False)

        show_info("Saved", f"Recorded {qty_produced} units of {output_type.replace('_', ' ').title()} for {work_order_number}.", parent=self)
        self._clear_form()
        self._load_filtered_history()

    def _clear_form(self) -> None:
        self.work_order_combo.setCurrentIndex(0)
        self.output_type_combo.setCurrentIndex(0)
        self.station_combo.setCurrentIndex(0)
        self.operator_input.clear()
        self.qty_produced_spin.setValue(0)
        self.qty_scrapped_spin.setValue(0)
        self.theoretical_yield_spin.setValue(0)
        self.length_spin.setValue(0)
        self.width_spin.setValue(0)
        self.height_spin.setValue(0)
        self.density_spin.setValue(0)
        self.bead_lot_input.clear()
        self.expansion_batch_input.clear()
        self.mold_id_combo.setCurrentIndex(0)
        self.material_combo.setCurrentIndex(0)
        self.material_qty_spin.setValue(0)
        self.notes_input.clear()
        self.yield_group.setVisible(False)
