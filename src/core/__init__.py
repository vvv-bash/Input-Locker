"""Core library surface for Input Locker.

This module exposes the main building blocks so the project can be
used as a reusable Python library without importing the GUI layer.

Typical usage from external code:

	from src.core import ConfigManager, DeviceManager

	cfg = ConfigManager()
	devices = DeviceManager().get_all_devices()

Only GUI-specific helpers live under :mod:`src.gui`; everything here is
safe to import from non‑Qt code (though some classes like
``InputBlocker`` still require PyQt6 to be installed).
"""

from .config_manager import ConfigManager
from .device_manager import DeviceManager, DeviceType, InputDeviceInfo
from .input_blocker import InputBlocker
from .hotkey_handler import HotkeyHandler

__all__ = [
	"ConfigManager",
	"DeviceManager",
	"DeviceType",
	"InputDeviceInfo",
	"InputBlocker",
	"HotkeyHandler",
]
