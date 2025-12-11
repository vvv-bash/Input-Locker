"""
Custom widget to display the device list.
"""

from PyQt6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QVBoxLayout,
    QLabel, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont

from ..core.device_manager import InputDeviceInfo, DeviceType
from ..utils.logger import logger


class DeviceItemWidget(QWidget):
    """Custom widget for each device item."""
    
    def __init__(self, device: InputDeviceInfo, is_blocked: bool, parent=None):
        """
        Initialize the item widget.

        Args:
            device: Device information
            is_blocked: Whether the device is blocked
            parent: Parent widget
        """
        super().__init__(parent)
        self.device = device
        self.is_blocked = is_blocked
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the item's UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        
        # Icono del dispositivo
        icon_label = QLabel(self.device.icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 18))
        icon_label.setFixedSize(30, 30)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Información del dispositivo
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Nombre del dispositivo
        name_label = QLabel(self.device.name)
        name_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        name_label.setWordWrap(False)
        info_layout.addWidget(name_label)
        
        # Detalles
        details = f"{self.device.device_type.value.title()} • {self.device.path}"
        details_label = QLabel(details)
        details_label.setStyleSheet("color: #888888; font-size: 9pt;")
        details_label.setWordWrap(False)
        info_layout.addWidget(details_label)
        
        layout.addLayout(info_layout, 1)
        
        # Estado
        status_label = QLabel("🔒 Blocked" if self.is_blocked else "✓ Allowed")
        status_label.setStyleSheet(
            f"color: {'#F44336' if self.is_blocked else '#4CAF50'}; "
            f"font-weight: bold; font-size: 10pt;"
        )
        status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(status_label)
        
        # Establecer altura mínima
        self.setMinimumHeight(60)
    
    def sizeHint(self):
        """Return the suggested size for the widget."""
        return QSize(self.width(), 60)


class DeviceListWidget(QWidget):
    """Widget to display and manage input devices."""
    
    # Signals
    device_selected = pyqtSignal(str)  # Emits the device path
    whitelist_requested = pyqtSignal(str)  # Request to add to whitelist
    selection_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        self.devices = []
        self.blocked_devices = set()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Detected Devices")
        title_label.setObjectName("lblSubtitle")
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold; padding: 5px;")
        layout.addWidget(title_label)
        
        # Device list
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSpacing(2)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        # Allow multi-selection for bulk actions
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        
        # Set uniform item height
        self.list_widget.setUniformItemSizes(False)
        
        # Styles for the list
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #333333;
                border-radius: 5px;
                background-color: #1E1E1E;
                outline: none;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
                margin: 2px 0px;
            }
            QListWidget::item:selected {
                background-color: #2D2D30;
                border-left: 3px solid #007ACC;
            }
            QListWidget::item:hover {
                background-color: #252526;
            }
            QListWidget::item:alternate {
                background-color: #1A1A1A;
            }
        """)
        
        layout.addWidget(self.list_widget)
        
        # Info footer
        self.info_label = QLabel("0 devices")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setObjectName("lblSubtitle")
        self.info_label.setStyleSheet("color: #888888; padding: 5px;")
        layout.addWidget(self.info_label)
    
    def update_devices(self, devices: list, blocked_devices: set):
        """
        Update the device list.

        Args:
            devices: List of InputDeviceInfo
            blocked_devices: Set of blocked device paths
        """
        self.devices = devices
        self.blocked_devices = blocked_devices
        
        # Clear list
        self.list_widget.clear()
        
        # Add devices
        for device in devices:
            self._add_device_item(device)
        
        # Update counter
        self.info_label.setText(f"{len(devices)} device(s) detected")

        logger.debug(f"Device list updated: {len(devices)} devices")
    
    def get_selected_device_paths(self) -> list:
        """Return a list of selected device paths."""
        selected = []
        for item in self.list_widget.selectedItems():
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                selected.append(path)
        return selected
    
    def _add_device_item(self, device: InputDeviceInfo):
        """
        Add a device to the list.

        Args:
            device: Device information
        """
        # Create item
        item = QListWidgetItem(self.list_widget)
        
        # Check if it's blocked
        is_blocked = device.path in self.blocked_devices
        
        # Create custom widget
        widget = DeviceItemWidget(device, is_blocked)
        
        # Set item size
        item.setSizeHint(QSize(self.list_widget.width() - 20, 60))
        
        # Add to the list
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        
        # Save reference to the device path
        item.setData(Qt.ItemDataRole.UserRole, device.path)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Callback when an item is clicked."""
        device_path = item.data(Qt.ItemDataRole.UserRole)
        if device_path:
            self.device_selected.emit(device_path)
            logger.debug(f"Device selected: {device_path}")

    def _on_selection_changed(self):
        """Emit selection_changed when the selection state changes."""
        self.selection_changed.emit()
    
    def get_selected_device_path(self) -> str:
        """Return the path of the selected device."""
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def clear(self):
        """Clear the device list."""
        self.list_widget.clear()
        self.devices = []
        self.blocked_devices = set()
        self.info_label.setText("0 devices")