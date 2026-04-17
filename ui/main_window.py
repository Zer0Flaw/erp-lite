"""
Main application window for XPanda ERP-Lite.
Features sidebar navigation, status bar, and module management.
"""

import logging
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QStackedWidget, QStatusBar, QLabel,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction, QKeySequence

from ui.components.sidebar import Sidebar
from ui.components.status_bar import StatusBar
from ui.themes.style_manager import StyleManager
from modules.inventory.views.inventory_dashboard import InventoryDashboard
from modules.inventory.views.material_detail import MaterialDetailView
from modules.inventory.views.receiving_log import ReceivingLogView

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""
    
    # Signals
    module_changed = pyqtSignal(str)
    status_message = pyqtSignal(str, int)  # message, timeout_ms
    
    def __init__(self, db_manager, settings):
        super().__init__()
        
        self.db_manager = db_manager
        self.settings = settings
        self.style_manager = StyleManager()
        
        # Module management
        self.current_module = None
        self.module_widgets: Dict[str, QWidget] = {}
        
        # UI components
        self.sidebar: Optional[Sidebar] = None
        self.content_stack: Optional[QStackedWidget] = None
        self.status_bar: Optional[StatusBar] = None
        
        # Setup window
        self.setup_window()
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.apply_theme()
        
        # Load initial module
        self.load_module('inventory')
        
        logger.info("Main window initialized")
    
    def setup_window(self) -> None:
        """Configure main window properties."""
        self.setWindowTitle(f"{self.settings.value('app/company_name', 'XPanda Foam')} - ERP-Lite")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        
        # Restore window geometry if available
        if self.settings.contains("mainwindow/geometry"):
            self.restoreGeometry(self.settings.value("mainwindow/geometry"))
        if self.settings.contains("mainwindow/state"):
            self.restoreState(self.settings.value("mainwindow/state"))
    
    def setup_ui(self) -> None:
        """Create and layout UI components."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable sidebar
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Setup sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.setMinimumWidth(250)
        self.sidebar.setMaximumWidth(350)
        splitter.addWidget(self.sidebar)
        
        # Setup content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Content stack for module views
        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(self.content_stack)
        
        splitter.addWidget(content_widget)
        
        # Set splitter proportions (sidebar:content = 1:4)
        splitter.setSizes([250, 1350])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # Setup status bar
        self.setup_status_bar()
    
    def setup_status_bar(self) -> None:
        """Create and configure the status bar."""
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)
        
        # Connect status message signal
        self.status_message.connect(self.status_bar.show_message)
        
        # Update status bar periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # Sidebar navigation
        if self.sidebar:
            self.sidebar.module_selected.connect(self.load_module)
            self.sidebar.settings_requested.connect(self.show_settings)
        
        # Window close event
        self.closeEvent = self.handle_close_event
    
    def setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # File menu shortcuts
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_record)
        self.addAction(new_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_current)
        self.addAction(save_action)
        
        find_action = QAction("Find", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self.search_current)
        self.addAction(find_action)
        
        # Escape to close dialogs
        escape_action = QAction("Escape", self)
        escape_action.setShortcut(QKeySequence.StandardKey.Cancel)
        escape_action.triggered.connect(self.escape_action)
        self.addAction(escape_action)
    
    def apply_theme(self) -> None:
        """Apply the current theme to the window."""
        theme_name = self.settings.value("app/theme", "default")
        self.style_manager.apply_theme(self, theme_name)
    
    def load_module(self, module_name: str) -> None:
        """
        Load and display a module.
        
        Args:
            module_name: Name of the module to load
        """
        try:
            # Check if module already loaded
            if module_name in self.module_widgets:
                self.content_stack.setCurrentWidget(self.module_widgets[module_name])
                self.current_module = module_name
                self.module_changed.emit(module_name)
                self.status_message.emit(f"Loaded {module_name.title()} module", 2000)
                return
            
            # Create module widget based on name
            module_widget = self.create_module_widget(module_name)
            
            if module_widget:
                # Add to stack and dictionary
                self.content_stack.addWidget(module_widget)
                self.module_widgets[module_name] = module_widget
                
                # Set as current widget
                self.content_stack.setCurrentWidget(module_widget)
                self.current_module = module_name
                self.module_changed.emit(module_name)
                
                self.status_message.emit(f"Loaded {module_name.title()} module", 2000)
                logger.info(f"Module {module_name} loaded successfully")
            else:
                self.status_message.emit(f"Failed to load {module_name} module", 3000)
                
        except Exception as e:
            logger.error(f"Error loading module {module_name}: {e}")
            self.status_message.emit(f"Error loading module: {e}", 3000)
    
    def create_module_widget(self, module_name: str) -> Optional[QWidget]:
        """
        Create a widget for the specified module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Module widget or None if creation failed
        """
        try:
            if module_name == 'inventory':
                return InventoryDashboard(self.db_manager, self.settings)
            elif module_name == 'inventory_detail':
                return MaterialDetailView(self.db_manager, self.settings)
            elif module_name == 'receiving':
                return ReceivingLogView(self.db_manager, self.settings)
            elif module_name == 'production':
                # Placeholder for production module
                widget = QWidget()
                layout = QVBoxLayout(widget)
                layout.addWidget(QLabel("Production Module - Coming Soon"))
                return widget
            elif module_name == 'orders':
                # Placeholder for orders module
                widget = QWidget()
                layout = QVBoxLayout(widget)
                layout.addWidget(QLabel("Orders Module - Coming Soon"))
                return widget
            elif module_name == 'quality':
                # Placeholder for quality module
                widget = QWidget()
                layout = QVBoxLayout(widget)
                layout.addWidget(QLabel("Quality Module - Coming Soon"))
                return widget
            else:
                logger.warning(f"Unknown module: {module_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating module widget for {module_name}: {e}")
            return None
    
    def update_status_bar(self) -> None:
        """Update status bar with current information."""
        if self.status_bar:
            # Update database connection status
            db_connected = self.db_manager.is_connected if self.db_manager else False
            self.status_bar.update_db_status(db_connected)
            
            # Update current module
            if self.current_module:
                self.status_bar.update_module(self.current_module)
    
    def show_settings(self) -> None:
        """Show the settings dialog."""
        try:
            from ui.components.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.settings, self)
            if dialog.exec() == 1:  # Accepted
                self.apply_theme()
                self.status_message.emit("Settings updated", 2000)
        except Exception as e:
            logger.error(f"Error showing settings: {e}")
            self.status_message.emit(f"Error opening settings: {e}", 3000)
    
    def new_record(self) -> None:
        """Handle new record shortcut."""
        if self.current_module and self.current_module in self.module_widgets:
            widget = self.module_widgets[self.current_module]
            if hasattr(widget, 'new_record'):
                widget.new_record()
    
    def save_current(self) -> None:
        """Handle save shortcut."""
        if self.current_module and self.current_module in self.module_widgets:
            widget = self.module_widgets[self.current_module]
            if hasattr(widget, 'save'):
                widget.save()
    
    def search_current(self) -> None:
        """Handle search shortcut."""
        if self.current_module and self.current_module in self.module_widgets:
            widget = self.module_widgets[self.current_module]
            if hasattr(widget, 'search'):
                widget.search()
    
    def escape_action(self) -> None:
        """Handle escape key."""
        # Close any active dialogs or cancel current operation
        if self.focusWidget():
            focused = self.focusWidget()
            if hasattr(focused, 'close'):
                focused.close()
    
    def auto_save(self) -> None:
        """Perform auto-save operations."""
        try:
            if self.current_module and self.current_module in self.module_widgets:
                widget = self.module_widgets[self.current_module]
                if hasattr(widget, 'auto_save'):
                    widget.auto_save()
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
    
    def handle_close_event(self, event) -> None:
        """Handle window close event."""
        try:
            # Save window geometry and state
            self.settings.setValue("mainwindow/geometry", self.saveGeometry())
            self.settings.setValue("mainwindow/state", self.saveState())
            
            # Perform cleanup
            if self.db_manager:
                self.db_manager.disconnect()
            
            logger.info("Application closed gracefully")
            event.accept()
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            event.accept()  # Still close even if cleanup fails
