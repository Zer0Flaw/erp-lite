"""
Material Detail view for XPanda ERP-Lite.
Displays detailed information about a specific material and its transaction history.
"""

import logging
from typing import Optional
from uuid import UUID
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QScrollArea, QGroupBox, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from modules.inventory.controllers.inventory_controller import InventoryController

logger = logging.getLogger(__name__)


class MaterialDetailView(QWidget):
    """Detailed view of a single material with real-time stock and transaction data."""

    back_to_dashboard = pyqtSignal()
    edit_material = pyqtSignal(str)

    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)

        self.db_manager = db_manager
        self.settings = settings
        self.current_material_id: Optional[str] = None
        self.controller = InventoryController(db_manager)

        self.info_labels: dict = {}
        self.stock_labels: dict = {}
        self.history_table: Optional[QTableWidget] = None

        self.setup_ui()

        logger.debug("Material detail view initialized")

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self._setup_header(main_layout)

        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        self._setup_material_info(content_layout)
        self._setup_stock_info(content_layout)
        self._setup_transaction_history(content_layout)

        content_scroll.setWidget(content_widget)
        main_layout.addWidget(content_scroll)

    def _setup_header(self, parent_layout) -> None:
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("Material Details")
        self.title_label.setProperty("class", "page-header")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "secondary")
        close_btn.clicked.connect(self.back_to_dashboard.emit)
        header_layout.addWidget(close_btn)

        edit_btn = QPushButton("Edit Material")
        edit_btn.setProperty("class", "primary")
        edit_btn.clicked.connect(self._on_edit_clicked)
        header_layout.addWidget(edit_btn)

        parent_layout.addWidget(header_widget)

    def _setup_material_info(self, parent_layout) -> None:
        group = QGroupBox("Material Information")
        group_layout = QHBoxLayout(group)

        left_fields = [
            ("SKU",              "sku"),
            ("Name",             "name"),
            ("Description",      "description"),
            ("Category",         "category"),
            ("Unit of Measure",  "unit_of_measure"),
        ]
        right_fields = [
            ("Reorder Point",    "reorder_point"),
            ("Storage Location", "storage_location"),
            ("Preferred Supplier","preferred_supplier"),
            ("Standard Cost",    "standard_cost"),
            ("Notes",            "notes"),
        ]

        for field_list in (left_fields, right_fields):
            col_widget = QWidget()
            col_layout = QVBoxLayout(col_widget)
            col_layout.setContentsMargins(0, 0, 16, 0)
            col_layout.setSpacing(8)

            for label_text, key in field_list:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)

                lbl = QLabel(f"{label_text}:")
                lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                lbl.setFixedWidth(140)
                row_layout.addWidget(lbl)

                val = QLabel("\u2014")
                val.setProperty("class", "info-value")
                val.setWordWrap(True)
                row_layout.addWidget(val, 1)

                self.info_labels[key] = val
                col_layout.addWidget(row_widget)

            col_layout.addStretch()
            group_layout.addWidget(col_widget)

        parent_layout.addWidget(group)

    def _setup_stock_info(self, parent_layout) -> None:
        group = QGroupBox("Current Stock")
        group_layout = QHBoxLayout(group)
        group_layout.setSpacing(16)

        stock_fields = [
            ("On Hand",    "on_hand"),
            ("Available",  "available"),
            ("Committed",  "committed"),
            ("Total Value","total_value"),
        ]

        for label_text, key in stock_fields:
            card = QWidget()
            card.setProperty("class", "summary-card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)

            lbl = QLabel(label_text.upper())
            lbl.setProperty("class", "card-category")
            card_layout.addWidget(lbl)

            val = QLabel("\u2014")
            val.setProperty("class", "card-value")
            card_layout.addWidget(val)

            self.stock_labels[key] = val
            group_layout.addWidget(card)

        group_layout.addStretch()
        parent_layout.addWidget(group)

    def _setup_transaction_history(self, parent_layout) -> None:
        group = QGroupBox("Transaction History")
        group_layout = QVBoxLayout(group)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["Date", "Type", "Quantity", "Reference", "Lot Number", "Notes"]
        )
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSortingEnabled(True)

        hdr = self.history_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        group_layout.addWidget(self.history_table)
        parent_layout.addWidget(group)

    def load_material(self, material_id: str) -> None:
        """Load and display a material by its UUID string."""
        self.current_material_id = material_id

        try:
            uid = UUID(material_id)
        except (ValueError, AttributeError) as e:
            logger.error(f"Invalid material ID: {material_id} — {e}")
            return

        self._load_material_info(uid)
        self._load_stock_info(uid)
        self._load_transaction_history(uid)

    def _load_material_info(self, uid: UUID) -> None:
        material = self.controller.get_material_by_id(uid)
        if not material:
            return

        self.title_label.setText(f"Material \u2014 {material['sku']}")

        for key, label in self.info_labels.items():
            value = material.get(key)
            if value is None or value == '':
                label.setText("\u2014")
            elif key == 'standard_cost' and value is not None:
                label.setText(f"${float(value):,.4f}")
            else:
                label.setText(str(value))

    def _load_stock_info(self, uid: UUID) -> None:
        summary = self.controller.get_inventory_summary(uid)
        if not summary:
            return

        inv = summary.get('inventory', {})
        mat = summary.get('material', {})
        uom = mat.get('unit_of_measure', '')

        self.stock_labels['on_hand'].setText(f"{inv.get('on_hand', 0):,.4f} {uom}".strip())
        self.stock_labels['available'].setText(f"{inv.get('available', 0):,.4f} {uom}".strip())
        self.stock_labels['committed'].setText(f"{inv.get('committed', 0):,.4f} {uom}".strip())
        self.stock_labels['total_value'].setText(f"${inv.get('total_value', 0):,.2f}")

    def _load_transaction_history(self, uid: UUID) -> None:
        if not self.history_table:
            return

        self.history_table.setRowCount(0)
        transactions = self.controller.get_material_transactions(uid)

        for txn in transactions:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            for col, value in enumerate([
                txn['date'],
                txn['type'],
                f"{txn['quantity']:+,.4f}",
                txn['reference'],
                txn['lot_number'],
                txn['notes'],
            ]):
                self.history_table.setItem(row, col, QTableWidgetItem(str(value)))

    def _on_edit_clicked(self) -> None:
        if self.current_material_id:
            self.edit_material.emit(self.current_material_id)

    # Standard module interface stubs
    def new_record(self) -> None: pass
    def save(self) -> None: pass
    def search(self) -> None: pass
    def auto_save(self) -> None: pass
