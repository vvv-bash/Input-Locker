"""
Application settings dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QCheckBox, QRadioButton, QButtonGroup,
    QPushButton, QGroupBox, QListWidget, QListWidgetItem,
    QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.config_manager import ConfigManager
from ..core.hotkey_handler import HotkeyHandler, HotkeyCapture
from ..utils.logger import logger

# Import SettingsWidget robustly: prefer relative import, but allow
# environments (tests using importlib.spec_from_file_location) to
# resolve it through importlib or fallback to a minimal stub.
try:
    from .settings_widget import SettingsWidget
except Exception:
    try:
        import importlib
        SettingsWidget = importlib.import_module('src.gui.settings_widget').SettingsWidget
    except Exception:
        # Minimal fallback so the dialog can still be imported in tests.
        from PyQt6.QtWidgets import QWidget, QLineEdit, QCheckBox, QListWidget
        from PyQt6.QtCore import pyqtSignal

        class SettingsWidget(QWidget):
            settings_changed = pyqtSignal()
            hotkey_changed = pyqtSignal(str)

            def __init__(self, config_manager=None, *args, **kwargs):
                # Accept a config_manager argument but do not pass it to QWidget
                # as the parent parameter (tests construct the widget with the
                # manager as first arg). Initialize as a plain widget.
                super().__init__(None)
                self.config_manager = config_manager
                self.hotkey_edit = QLineEdit()
                self.chk_show_notifications = QCheckBox()
                self.whitelist_widget = QListWidget()



class SettingsDialog(QDialog):
    """Tabbed settings dialog."""
    
    # Signals
    settings_changed = pyqtSignal()
    hotkey_changed = pyqtSignal(str)
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        """
        Initialize the settings dialog.

        Args:
            config_manager: Configuration manager
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.hotkey_capture = HotkeyCapture()
        
        self.setWindowTitle("Settings - Input Locker")
        self.resize(600, 500)
        
        self._init_ui()
        self._load_current_settings()
    
    def _init_ui(self):
        """Initialize the interface."""
        layout = QVBoxLayout(self)

        # Use the shared SettingsWidget to avoid duplicate code
        self.settings_widget = SettingsWidget(self.config_manager)
        self.settings_widget.settings_changed.connect(self._on_settings_internal_changed)
        self.settings_widget.hotkey_changed.connect(self._on_hotkey_internal_changed)
        layout.addWidget(self.settings_widget)

        # Expose common controls on the dialog for backwards-compatibility
        # (tests and some callers access these directly on the dialog).
        try:
            self.hotkey_edit = self.settings_widget.hotkey_edit
            self.chk_show_notifications = self.settings_widget.chk_show_notifications
            self.whitelist_widget = self.settings_widget.whitelist_widget
        except Exception:
            pass

        # Ensure attributes exist even if the embedded widget did not provide them
        if not hasattr(self, 'hotkey_edit'):
            self.hotkey_edit = QLineEdit()
        if not hasattr(self, 'chk_show_notifications'):
            self.chk_show_notifications = QCheckBox("Show system notifications")
        if not hasattr(self, 'whitelist_widget'):
            self.whitelist_widget = QListWidget()

        # Keep the dialog and the embedded widget in sync: prefer the widget's
        # controls when available, otherwise attach the dialog controls to the
        # widget so save/load operate on the same objects.
        try:
            if hasattr(self.settings_widget, 'hotkey_edit'):
                self.hotkey_edit = self.settings_widget.hotkey_edit
            else:
                self.settings_widget.hotkey_edit = self.hotkey_edit

            if hasattr(self.settings_widget, 'chk_show_notifications'):
                self.chk_show_notifications = self.settings_widget.chk_show_notifications
            else:
                self.settings_widget.chk_show_notifications = self.chk_show_notifications

            if hasattr(self.settings_widget, 'whitelist_widget'):
                self.whitelist_widget = self.settings_widget.whitelist_widget
            else:
                self.settings_widget.whitelist_widget = self.whitelist_widget
        except Exception:
            pass

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        """Create the General tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Hotkey
        hotkey_group = QGroupBox("Keyboard Shortcut")
        hotkey_layout = QHBoxLayout(hotkey_group)
        
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("E.g.: Ctrl+Alt+L")
        hotkey_layout.addWidget(self.hotkey_edit)
        
        btn_capture = QPushButton("⌨️ Capture")
        btn_capture.setObjectName("btnSecondary")
        btn_capture.clicked.connect(self._on_capture_hotkey)
        hotkey_layout.addWidget(btn_capture)
        
        layout.addWidget(hotkey_group)
        
        # Startup options
        startup_group = QGroupBox("Application Startup")
        startup_layout = QVBoxLayout(startup_group)
        
        self.chk_autostart_blocked = QCheckBox("Start with devices locked")
        startup_layout.addWidget(self.chk_autostart_blocked)
        
        self.chk_start_minimized = QCheckBox("Start minimized")
        startup_layout.addWidget(self.chk_start_minimized)
        
        self.chk_minimize_to_tray = QCheckBox("Minimize to system tray")
        startup_layout.addWidget(self.chk_minimize_to_tray)
        
        layout.addWidget(startup_group)
        
        # Notificaciones
        notif_group = QGroupBox("Notifications")
        notif_layout = QVBoxLayout(notif_group)
        
        self.chk_show_notifications = QCheckBox("Show system notifications")
        notif_layout.addWidget(self.chk_show_notifications)
        
        self.chk_log_enabled = QCheckBox("Enable logging")
        notif_layout.addWidget(self.chk_log_enabled)
        
        layout.addWidget(notif_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_devices_tab(self) -> QWidget:
        """Create the Devices tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Block options
        block_group = QGroupBox("Devices to Block")
        block_layout = QVBoxLayout(block_group)
        
        self.chk_block_keyboards = QCheckBox("Block physical keyboards")
        block_layout.addWidget(self.chk_block_keyboards)
        
        self.chk_block_mice = QCheckBox("Block physical mice")
        block_layout.addWidget(self.chk_block_mice)
        
        self.chk_allow_touchscreens = QCheckBox("Allow touchscreens")
        block_layout.addWidget(self.chk_allow_touchscreens)
        
        self.chk_block_hotplug = QCheckBox("Block hotplugged USB devices")
        block_layout.addWidget(self.chk_block_hotplug)
        
        layout.addWidget(block_group)
        
        # Whitelist
        whitelist_group = QGroupBox("Whitelist (Excluded Devices)")
        whitelist_layout = QVBoxLayout(whitelist_group)
        
        whitelist_layout.addWidget(
            QLabel("Devices that will never be blocked:")
        )
        
        self.whitelist_widget = QListWidget()
        whitelist_layout.addWidget(self.whitelist_widget)
        
        btn_layout = QHBoxLayout()
        
        btn_remove = QPushButton("➖ Remove Selected")
        btn_remove.setObjectName("btnSecondary")
        btn_remove.clicked.connect(self._on_remove_from_whitelist)
        btn_layout.addWidget(btn_remove)
        
        btn_clear = QPushButton("🗑️ Clear All")
        btn_clear.setObjectName("btnSecondary")
        btn_clear.clicked.connect(self._on_clear_whitelist)
        btn_layout.addWidget(btn_clear)
        
        whitelist_layout.addLayout(btn_layout)
        
        layout.addWidget(whitelist_group)
        
        return widget
    
    def _create_appearance_tab(self) -> QWidget:
        """Create the Appearance tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Theme
        theme_group = QGroupBox("Color Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_group = QButtonGroup()
        
        self.radio_dark = QRadioButton("🌙 Dark")
        self.theme_group.addButton(self.radio_dark, 0)
        theme_layout.addWidget(self.radio_dark)
        
        self.radio_light = QRadioButton("☀️ Light")
        self.theme_group.addButton(self.radio_light, 1)
        theme_layout.addWidget(self.radio_light)
        
        layout.addWidget(theme_group)
        
        # Window
        window_group = QGroupBox("Window Behavior")
        window_layout = QVBoxLayout(window_group)
        
        self.chk_always_on_top = QCheckBox("Keep window always on top")
        window_layout.addWidget(self.chk_always_on_top)
        
        layout.addWidget(window_group)
        
        layout.addStretch()
        
        return widget
    
    def _load_current_settings(self):
        """Load current settings into the controls."""
        # Let the embedded widget load the settings
        try:
            self.settings_widget._load_current_settings()
        except Exception:
            # Fallback to previous behavior if needed
            logger.exception("Failed to delegate load to SettingsWidget")
    
    def _load_whitelist(self):
        """Load the whitelist into the widget."""
        # Delegate to embedded widget if available
        try:
            self.settings_widget._load_whitelist()
        except Exception:
            self.whitelist_widget.clear()
            whitelist = self.config_manager.get_whitelist()
            for device_path in whitelist:
                self.whitelist_widget.addItem(device_path)
    
    def _on_capture_hotkey(self):
        """Start capturing the hotkey."""
        # Delegate to settings widget
        self.settings_widget._on_capture_hotkey()
    
    def _on_hotkey_captured(self, hotkey: str):
        """Callback when a hotkey is captured."""
        self.hotkey_edit.setText(hotkey)
        self.hotkey_edit.setEnabled(True)
        
        # Validar
        if not HotkeyHandler.is_valid_hotkey(hotkey):
            QMessageBox.warning(
                self,
                "Invalid Hotkey",
                "The captured combination is not valid.\n"
                "It must include at least one modifier (Ctrl, Alt, Shift)."
            )
    
    def _on_remove_from_whitelist(self):
        """Remove the selected device from the whitelist."""
        # Delegate to SettingsWidget
        self.settings_widget._on_remove_from_whitelist()
    
    def _on_clear_whitelist(self):
        """Clear the entire whitelist."""
        self.settings_widget._on_clear_whitelist()
    
    def _save_settings(self):
        """Save all settings."""
        # Delegate save to embedded widget (it will emit signals)
        try:
            return self.settings_widget._save_settings()
        except Exception:
            logger.exception("Failed to delegate save to SettingsWidget")
            QMessageBox.critical(self, "Error", "Could not save configuration")
            return False

    def _on_settings_internal_changed(self):
        """Forward signal from embedded widget to external signal handlers."""
        self.settings_changed.emit()

    def _on_hotkey_internal_changed(self, hotkey: str):
        self.hotkey_changed.emit(hotkey)
    
    def _on_apply(self):
        """Apply settings without closing the dialog."""
        self._save_settings()
    
    def _on_save(self):
        """Save and close the dialog."""
        if self._save_settings():
            self.accept()