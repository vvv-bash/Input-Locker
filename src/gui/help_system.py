"""
Help and documentation system with tooltips and contextual help.
"""
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from ..utils.logger import logger


class HelpTopic(Enum):
    """Available help topics."""
    OVERVIEW = "overview"
    DEVICES = "devices"
    BLOCKING = "blocking"
    HOTKEYS = "hotkeys"
    SETTINGS = "settings"
    THEMES = "themes"
    POWER_MANAGEMENT = "power_management"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class HelpContent:
    """Help content for a topic."""
    title: str
    description: str
    instructions: str
    tips: list
    related_topics: list


class HelpSystem:
    """System for managing help content and tooltips."""
    
    @staticmethod
    def get_tooltip(context: str) -> str:
        """Get a tooltip for a UI element."""
        tooltips = {
            "lock_button": "Lock selected devices (Ctrl+L)",
            "unlock_button": "Unlock all devices (Ctrl+U)",
            "refresh_button": "Refresh device list (F5)",
            "settings_button": "Open settings (Ctrl+,)",
        }
        return tooltips.get(context, "")


class HelpPanel(QFrame):
    """Sidebar panel for displaying help content."""
    
    def __init__(self):
        """Initialize the help panel."""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("❓ Help & Tips")
        title.setObjectName("lblSubtitle")
        layout.addWidget(title)

        body = QLabel(
            "Use the sidebar to navigate between Status, Devices, "
            "Settings, Analytics and Diagnostics.\n\n"
            "• Lock/Unlock: big button on the Status page or tray icon.\n"
            "• Hotkey: default Ctrl+Alt+L (configurable in Settings).\n"
            "• Devices: block specific keyboards/mice, whitelisting allowed.\n"
            "• Diagnostics: check dependencies and basic performance info."
        )
        body.setWordWrap(True)
        body.setObjectName("lblBody")
        layout.addWidget(body)

        layout.addStretch(1)
