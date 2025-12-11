"""
Embedded settings widget used by SettingsDialog and other callers.

Provides controls for general options, device whitelist and logging
settings (level, JSON/plain mode and rotation parameters). Applies
changes to the provided ConfigManager and the runtime `logger` API.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QListWidget, QGroupBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal
import logging

from ..core.config_manager import ConfigManager
from ..core.hotkey_handler import HotkeyCapture, HotkeyHandler
from ..utils.logger import logger


class SettingsWidget(QWidget):
    """A reusable settings widget exposing common controls."""

    settings_changed = pyqtSignal()
    hotkey_changed = pyqtSignal(str)

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.hotkey_capture = HotkeyCapture()
        self._init_ui()
        self._load_current_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Hotkey group
        hotkey_group = QGroupBox("Keyboard Shortcut")
        hk_layout = QHBoxLayout(hotkey_group)
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("E.g.: Ctrl+Alt+L")
        hk_layout.addWidget(self.hotkey_edit)

        btn_capture = QPushButton("⌨️ Capture")
        btn_capture.clicked.connect(self._on_capture_hotkey)
        hk_layout.addWidget(btn_capture)

        layout.addWidget(hotkey_group)

        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout(general_group)
        self.chk_show_notifications = QCheckBox("Show system notifications")
        self.chk_show_notifications.setChecked(True)
        general_layout.addWidget(self.chk_show_notifications)
        layout.addWidget(general_group)

        # Whitelist
        whitelist_group = QGroupBox("Whitelist (Excluded Devices)")
        wl_layout = QVBoxLayout(whitelist_group)
        wl_layout.addWidget(QLabel("Devices that will never be blocked:"))
        self.whitelist_widget = QListWidget()
        wl_layout.addWidget(self.whitelist_widget)

        btns = QHBoxLayout()
        btn_remove = QPushButton("➖ Remove Selected")
        btn_remove.clicked.connect(self._on_remove_from_whitelist)
        btns.addWidget(btn_remove)

        btn_clear = QPushButton("🗑️ Clear All")
        btn_clear.clicked.connect(self._on_clear_whitelist)
        btns.addWidget(btn_clear)

        wl_layout.addLayout(btns)
        layout.addWidget(whitelist_group)

        # Logging settings
        log_group = QGroupBox("Logging")
        log_layout = QVBoxLayout(log_group)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Level:"))
        self.log_level_combo = QComboBox()
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            self.log_level_combo.addItem(level)
        h1.addWidget(self.log_level_combo)
        log_layout.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Mode:"))
        self.log_mode_combo = QComboBox()
        self.log_mode_combo.addItems(["Plain", "JSON"])
        h2.addWidget(self.log_mode_combo)
        log_layout.addLayout(h2)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Rotate after (MB):"))
        self.log_max_mb_spin = QSpinBox()
        self.log_max_mb_spin.setRange(1, 10240)
        h3.addWidget(self.log_max_mb_spin)

        h3.addWidget(QLabel("Backups:"))
        self.log_backup_spin = QSpinBox()
        self.log_backup_spin.setRange(0, 100)
        h3.addWidget(self.log_backup_spin)

        log_layout.addLayout(h3)
        layout.addWidget(log_group)

        # Action buttons
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self._on_save)
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self._on_apply)
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_box.addWidget(btn_apply)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

        layout.addStretch()

    def _load_current_settings(self):
        try:
            hotkey = self.config_manager.get_hotkey()
            self.hotkey_edit.setText(hotkey)
        except Exception:
            pass

        try:
            self._load_whitelist()
        except Exception:
            pass

        try:
            level = self.config_manager.get('logging', 'level', 'INFO')
            idx = self.log_level_combo.findText(level.upper())
            if idx >= 0:
                self.log_level_combo.setCurrentIndex(idx)

            json_mode = self.config_manager.get('logging', 'json', False)
            self.log_mode_combo.setCurrentIndex(1 if json_mode else 0)

            rotation = self.config_manager.get_log_rotation()
            mb = int(rotation.get('max_bytes', 10 * 1024 * 1024) // (1024 * 1024))
            backups = int(rotation.get('backup_count', 5))
            self.log_max_mb_spin.setValue(max(1, mb))
            self.log_backup_spin.setValue(backups)
        except Exception:
            pass

    def _load_whitelist(self):
        self.whitelist_widget.clear()
        try:
            whitelist = self.config_manager.get_whitelist()
            for device_path in whitelist:
                self.whitelist_widget.addItem(device_path)
        except Exception:
            pass

    def _on_capture_hotkey(self):
        def cb(result: str):
            self.hotkey_edit.setText(result)
            self.hotkey_changed.emit(result)

        try:
            self.hotkey_capture.start_capture(cb)
        except Exception:
            logger.warning("Hotkey capture failed to start")

    def _on_remove_from_whitelist(self):
        items = self.whitelist_widget.selectedItems()
        for it in items:
            path = it.text()
            self.config_manager.remove_from_whitelist(path)
            self.whitelist_widget.takeItem(self.whitelist_widget.row(it))

    def _on_clear_whitelist(self):
        try:
            for item_index in range(self.whitelist_widget.count()-1, -1, -1):
                item = self.whitelist_widget.item(item_index)
                self.whitelist_widget.takeItem(item_index)
            self.config_manager.set('devices', 'whitelist', [])
            self.config_manager.save()
        except Exception:
            pass

    def _apply_logging_settings(self):
        level_name = self.log_level_combo.currentText()
        level = getattr(logging, level_name, logging.INFO)
        json_mode = (self.log_mode_combo.currentText() == 'JSON')
        max_mb = max(1, int(self.log_max_mb_spin.value()))
        max_bytes = max_mb * 1024 * 1024
        backups = int(self.log_backup_spin.value())

        self.config_manager.set('logging', 'level', level_name)
        self.config_manager.set('logging', 'json', bool(json_mode))
        self.config_manager.set_log_rotation(max_bytes, backups)

        try:
            logger.configure(level=level, json_format=json_mode)
            logger.reconfigure_rotation(max_bytes=max_bytes, backup_count=backups)
        except Exception:
            pass

    def _on_apply(self):
        self._save_settings()

    def _on_save(self):
        if self._save_settings():
            self.settings_changed.emit()

    def _save_settings(self) -> bool:
        try:
            hotkey = self.hotkey_edit.text().strip()
            if hotkey and HotkeyHandler.is_valid_hotkey(hotkey):
                self.config_manager.set_hotkey(hotkey)
                self.hotkey_changed.emit(hotkey)

            # Save notifications setting
            show_notif = self.chk_show_notifications.isChecked()
            self.config_manager.set('general', 'show_notifications', show_notif)

            self._apply_logging_settings()
            self.config_manager.save()
            return True
        except Exception:
            return False
