"""
Inventory Dashboard view for XPanda ERP-Lite.
Displays inventory summary, low stock alerts, and recent activity.
"""

import logging
from typing import Optional
from uuid import UUID
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete
from ui.components.form_dialog import MaterialFormDialog, ReceivingFormDialog
from modules.inventory.controllers.inventory_controller import InventoryController
from modules.inventory.views.material_detail import MaterialDetailView

logger = logging.getLogger(__name__)


class InventoryDashboard(QWidget):
    """Main inventory dashboard with summary cards and tables."""
    
    # Signals
    material_selected = pyqtSignal(str)
    new_material_requested = pyqtSignal()
    receiving_requested = pyqtSignal()
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        self.controller = InventoryController(db_manager)
        
        # UI components
        self.summary_cards: dict = {}
        self.inventory_table: Optional[DataTableWithFilter] = None
        self.recent_activity_table: Optional[DataTableWithFilter] = None
        
        self.setup_ui()
        self.setup_connections()
        self.setup_controller_callbacks()
        self.load_data()
        
        logger.debug("Inventory dashboard initialized")
    
    def setup_ui(self) -> None:
        """Create and layout dashboard components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self.setup_header(main_layout)
        
        # Summary cards
        self.setup_summary_cards(main_layout)
        
        # Content area with tables
        content_layout = QHBoxLayout()
        
        # Inventory table (left side)
        self.setup_inventory_table(content_layout)
        
        # Recent activity table (right side)
        self.setup_recent_activity_table(content_layout)
        
        main_layout.addLayout(content_layout)
    
    def setup_header(self, parent_layout) -> None:
        """Create dashboard header."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Inventory Dashboard")
        title.setProperty("class", "page-header")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Action buttons
        new_material_btn = QPushButton("New Material")
        new_material_btn.setProperty("class", "primary")
        new_material_btn.clicked.connect(self.create_new_material)
        header_layout.addWidget(new_material_btn)

        self.edit_material_btn = QPushButton("Edit Material")
        self.edit_material_btn.setProperty("class", "secondary")
        self.edit_material_btn.clicked.connect(self.edit_selected_material)
        header_layout.addWidget(self.edit_material_btn)

        self.delete_material_btn = QPushButton("Delete Material")
        self.delete_material_btn.setProperty("class", "danger")
        self.delete_material_btn.clicked.connect(self.delete_selected_material)
        header_layout.addWidget(self.delete_material_btn)

        receiving_btn = QPushButton("Receive Materials")
        receiving_btn.setProperty("class", "accent")
        receiving_btn.clicked.connect(self.open_receiving_dialog)
        header_layout.addWidget(receiving_btn)

        parent_layout.addWidget(header_widget)
    
    def setup_summary_cards(self, parent_layout) -> None:
        """Create summary cards widget."""
        cards_widget = QWidget()
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(15)
        
        # Create cards
        cards = [
            ("Total SKUs", "0", "#3498DB"),
            ("Low Stock Items", "0", "#E74C3C"),
            ("Total Value", "$0.00", "#27AE60"),
            ("Recent Receiving", "0", "#F39C12"),
        ]
        
        for title, value, color in cards:
            card = self.create_summary_card(title, value, color)
            cards_layout.addWidget(card)
            self.summary_cards[title] = card
        
        cards_layout.addStretch()
        parent_layout.addWidget(cards_widget)
    
    def create_summary_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a summary card widget."""
        card = QFrame()
        card.setProperty("class", "summary-card")
        if color == "#3498DB":
            card.setProperty("accent", "primary")
        elif color == "#27AE60":
            card.setProperty("accent", "success")
        elif color == "#F39C12":
            card.setProperty("accent", "warning")
        elif color == "#E74C3C":
            card.setProperty("accent", "danger")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Category label
        category_label = QLabel(title.upper())
        category_label.setProperty("class", "card-category")
        layout.addWidget(category_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setProperty("class", "card-value")
        layout.addWidget(value_label)
        
        return card
    
    def setup_inventory_table(self, parent_layout) -> None:
        """Create inventory materials table."""
        # Container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 10, 0)
        
        # Table header
        header_label = QLabel("Inventory Items")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setProperty("class", "subheader")
        table_layout.addWidget(header_label)
        
        # Data table with filter
        self.inventory_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'sku', 'title': 'SKU', 'width': 120},
            {'key': 'description', 'title': 'Description', 'resizable': True},
            {'key': 'category', 'title': 'Category', 'width': 120},
            {'key': 'on_hand', 'title': 'On Hand', 'width': 80},
            {'key': 'available', 'title': 'Available', 'width': 80},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'storage_location', 'title': 'Location', 'width': 100}
        ]
        
        self.inventory_table.set_columns(columns)
        table_layout.addWidget(self.inventory_table)
        parent_layout.addWidget(table_container)
    
    def setup_recent_activity_table(self, parent_layout) -> None:
        """Create recent activity table."""
        # Container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(10, 0, 0, 0)
        
        # Table header
        header_label = QLabel("Recent Activity")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setProperty("class", "subheader")
        table_layout.addWidget(header_label)
        
        # Data table with filter
        self.recent_activity_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'date', 'title': 'Date', 'width': 100},
            {'key': 'type', 'title': 'Action', 'width': 120},
            {'key': 'material_sku', 'title': 'Material', 'resizable': True},
            {'key': 'quantity', 'title': 'Quantity', 'width': 80},
            {'key': 'reference', 'title': 'Reference', 'width': 100}
        ]
        
        self.recent_activity_table.set_columns(columns)
        self.recent_activity_table.data_table.setMaximumHeight(250)
        
        table_layout.addWidget(self.recent_activity_table)
        parent_layout.addWidget(table_container)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        if self.inventory_table:
            self.inventory_table.row_double_clicked.connect(self.on_material_double_clicked)
    
    def setup_controller_callbacks(self) -> None:
        """Setup callbacks for controller notifications."""
        self.controller.register_data_changed_callback(self.on_data_changed)
        self.controller.register_status_message_callback(self.on_status_message)
    
    def load_data(self) -> None:
        """Load dashboard data from database."""
        try:
            # Load summary data
            self.load_summary_data()
            
            # Load inventory items
            self.load_inventory_items()
            
            # Load recent activity
            self.load_recent_activity()
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}")
    
    def on_data_changed(self) -> None:
        """Handle data change notifications."""
        self.load_data()
    
    def on_status_message(self, message: str, timeout: int) -> None:
        """Handle status message notifications."""
        # This would be handled by the main window's status bar
        logger.info(f"Status: {message}")
    
    def on_material_double_clicked(self, row: int) -> None:
        """Handle double-click on inventory item — open detail dialog."""
        if self.inventory_table:
            selected_data = self.inventory_table.get_selected_data()
            if selected_data:
                material_id = selected_data[0].get('id', '')
                if material_id:
                    self.show_material_detail(material_id)
    
    def load_summary_data(self) -> None:
        """Load summary statistics."""
        try:
            dashboard_data = self.controller.get_dashboard_data()
            summary_cards = dashboard_data.get('summary_cards', {})
            
            # Update summary cards
            card_mappings = {
                "Total SKUs": summary_cards.get('total_skus', 0),
                "Low Stock Items": summary_cards.get('low_stock_items', 0),
                "Total Value": summary_cards.get('total_value', "$0.00"),
                "Recent Receiving": summary_cards.get('recent_receiving', 0)
            }
            
            for title, value in card_mappings.items():
                if title in self.summary_cards:
                    card = self.summary_cards[title]
                    # Update the value label (second child)
                    if card.layout().count() >= 2:
                        value_label = card.layout().itemAt(1).widget()
                        if isinstance(value_label, QLabel):
                            value_label.setText(str(value))
        except Exception as e:
            logger.error(f"Error loading summary data: {e}")
    
    def load_inventory_items(self) -> None:
        """Load inventory items into table."""
        if not self.inventory_table:
            return

        try:
            items = self.controller.search_inventory("", None)
            self.inventory_table.load_data(items)
        except Exception as e:
            logger.error(f"Error loading inventory items: {e}")
    
    def load_recent_activity(self) -> None:
        """Load recent activity into table."""
        if not self.recent_activity_table:
            return
        
        try:
            # Get recent transactions from controller
            transactions = self.controller.get_recent_transactions(50)
            
            # Load into table
            self.recent_activity_table.load_data(transactions)
            
        except Exception as e:
            logger.error(f"Error loading recent activity: {e}")
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.create_new_material()
    
    def save(self) -> None:
        """Handle save action."""
        # Dashboard doesn't have editable data
        pass
    
    def search(self) -> None:
        """Handle search action."""
        if self.inventory_table:
            self.inventory_table.search_input.setFocus()
            self.inventory_table.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save (not applicable to dashboard)."""
        pass
    
    def create_new_material(self) -> None:
        """Create a new material using the form dialog."""
        try:
            dialog = MaterialFormDialog(parent=self)
            
            if dialog.exec() == 1:  # Accepted
                material_data = dialog.get_material_data()
                material_data['created_by'] = 'System'  # Would get from user session
                
                success, message = self.controller.create_material(material_data)
                
                if success:
                    show_info("Success", message)
                else:
                    show_error("Error", message)
                    
        except Exception as e:
            logger.error(f"Error creating material dialog: {e}")
            show_error("Error", f"Failed to open material form: {e}")
    
    def edit_selected_material(self) -> None:
        """Edit the selected material."""
        try:
            selected_data = self.inventory_table.get_selected_data()
            if not selected_data:
                show_info("No Selection", "Please select a material to edit.")
                return
            
            material = selected_data[0]
            material_id = UUID(material['id'])
            
            # Get full material data
            material_data = self.controller.get_material_by_id(material_id)
            if not material_data:
                show_error("Error", "Material not found.")
                return
            
            # Open edit dialog
            dialog = MaterialFormDialog(material_data, parent=self)
            
            if dialog.exec() == 1:  # Accepted
                updated_data = dialog.get_material_data()
                success, message = self.controller.update_material(material_id, updated_data)
                
                if success:
                    show_info("Success", message)
                else:
                    show_error("Error", message)
                    
        except Exception as e:
            logger.error(f"Error editing material: {e}")
            show_error("Error", f"Failed to edit material: {e}")
    
    def delete_selected_material(self) -> None:
        """Delete the selected material."""
        try:
            selected_data = self.inventory_table.get_selected_data()
            if not selected_data:
                show_info("No Selection", "Please select a material to delete.")
                return
            
            material = selected_data[0]
            
            # Confirm deletion
            if confirm_delete("Material", f"{material['sku']} - {material['description']}", self):
                material_id = UUID(material['id'])
                success, message = self.controller.delete_material(material_id, 'System')
                
                if success:
                    show_info("Success", message)
                else:
                    show_error("Error", message)
                    
        except Exception as e:
            logger.error(f"Error deleting material: {e}")
            show_error("Error", f"Failed to delete material: {e}")
    
        
    def open_receiving_dialog(self) -> None:
        """Open the Receive Materials form dialog."""
        try:
            material_options = self.controller.get_material_options()
            if not material_options:
                show_info("No Materials", "Add materials before logging a receipt.")
                return

            dialog = ReceivingFormDialog(material_options, parent=self)

            if dialog.exec() == 1:
                transaction_data = dialog.get_receiving_data()

                if not transaction_data.get('material_id'):
                    show_error("Error", "No material selected.")
                    return

                # Controller expects UUID, not string
                transaction_data['material_id'] = UUID(transaction_data['material_id'])

                success, message = self.controller.create_receiving_transaction(transaction_data)

                if success:
                    show_info("Success", message)
                else:
                    show_error("Error", message)

        except Exception as e:
            logger.error(f"Error opening receiving dialog: {e}")
            show_error("Error", f"Failed to open receiving form: {e}")

    def show_material_detail(self, material_id: str) -> None:
        """Open MaterialDetailView in a modal dialog for the given material ID."""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Material Details")
            dialog.resize(900, 660)
            dialog.setModal(True)

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)

            detail_view = MaterialDetailView(self.db_manager, self.settings, parent=dialog)
            detail_view.back_to_dashboard.connect(dialog.accept)
            layout.addWidget(detail_view)

            detail_view.load_material(material_id)
            dialog.exec()

        except Exception as e:
            logger.error(f"Error opening material detail: {e}")
            show_error("Error", f"Failed to open material details: {e}")

    def refresh_data(self) -> None:
        """Refresh all dashboard data."""
        self.load_data()
