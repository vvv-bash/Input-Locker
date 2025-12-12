"""
Input devices manager with intelligent detection and classification.
"""

import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

import evdev
from evdev import ecodes, InputDevice

from ..utils.logger import logger


class DeviceType(Enum):
    """Tipos de dispositivos de entrada."""
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    TOUCHSCREEN = "touchscreen"
    TOUCHPAD = "touchpad"
    UNKNOWN = "unknown"


@dataclass
class InputDeviceInfo:
    """Information about an input device."""
    path: str
    name: str
    device_type: DeviceType
    phys: str
    vendor: str
    product: str
    capabilities: Dict
    
    def __str__(self):
        return f"{self.name} ({self.device_type.value})"
    
    @property
    def icon(self) -> str:
        """Return the emoji/icon appropriate for the device."""
        icons = {
            DeviceType.KEYBOARD: "⌨️",
            DeviceType.MOUSE: "🖱️",
            DeviceType.TOUCHSCREEN: "👆",
            DeviceType.TOUCHPAD: "👆",
            DeviceType.UNKNOWN: "❓"
        }
        return icons.get(self.device_type, "❓")


class DeviceManager:
    """Manager for detecting and classifying input devices."""
    
    # Patrones para identificar dispositivos específicos
    KEYBOARD_PATTERNS = [
        r'keyboard',
        r'keychron',
        r'logitech.*keyboard',
        r'.*kbd',
    ]
    
    MOUSE_PATTERNS = [
        r'mouse',
        r'logitech.*mouse',
        r'.*pointing.*device',
    ]
    
    TOUCHSCREEN_PATTERNS = [
        r'touchscreen',
        r'touch.*screen',
        r'.*ts.*',
    ]
    
    TOUCHPAD_PATTERNS = [
        r'touchpad',
        r'synaptics',
        r'elan.*touchpad',
    ]
    
    def __init__(self):
        """Inicializa el gestor de dispositivos."""
        self.devices: Dict[str, InputDeviceInfo] = {}
        self._scan_devices()
    
    def _scan_devices(self):
        """Scan all devices under /dev/input/."""
        logger.info("Scanning input devices...")
        
        input_dir = Path('/dev/input')
        if not input_dir.exists():
            logger.error("Directorio /dev/input no existe")
            return
        
        # Buscar todos los event*
        event_files = sorted(input_dir.glob('event*'))
        
        for event_path in event_files:
            try:
                device = InputDevice(str(event_path))
                device_info = self._analyze_device(device)
                
                if device_info:
                    self.devices[device_info.path] = device_info
                    logger.info(f"Detected: {device_info}")
                    
            except Exception as e:
                logger.warning(f"Error analizando {event_path}: {e}")
        
        logger.info(f"Total devices detected: {len(self.devices)}")
    
    def _analyze_device(self, device: InputDevice) -> Optional[InputDeviceInfo]:
        """
        Analyze a device and determine its type.

        Args:
            device: evdev InputDevice to analyze

        Returns:
            InputDeviceInfo or None if it could not be classified
        """
        try:
            caps = device.capabilities(verbose=False)
            name = device.name.lower()

            # Determine type
            device_type = self._classify_device(name, caps)

            # Extract additional information
            info = device.info

            device_info = InputDeviceInfo(
                path=device.path,
                name=device.name,
                device_type=device_type,
                phys=device.phys or "unknown",
                vendor=f"{info.vendor:04x}",
                product=f"{info.product:04x}",
                capabilities=caps
            )

            return device_info

        except Exception as e:
            logger.error(f"Error analyzing device {getattr(device, 'path', 'unknown')}: {e}")
            return None
    
    def _classify_device(self, name: str, caps: Dict) -> DeviceType:
        """
        Classify a device by its name and capabilities.

        Args:
            name: Device name (lowercase)
            caps: Device capabilities

        Returns:
            Detected DeviceType
        """
        # 1. Detectar touchscreen (prioridad alta)
        if self._is_touchscreen(caps):
            return DeviceType.TOUCHSCREEN
        
        # 2. Detectar por patrones de nombre
        for pattern in self.TOUCHSCREEN_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return DeviceType.TOUCHSCREEN
        
        for pattern in self.TOUCHPAD_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return DeviceType.TOUCHPAD
        
        for pattern in self.KEYBOARD_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return DeviceType.KEYBOARD
        
        for pattern in self.MOUSE_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return DeviceType.MOUSE
        
        # 3. Clasificar por capabilities
        if self._has_keyboard_keys(caps):
            return DeviceType.KEYBOARD
        
        if self._is_pointer_device(caps):
            return DeviceType.MOUSE
        
        return DeviceType.UNKNOWN
    
    def _is_touchscreen(self, caps: Dict) -> bool:
        """
        Detect whether a device is a touchscreen based on capabilities.

        Args:
            caps: Device capabilities

        Returns:
            True if touchscreen
        """
        # Buscar eventos multi-touch absolutos
        if ecodes.EV_ABS not in caps:
            return False
        
        abs_events = caps[ecodes.EV_ABS]
        
        # Verificar eventos multi-touch característicos
        multitouch_events = {
            ecodes.ABS_MT_POSITION_X,
            ecodes.ABS_MT_POSITION_Y,
            ecodes.ABS_MT_SLOT,
            ecodes.ABS_MT_TRACKING_ID
        }
        
        # Si tiene al menos 2 de estos eventos, es touchscreen
        found = sum(1 for event in multitouch_events 
                   if any(e[0] == event for e in abs_events))
        return found >= 2
    
    def _has_keyboard_keys(self, caps: Dict) -> bool:
        """
        Check if device has keyboard keys.

        Args:
            caps: Device capabilities

        Returns:
            True if it contains keyboard keys
        """
        if ecodes.EV_KEY not in caps:
            return False
        
        keys = caps[ecodes.EV_KEY]
        
        # Buscar teclas características de teclado
        keyboard_keys = {
            ecodes.KEY_A, ecodes.KEY_Z,
            ecodes.KEY_ENTER, ecodes.KEY_SPACE,
            ecodes.KEY_ESC, ecodes.KEY_LEFTCTRL
        }
        
        # Si tiene al menos 3 teclas de teclado, es teclado
        found = sum(1 for key in keyboard_keys if key in keys)
        return found >= 3
    
    def _is_pointer_device(self, caps: Dict) -> bool:
        """
        Determine if device is a pointer device (mouse).

        Args:
            caps: Device capabilities

        Returns:
            True if mouse-like
        """
        # Debe tener eventos relativos (mouse) o absolutos (touchpad)
        has_rel = ecodes.EV_REL in caps
        has_abs = ecodes.EV_ABS in caps
        
        if not (has_rel or has_abs):
            return False
        
        # Debe tener botones
        if ecodes.EV_KEY not in caps:
            return False
        
        keys = caps[ecodes.EV_KEY]
        
        # Buscar botones de mouse
        mouse_buttons = {
            ecodes.BTN_LEFT,
            ecodes.BTN_RIGHT,
            ecodes.BTN_MIDDLE,
            ecodes.BTN_MOUSE
        }
        
        # Si tiene al menos un botón de mouse
        found = any(btn in keys for btn in mouse_buttons)
        return found
    
    def get_devices_by_type(self, device_type: DeviceType) -> List[InputDeviceInfo]:
        """
        Obtiene todos los dispositivos de un tipo específico.
        
        Args:
            device_type: Tipo de dispositivo a buscar
            
        Returns:
            Lista de dispositivos del tipo especificado
        """
        return [
            dev for dev in self.devices.values()
            if dev.device_type == device_type
        ]
    
    def get_all_devices(self) -> List[InputDeviceInfo]:
        """Retorna todos los dispositivos detectados."""
        return list(self.devices.values())
    
    def get_device_by_path(self, path: str) -> Optional[InputDeviceInfo]:
        """
        Obtiene información de un dispositivo por su path.
        
        Args:
            path: Path del dispositivo (ej: /dev/input/event0)
            
        Returns:
            InputDeviceInfo o None si no existe
        """
        return self.devices.get(path)
    
    def refresh(self):
        """Refresca la lista de dispositivos."""
        logger.info("Refrescando lista de dispositivos...")
        self.devices.clear()
        self._scan_devices()
    
    def get_summary(self) -> Dict[str, int]:
        """
        Obtiene un resumen de dispositivos por tipo.
        
        Returns:
            Diccionario con conteo por tipo
        """
        summary = {
            'keyboards': len(self.get_devices_by_type(DeviceType.KEYBOARD)),
            'mice': len(self.get_devices_by_type(DeviceType.MOUSE)),
            'touchscreens': len(self.get_devices_by_type(DeviceType.TOUCHSCREEN)),
            'touchpads': len(self.get_devices_by_type(DeviceType.TOUCHPAD)),
            'unknown': len(self.get_devices_by_type(DeviceType.UNKNOWN)),
            'total': len(self.devices)
        }
        return summary