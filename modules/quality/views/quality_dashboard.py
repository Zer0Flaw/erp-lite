"""
Quality Dashboard view for XPanda ERP-Lite.
Displays quality summary, inspections, NCRs, and CAPAs.
"""

import logging
from typing import Optional
from uuid import UUID
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTableWithFilter
from ui.components.message_box import show_info, show_error, confirm_delete

logger = logging.getLogger(__name__)


class QualityDashboard(QWidget):
    """Main quality dashboard with summary cards and tables."""
    
    # Signals
    inspection_selected = pyqtSignal(str)
    ncr_selected = pyqtSignal(str)
    capa_selected = pyqtSignal(str)
    new_inspection_requested = pyqtSignal()
    new_ncr_requested = pyqtSignal()
    new_capa_requested = pyqtSignal()
    
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.settings = settings
        
        # UI components
        self.summary_cards: dict = {}
        self.inspections_table: Optional[DataTableWithFilter] = None
        self.ncrs_table: Optional[DataTableWithFilter] = None
        self.capas_table: Optional[DataTableWithFilter] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
        
        logger.debug("Quality dashboard initialized")
    
    def setup_ui(self) -> None:
        """Create and layout dashboard components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Quality Dashboard")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setProperty("class", "header")
        main_layout.addWidget(title_label)
        
        # Summary cards section
        self.setup_summary_cards(main_layout)
        
        # Tables section (vertical layout for better space utilization)
        tables_layout = QVBoxLayout()
        tables_layout.setSpacing(15)
        
        # Inspections table
        self.setup_inspections_table(tables_layout)
        
        # NCRs table
        self.setup_ncrs_table(tables_layout)
        
        # CAPAs table
        self.setup_capas_table(tables_layout)
        
        main_layout.addLayout(tables_layout)
        
        # Styling is now handled by centralized StyleManager
    
    def setup_summary_cards(self, parent_layout) -> None:
        """Create summary cards section."""
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Define summary cards
        card_configs = [
            {"title": "Pending Inspections", "value": "0", "color": "#3498DB"},
            {"title": "Open NCRs", "value": "0", "color": "#E74C3C"},
            {"title": "Active CAPAs", "value": "0", "color": "#F39C12"},
            {"title": "Quality Score", "value": "0%", "color": "#27AE60"}
        ]
        
        for config in card_configs:
            card = self.create_summary_card(config["title"], config["value"], config["color"])
            self.summary_cards[config["title"]] = card
            cards_layout.addWidget(card)
        
        cards_layout.addStretch()
        parent_layout.addLayout(cards_layout)
    
    def create_summary_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a summary card widget."""
        card = QFrame()
        card.setProperty("class", "summary-card")
        card.setMinimumSize(200, 100)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel(title)
        title_label.setProperty("class", "card-title")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setProperty("class", "card-value")
        layout.addWidget(value_label)
        
        return card
    
    def setup_inspections_table(self, parent_layout) -> None:
        """Create inspections table."""
        # Container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 10)
        
        # Table header
        header_label = QLabel("Recent Inspections")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setProperty("class", "subheader")
        table_layout.addWidget(header_label)
        
        # Data table with filter
        self.inspections_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'inspection_number', 'title': 'Inspection #', 'width': 100},
            {'key': 'inspection_type', 'title': 'Type', 'width': 100},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'material_sku', 'title': 'Material SKU', 'width': 120},
            {'key': 'batch_number', 'title': 'Batch', 'width': 80},
            {'key': 'inspector', 'title': 'Inspector', 'width': 100},
            {'key': 'overall_result', 'title': 'Result', 'width': 80},
            {'key': 'inspection_date', 'title': 'Date', 'width': 100}
        ]
        
        self.inspections_table.set_columns(columns)
        self.inspections_table.data_table.setMaximumHeight(200)
        
        table_layout.addWidget(self.inspections_table)
        parent_layout.addWidget(table_container)
    
    def setup_ncrs_table(self, parent_layout) -> None:
        """Create NCRs table."""
        # Container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 10)
        
        # Table header
        header_label = QLabel("Recent NCRs")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setProperty("class", "subheader")
        table_layout.addWidget(header_label)
        
        # Data table with filter
        self.ncrs_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'ncr_number', 'title': 'NCR #', 'width': 80},
            {'key': 'severity', 'title': 'Severity', 'width': 80},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'material_sku', 'title': 'Material SKU', 'width': 120},
            {'key': 'batch_number', 'title': 'Batch', 'width': 80},
            {'key': 'discovery_date', 'title': 'Discovery Date', 'width': 120},
            {'key': 'reported_by', 'title': 'Reported By', 'width': 100},
            {'key': 'days_open', 'title': 'Days Open', 'width': 80}
        ]
        
        self.ncrs_table.set_columns(columns)
        self.ncrs_table.data_table.setMaximumHeight(200)
        
        table_layout.addWidget(self.ncrs_table)
        parent_layout.addWidget(table_container)
    
    def setup_capas_table(self, parent_layout) -> None:
        """Create CAPAs table."""
        # Container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Table header
        header_label = QLabel("Recent CAPAs")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setProperty("class", "subheader")
        table_layout.addWidget(header_label)
        
        # Data table with filter
        self.capas_table = DataTableWithFilter()
        
        # Configure columns
        columns = [
            {'key': 'capa_number', 'title': 'CAPA #', 'width': 80},
            {'key': 'title', 'title': 'Title', 'resizable': True},
            {'key': 'status', 'title': 'Status', 'width': 100},
            {'key': 'priority', 'title': 'Priority', 'width': 80},
            {'key': 'assigned_to', 'title': 'Assigned To', 'width': 120},
            {'key': 'due_date', 'title': 'Due Date', 'width': 100},
            {'key': 'days_overdue', 'title': 'Days Overdue', 'width': 100}
        ]
        
        self.capas_table.set_columns(columns)
        self.capas_table.data_table.setMaximumHeight(200)
        
        table_layout.addWidget(self.capas_table)
        parent_layout.addWidget(table_container)
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        if self.inspections_table:
            self.inspections_table.row_double_clicked.connect(self.on_inspection_double_clicked)
        
        if self.ncrs_table:
            self.ncrs_table.row_double_clicked.connect(self.on_ncr_double_clicked)
        
        if self.capas_table:
            self.capas_table.row_double_clicked.connect(self.on_capa_double_clicked)
    
    def load_data(self) -> None:
        """Load dashboard data from database."""
        try:
            # Load summary data
            self.load_summary_data()
            
            # Load inspections
            self.load_inspections()
            
            # Load NCRs
            self.load_ncrs()
            
            # Load CAPAs
            self.load_capas()
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}")
    
    def load_summary_data(self) -> None:
        """Load summary statistics."""
        # Placeholder data - will be replaced with actual database queries
        summary_data = {
            "Pending Inspections": "3",
            "Open NCRs": "2", 
            "Active CAPAs": "4",
            "Quality Score": "96.5%"
        }
        
        for title, value in summary_data.items():
            if title in self.summary_cards:
                card = self.summary_cards[title]
                # Update the value label (second child)
                if card.layout().count() >= 2:
                    value_label = card.layout().itemAt(1).widget()
                    if isinstance(value_label, QLabel):
                        value_label.setText(str(value))
    
    def load_inspections(self) -> None:
        """Load inspections into table."""
        if not self.inspections_table:
            return
        
        try:
            # Placeholder data - will be replaced with actual database query
            inspections_data = [
                {
                    'inspection_number': 'INSP-001',
                    'inspection_type': 'Incoming',
                    'status': 'Completed',
                    'material_sku': 'EPS-BLOCK-001',
                    'batch_number': 'BATCH-001',
                    'inspector': 'John Smith',
                    'overall_result': 'PASS',
                    'inspection_date': '2024-04-15'
                },
                {
                    'inspection_number': 'INSP-002',
                    'inspection_type': 'In Process',
                    'status': 'In Progress',
                    'material_sku': 'EPS-BLOCK-002',
                    'batch_number': 'BATCH-002',
                    'inspector': 'Jane Doe',
                    'overall_result': 'FAIL',
                    'inspection_date': '2024-04-16'
                },
                {
                    'inspection_number': 'INSP-003',
                    'inspection_type': 'Final',
                    'status': 'Scheduled',
                    'material_sku': 'EPS-BEAD-001',
                    'batch_number': 'BATCH-003',
                    'inspector': 'Bob Wilson',
                    'overall_result': '',
                    'inspection_date': '2024-04-17'
                }
            ]
            
            # Load into table
            self.inspections_table.load_data(inspections_data)
            
        except Exception as e:
            logger.error(f"Error loading inspections: {e}")
    
    def load_ncrs(self) -> None:
        """Load NCRs into table."""
        if not self.ncrs_table:
            return
        
        try:
            # Placeholder data - will be replaced with actual database query
            ncrs_data = [
                {
                    'ncr_number': 'NCR-001',
                    'severity': 'Major',
                    'status': 'Open',
                    'material_sku': 'EPS-BLOCK-002',
                    'batch_number': 'BATCH-002',
                    'discovery_date': '2024-04-16',
                    'reported_by': 'Jane Doe',
                    'days_open': 1
                },
                {
                    'ncr_number': 'NCR-002',
                    'severity': 'Critical',
                    'status': 'Under Investigation',
                    'material_sku': 'EPS-BLOCK-003',
                    'batch_number': 'BATCH-004',
                    'discovery_date': '2024-04-15',
                    'reported_by': 'John Smith',
                    'days_open': 2
                }
            ]
            
            # Load into table
            self.ncrs_table.load_data(ncrs_data)
            
        except Exception as e:
            logger.error(f"Error loading NCRs: {e}")
    
    def load_capas(self) -> None:
        """Load CAPAs into table."""
        if not self.capas_table:
            return
        
        try:
            # Placeholder data - will be replaced with actual database query
            capas_data = [
                {
                    'capa_number': 'CAPA-001',
                    'title': 'Improve incoming inspection process',
                    'status': 'In Progress',
                    'priority': 'High',
                    'assigned_to': 'Quality Manager',
                    'due_date': '2024-04-20',
                    'days_overdue': 0
                },
                {
                    'capa_number': 'CAPA-002',
                    'title': 'Address material quality issues',
                    'status': 'Open',
                    'priority': 'Medium',
                    'assigned_to': 'Production Manager',
                    'due_date': '2024-04-25',
                    'days_overdue': 0
                }
            ]
            
            # Load into table
            self.capas_table.load_data(capas_data)
            
        except Exception as e:
            logger.error(f"Error loading CAPAs: {e}")
    
    def on_inspection_double_clicked(self, row: int) -> None:
        """Handle double-click on inspection."""
        if self.inspections_table:
            selected_data = self.inspections_table.get_selected_data()
            if selected_data:
                inspection = selected_data[0]
                self.inspection_selected.emit(inspection.get('inspection_number', ''))
    
    def on_ncr_double_clicked(self, row: int) -> None:
        """Handle double-click on NCR."""
        if self.ncrs_table:
            selected_data = self.ncrs_table.get_selected_data()
            if selected_data:
                ncr = selected_data[0]
                self.ncr_selected.emit(ncr.get('ncr_number', ''))
    
    def on_capa_double_clicked(self, row: int) -> None:
        """Handle double-click on CAPA."""
        if self.capas_table:
            selected_data = self.capas_table.get_selected_data()
            if selected_data:
                capa = selected_data[0]
                self.capa_selected.emit(capa.get('capa_number', ''))
    
    def refresh_data(self) -> None:
        """Refresh all dashboard data."""
        self.load_data()
    
    def new_record(self) -> None:
        """Handle new record action."""
        self.new_inspection_requested.emit()
    
    def save(self) -> None:
        """Handle save action."""
        # Dashboard doesn't have editable data
        pass
    
    def search(self) -> None:
        """Handle search action."""
        if self.inspections_table:
            self.inspections_table.search_input.setFocus()
            self.inspections_table.search_input.selectAll()
    
    def auto_save(self) -> None:
        """Handle auto-save (not applicable to dashboard)."""
        pass
