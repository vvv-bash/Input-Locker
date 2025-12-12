"""
Input devices blocker.
"""

from typing import Dict, Set
from evdev import InputDevice, ecodes
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot
from ..utils.logger import logger
from .selective_keyboard_blocker import SelectiveKeyboardBlocker


class InputBlocker(QObject):
    """Manage locking and unlocking of input devices."""
    
    # Señales thread-safe para comunicación con UI
    lock_changed = pyqtSignal(bool)
    device_locked = pyqtSignal(str)
    device_unlocked = pyqtSignal(str)
    unlock_requested = pyqtSignal()  # ← NUEVA SEÑAL para desbloqueo desde hotkey
    
    def __init__(self, device_manager, config_manager, hotkey_handler=None):
        """
        Initialize the blocker.

        Args:
            device_manager: Device manager
            config_manager: Configuration manager
            hotkey_handler: Global hotkey handler (optional)
        """
        super().__init__()
        
        self.device_manager = device_manager
        self.config_manager = config_manager
        self.hotkey_handler = hotkey_handler
        self.locked_devices: Set[str] = set()
        self.selective_blockers: Dict[str, SelectiveKeyboardBlocker] = {}
        self.is_locked = False
        self._unlocking = False
        
        # Conectar la señal de desbloqueo con el slot
        self.unlock_requested.connect(self._do_unlock)
        
        # Crear diccionario de dispositivos en formato compatible
        self.devices = {}
        for path, device_info in self.device_manager.devices.items():
            self.devices[path] = {
                'name': device_info.name,
                'type': device_info.device_type.value,
                'path': device_info.path,
                'enabled': True,
                '_device_info': device_info
            }
        
        logger.info("InputBlocker inicializado")
    
    def _get_allowed_keys_from_hotkey(self, hotkey: str) -> set:
        """
        Extract allowed keys from the hotkey string.

        Args:
            hotkey: Hotkey string (e.g. "ctrl+alt+l")

        Returns:
            set: Set of allowed key codes
        """
        allowed = set()
        parts = hotkey.lower().split('+')
        
        for part in parts:
            part = part.strip()
            if part in ['ctrl', 'control']:
                allowed.add(ecodes.KEY_LEFTCTRL)
                allowed.add(ecodes.KEY_RIGHTCTRL)
            elif part == 'alt':
                allowed.add(ecodes.KEY_LEFTALT)
                allowed.add(ecodes.KEY_RIGHTALT)
            elif part == 'shift':
                allowed.add(ecodes.KEY_LEFTSHIFT)
                allowed.add(ecodes.KEY_RIGHTSHIFT)
            elif part == 'super':
                allowed.add(ecodes.KEY_LEFTMETA)
                allowed.add(ecodes.KEY_RIGHTMETA)
            else:
                # Tecla principal
                key_name = f"KEY_{part.upper()}"
                if hasattr(ecodes, key_name):
                    allowed.add(getattr(ecodes, key_name))
        
        return allowed
    
    @pyqtSlot()
    def _do_unlock(self):
        """Slot that performs unlocking on the main (Qt) thread."""
        if self._unlocking:
            logger.warning("Ya se está procesando un desbloqueo, ignorando...")
            return
        
        logger.info("🔓 Ejecutando desbloqueo desde señal Qt...")
        self._unlocking = True
        
        try:
            self._unlock_all_internal()
        except Exception as e:
            logger.error(f"Error desbloqueando desde señal: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self._unlocking = False
    
    def lock_all(self):
        """
        Lock all enabled devices.
        - Keyboards: selective blocking (only hotkey allowed)
        - Mice: full blocking
        - Touchscreens: NOT blocked
        """
        if self.is_locked:
            logger.warning("Los dispositivos ya están bloqueados")
            return
        
        try:
            logger.info("=" * 60)
            logger.info("INICIANDO BLOQUEO DE DISPOSITIVOS")
            logger.info("=" * 60)
            
            # DETENER el hotkey handler global antes de bloquear
            if self.hotkey_handler:
                logger.info("⏸️  Deteniendo HotkeyHandler global...")
                self.hotkey_handler.stop()
            
            # Obtener teclas permitidas del hotkey
            hotkey = self.config_manager.get_hotkey()
            allowed_keys = self._get_allowed_keys_from_hotkey(hotkey)
            
            logger.info(f"Hotkey configurado: {hotkey}")
            logger.info(f"Teclas permitidas: {[hex(k) for k in allowed_keys]}")
            
            # Crear callback para desbloquear - SIMPLEMENTE EMITE LA SEÑAL
            def hotkey_callback():
                logger.info("🎯 CALLBACK DEL HOTKEY INVOCADO")
                logger.info("   Emitiendo señal unlock_requested...")
                try:
                    self.unlock_requested.emit()
                    logger.info("   ✅ Señal emitida correctamente")
                except Exception as e:
                    logger.error(f"   ❌ Error emitiendo señal: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            blocked_count = 0

            # Unlock pattern configuration (default: arrows)
            pattern_id = "arrows"
            try:
                pattern_id = self.config_manager.get_unlock_pattern_id()
            except Exception:
                pass
            
            for device_id, device_info in self.devices.items():
                # Saltar dispositivos deshabilitados
                if not device_info.get('enabled', True):
                    logger.debug(f"Saltando dispositivo deshabilitado: {device_info['name']}")
                    continue
                
                device_type = device_info.get('type')
                device_path = device_info.get('path')
                
                # NO BLOQUEAR TOUCHSCREENS
                if device_type == 'touchscreen':
                    logger.info(f"✓ Touchscreen NO bloqueado: {device_info['name']}")
                    continue
                
                # BLOQUEO SELECTIVO DE TECLADOS
                if device_type == 'keyboard':
                    try:
                        device = InputDevice(device_path)
                        blocker = SelectiveKeyboardBlocker(
                            device,
                            allowed_keys,
                            hotkey_callback=hotkey_callback,
                            pattern_id=pattern_id,
                        )
                        blocker.start()
                        
                        self.selective_blockers[device_id] = blocker
                        self.locked_devices.add(device_id)
                        blocked_count += 1
                        
                        logger.info(f"✓ Teclado con bloqueo selectivo: {device_info['name']}")
                        self.device_locked.emit(device_id)
                        
                    except Exception as e:
                        logger.error(f"Error en bloqueo selectivo de teclado {device_info['name']}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        continue
                
                # BLOQUEO TOTAL DE RATONES Y OTROS
                elif device_type in ['mouse', 'touchpad']:
                    if self._block_device(device_id):
                        self.locked_devices.add(device_id)
                        blocked_count += 1
                        logger.info(f"✓ Dispositivo bloqueado: {device_info['name']} ({device_type})")
                        self.device_locked.emit(device_id)
            
            self.is_locked = True
            self.lock_changed.emit(True)
            
            logger.info("=" * 60)
            logger.info(f"✅ BLOQUEO COMPLETADO: {blocked_count} dispositivo(s)")
            logger.info(f"💡 Presiona {hotkey} para desbloquear")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error bloqueando dispositivos: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Intentar limpiar en caso de error
            self.unlock_all()
            raise
    
    def _unlock_all_internal(self):
        """Internal unlock method (called from the slot)."""
        if not self.is_locked:
            logger.warning("Los dispositivos no están bloqueados")
            return
        
        logger.info("=" * 60)
        logger.info("INICIANDO DESBLOQUEO DE DISPOSITIVOS")
        logger.info("=" * 60)
        
        # Detener bloqueadores selectivos de teclado
        for device_id, blocker in list(self.selective_blockers.items()):
            try:
                logger.info(f"Deteniendo bloqueador: {device_id}")
                blocker.stop()
                logger.info(f"✓ Desbloqueado teclado selectivo: {device_id}")
                self.device_unlocked.emit(device_id)
            except Exception as e:
                logger.error(f"Error desbloqueando teclado {device_id}: {e}")
        
        self.selective_blockers.clear()
        
        # Desbloquear dispositivos normales
        for device_id in list(self.locked_devices):
            self._unblock_device(device_id)
            self.device_unlocked.emit(device_id)
        
        self.locked_devices.clear()
        self.is_locked = False
        self.lock_changed.emit(False)
        
        # REINICIAR el hotkey handler global después de desbloquear
        if self.hotkey_handler:
            logger.info("▶️  Reiniciando HotkeyHandler global...")
            self.hotkey_handler.start()
        
        logger.info("=" * 60)
        logger.info("✅ DESBLOQUEO COMPLETADO")
        logger.info("=" * 60)
    
    def unlock_all(self):
        """Unlock all devices (public method)."""
        try:
            self._unlock_all_internal()
        except Exception as e:
            logger.error(f"Error desbloqueando dispositivos: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Asegurar que el hotkey handler se reinicie incluso si hay error
            if self.hotkey_handler:
                try:
                    self.hotkey_handler.start()
                except:
                    pass
    
    def toggle_lock(self):
        """Toggle between locking and unlocking all devices."""
        if self.is_locked:
            logger.info("Desbloqueando dispositivos (toggle)")
            self.unlock_all()
        else:
            logger.info("Bloqueando dispositivos (toggle)")
            self.lock_all()
    
    def _block_device(self, device_id: str) -> bool:
        """Block a single device (full grab)."""
        try:
            device_info = self.devices.get(device_id)
            if not device_info:
                return False
            
            device_path = device_info['path']
            device = InputDevice(device_path)
            device.grab()
            
            # Guardar referencia al dispositivo
            device_info['_grabbed_device'] = device
            
            return True
            
        except Exception as e:
            logger.error(f"Error bloqueando {device_id}: {e}")
            return False
    
    def _unblock_device(self, device_id: str) -> bool:
        """Unblock a single device."""
        try:
            device_info = self.devices.get(device_id)
            if not device_info:
                return False
            
            grabbed_device = device_info.get('_grabbed_device')
            if grabbed_device:
                grabbed_device.ungrab()
                grabbed_device.close()
                device_info['_grabbed_device'] = None
            
            logger.info(f"✓ Desbloqueado: {device_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error desbloqueando {device_id}: {e}")
            return False
    
    def get_blocked_devices(self) -> Set[str]:
        """Obtiene el conjunto de dispositivos bloqueados."""
        return self.locked_devices.copy()
    
    def get_blocked_count(self) -> int:
        """Obtiene el número de dispositivos bloqueados."""
        return len(self.locked_devices)
    
    def get_lock_status(self) -> bool:
        """Obtiene el estado general de bloqueo."""
        return self.is_locked
    
    def toggle_device(self, device_id: str):
        """Alterna el estado de bloqueo de un dispositivo."""
        if device_id in self.locked_devices:
            self._unblock_device(device_id)
            self.locked_devices.remove(device_id)
            self.device_unlocked.emit(device_id)
        else:
            if self._block_device(device_id):
                self.locked_devices.add(device_id)
                self.device_locked.emit(device_id)