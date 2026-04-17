"""
Reusable data table component for XPanda ERP-Lite.
Provides a feature-rich table with sorting, filtering, and column management.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu,
    QCheckBox, QLineEdit, QHBoxLayout, QWidget, QLabel,
    QVBoxLayout, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont, QColor

logger = logging.getLogger(__name__)


class DataTable(QTableWidget):
    """
    Enhanced table widget with sorting, filtering, and column management.
    """
    
    # Signals
    row_double_clicked = pyqtSignal(int)
    selection_changed = pyqtSignal(list)
    filter_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.original_data: List[Dict[str, Any]] = []
        self.filtered_data: List[Dict[str, Any]] = []
        self.column_config: Dict[str, Dict[str, Any]] = {}
        self.visible_columns: List[str] = []
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self) -> None:
        """Configure table appearance and behavior."""
        # Table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.setSortingEnabled(True)
        
        # Header configuration
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Vertical header
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(25)
        
        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Styling is now handled by centralized StyleManager
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Header context menu
        self.horizontalHeader().customContextMenuRequested.connect(self._show_header_context_menu)
    
    def set_columns(self, columns: List[Dict[str, Any]]) -> None:
        """
        Configure table columns.
        
        Args:
            columns: List of column dictionaries with keys:
                     - key: Internal column key
                     - title: Display title
                     - width: Column width (optional)
                     - resizable: Whether column is resizable (default: True)
                     - sortable: Whether column is sortable (default: True)
                     - visible: Whether column is initially visible (default: True)
        """
        self.column_config = {}
        self.visible_columns = []
        
        # Set column count
        self.setColumnCount(len(columns))
        
        # Configure each column
        for i, col in enumerate(columns):
            key = col['key']
            title = col['title']
            
            # Store column configuration
            self.column_config[key] = {
                'title': title,
                'width': col.get('width'),
                'resizable': col.get('resizable', True),
                'sortable': col.get('sortable', True),
                'visible': col.get('visible', True),
                'index': i
            }
            
            # Set header title
            header_item = QTableWidgetItem(title)
            self.setHorizontalHeaderItem(i, header_item)
            
            # Set column width if specified
            if 'width' in col:
                self.setColumnWidth(i, col['width'])
            
            # Add to visible columns list
            if col.get('visible', True):
                self.visible_columns.append(key)
        
        # Update header resize modes
        header = self.horizontalHeader()
        for i, col in enumerate(columns):
            if not col.get('resizable', True):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
    
    def load_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Load data into the table.
        
        Args:
            data: List of data dictionaries
        """
        self.original_data = data.copy()
        self.filtered_data = data.copy()
        self._refresh_table()
    
    def filter_data(self, filter_text: str) -> None:
        """
        Filter table data based on search text.
        
        Args:
            filter_text: Text to filter by
        """
        if not filter_text.strip():
            self.filtered_data = self.original_data.copy()
        else:
            filter_text = filter_text.lower()
            self.filtered_data = []
            
            for row in self.original_data:
                # Check if any visible column contains the filter text
                match = False
                for col_key in self.visible_columns:
                    if col_key in row:
                        value = str(row[col_key]).lower()
                        if filter_text in value:
                            match = True
                            break
                
                if match:
                    self.filtered_data.append(row)
        
        self._refresh_table()
        self.filter_changed.emit(filter_text)
    
    def get_selected_rows(self) -> List[int]:
        """Get indices of selected rows."""
        selected_rows = []
        for item in self.selectedItems():
            row = item.row()
            if row not in selected_rows:
                selected_rows.append(row)
        return selected_rows
    
    def get_selected_data(self) -> List[Dict[str, Any]]:
        """Get data for selected rows."""
        selected_rows = self.get_selected_rows()
        return [self.filtered_data[row] for row in selected_rows if row < len(self.filtered_data)]
    
    def get_row_data(self, row: int) -> Optional[Dict[str, Any]]:
        """Get data for a specific row."""
        if 0 <= row < len(self.filtered_data):
            return self.filtered_data[row]
        return None
    
    def _refresh_table(self) -> None:
        """Refresh the table display with current filtered data."""
        # Set row count
        self.setRowCount(len(self.filtered_data))
        
        # Populate table
        for row_idx, row_data in enumerate(self.filtered_data):
            for col_key, col_config in self.column_config.items():
                if col_key in row_data and col_config['visible']:
                    col_idx = col_config['index']
                    value = row_data[col_key]
                    
                    # Create table item
                    item = QTableWidgetItem(str(value))
                    
                    # Apply styling based on value type or content
                    self._apply_item_styling(item, col_key, value)
                    
                    self.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.resizeColumnsToContents()
    
    def _apply_item_styling(self, item: QTableWidgetItem, column_key: str, value: Any) -> None:
        """Apply styling to table items based on content."""
        # Status-based styling
        if column_key == 'status':
            if value == 'Low Stock':
                item.setBackground(QColor('#F39C12'))
                item.setForeground(QColor('white'))
            elif value == 'Normal':
                item.setBackground(QColor('#27AE60'))
                item.setForeground(QColor('white'))
            elif value == 'Critical':
                item.setBackground(QColor('#E74C3C'))
                item.setForeground(QColor('white'))
        
        # Numeric formatting
        elif column_key in ['quantity', 'on_hand', 'available', 'reorder_point']:
            if isinstance(value, (int, float)):
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Currency formatting
        elif column_key in ['cost', 'value', 'total_value']:
            if isinstance(value, (int, float)):
                item.setText(f"${value:,.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    
    def _on_item_double_clicked(self, item) -> None:
        """Handle item double-click."""
        if item:
            self.row_double_clicked.emit(item.row())
    
    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        selected_data = self.get_selected_data()
        self.selection_changed.emit(selected_data)
    
    def _show_context_menu(self, position) -> None:
        """Show context menu for table rows."""
        if self.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        # Add common actions
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(lambda: self.load_data(self.original_data))
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        # Copy action
        copy_action = QAction("Copy Selected", self)
        copy_action.triggered.connect(self._copy_selected)
        menu.addAction(copy_action)
        
        # Export action
        export_action = QAction("Export to CSV", self)
        export_action.triggered.connect(self._export_to_csv)
        menu.addAction(export_action)
        
        menu.exec(self.mapToGlobal(position))
    
    def _show_header_context_menu(self, position) -> None:
        """Show context menu for column headers."""
        menu = QMenu(self)
        
        # Add column visibility toggles
        for col_key, col_config in self.column_config.items():
            action = QAction(col_config['title'], self)
            action.setCheckable(True)
            action.setChecked(col_config['visible'])
            action.triggered.connect(lambda checked, key=col_key: self._toggle_column_visibility(key))
            menu.addAction(action)
        
        menu.addSeparator()
        
        # Reset columns action
        reset_action = QAction("Reset Columns", self)
        reset_action.triggered.connect(self._reset_columns)
        menu.addAction(reset_action)
        
        menu.exec(self.horizontalHeader().mapToGlobal(position))
    
    def _toggle_column_visibility(self, column_key: str) -> None:
        """Toggle column visibility."""
        if column_key in self.column_config:
            col_config = self.column_config[column_key]
            col_config['visible'] = not col_config['visible']
            
            if col_config['visible']:
                self.showColumn(col_config['index'])
                if column_key not in self.visible_columns:
                    self.visible_columns.append(column_key)
            else:
                self.hideColumn(col_config['index'])
                if column_key in self.visible_columns:
                    self.visible_columns.remove(column_key)
            
            self._refresh_table()
    
    def _reset_columns(self) -> None:
        """Reset all columns to visible."""
        for col_key, col_config in self.column_config.items():
            col_config['visible'] = True
            self.showColumn(col_config['index'])
        
        self.visible_columns = list(self.column_config.keys())
        self._refresh_table()
    
    def _copy_selected(self) -> None:
        """Copy selected data to clipboard."""
        selected_data = self.get_selected_data()
        if not selected_data:
            return
        
        # Create tab-separated text
        lines = []
        
        # Header
        header = [self.column_config[key]['title'] for key in self.visible_columns if key in self.column_config]
        lines.append('\t'.join(header))
        
        # Data rows
        for row_data in selected_data:
            row = [str(row_data.get(key, '')) for key in self.visible_columns if key in self.column_config]
            lines.append('\t'.join(row))
        
        # Copy to clipboard
        clipboard_text = '\n'.join(lines)
        
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(clipboard_text)
    
    def _export_to_csv(self) -> None:
        """Export table data to CSV file."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                import csv
                
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Header
                    header = [self.column_config[key]['title'] for key in self.visible_columns if key in self.column_config]
                    writer.writerow(header)
                    
                    # Data rows
                    for row_data in self.filtered_data:
                        row = [row_data.get(key, '') for key in self.visible_columns if key in self.column_config]
                        writer.writerow(row)
                
                logger.info(f"Data exported to {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to export data: {e}")


class DataTableWithFilter(QWidget):
    """
    Data table with integrated search/filter controls.
    """
    
    # Signals
    row_double_clicked = pyqtSignal(int)
    selection_changed = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self) -> None:
        """Create UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Filter controls
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter...")
        filter_layout.addWidget(self.search_input)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setProperty("class", "secondary")
        filter_layout.addWidget(self.clear_button)
        
        filter_layout.addStretch()
        
        # Results count
        self.results_label = QLabel("0 records")
        filter_layout.addWidget(self.results_label)
        
        layout.addWidget(filter_widget)
        
        # Data table
        self.data_table = DataTable()
        layout.addWidget(self.data_table)
    
    def setup_connections(self) -> None:
        """Connect signals."""
        self.search_input.textChanged.connect(self._on_filter_changed)
        self.clear_button.clicked.connect(self._on_clear_filter)
        
        # Forward table signals
        self.data_table.row_double_clicked.connect(self.row_double_clicked.emit)
        self.data_table.selection_changed.connect(self.selection_changed.emit)
    
    def set_columns(self, columns: List[Dict[str, Any]]) -> None:
        """Set table columns."""
        self.data_table.set_columns(columns)
    
    def load_data(self, data: List[Dict[str, Any]]) -> None:
        """Load data into table."""
        self.data_table.load_data(data)
        self._update_results_count()
    
    def _on_filter_changed(self, text: str) -> None:
        """Handle filter text change."""
        self.data_table.filter_data(text)
        self._update_results_count()
    
    def _on_clear_filter(self) -> None:
        """Clear filter."""
        self.search_input.clear()
    
    def _update_results_count(self) -> None:
        """Update results count label."""
        count = self.data_table.rowCount()
        self.results_label.setText(f"{count} record{'s' if count != 1 else ''}")
    
    def get_selected_data(self) -> List[Dict[str, Any]]:
        """Get selected data."""
        return self.data_table.get_selected_data()
    
    def get_selected_rows(self) -> List[int]:
        """Get selected row indices."""
        return self.data_table.get_selected_rows()
