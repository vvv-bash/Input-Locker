"""
USB power management for input devices.
"""
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import logger


class PowerState(Enum):
    """Power states for USB devices."""
    ON = "on"
    SUSPEND = "suspend"
    UNKNOWN = "unknown"


@dataclass
class USBDevice:
    """Information about a USB device."""
    bus: str
    device: str
    vendor_id: str
    product_id: str
    name: str
    path: str
    
    @property
    def usb_address(self) -> str:
        """Return USB address in format bus:device"""
        return f"{self.bus}:{self.device}"


class PowerManager:
    """Manager for controlling USB device power state."""
    
    def __init__(self):
        """Initialize the power manager."""
        self.devices: Dict[str, USBDevice] = {}
        self._scan_usb_devices()
    
    def _scan_usb_devices(self):
        """Scan for USB devices using lsusb."""
        try:
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
            for line in result.stdout.strip().split('\n'):
                if line:
                    device = self._parse_lsusb_line(line)
                    if device:
                        self.devices[device.usb_address] = device
            logger.info(f"Found {len(self.devices)} USB devices")
        except Exception as e:
            logger.warning(f"USB scanning error: {e}")
    
    def _parse_lsusb_line(self, line: str) -> Optional[USBDevice]:
        """Parse lsusb output line."""
        try:
            parts = line.split()
            if len(parts) < 7:
                return None
            bus = parts[1]
            device = parts[3].rstrip(':')
            vendor_product = parts[6]
            name = ' '.join(parts[7:])
            if ':' not in vendor_product:
                return None
            vendor_id, product_id = vendor_product.split(':')
            return USBDevice(bus, device, vendor_id, product_id, name, f"/sys/bus/usb/devices/{bus}-{device}")
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None
    
    def get_all_devices(self) -> List[USBDevice]:
        """Get all detected USB devices."""
        return list(self.devices.values())
    
    def refresh(self):
        """Refresh the list of USB devices."""
        logger.info("Refreshing USB devices")
        self.devices.clear()
        self._scan_usb_devices()
