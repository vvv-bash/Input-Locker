"""
Selective keyboard blocker that allows specific hotkeys.
"""

import threading
from evdev import InputDevice, UInput, ecodes
from select import select
from ..utils.logger import logger
from .pattern_unlocker import PatternUnlocker


class SelectiveKeyboardBlocker:
    """Block a physical keyboard while allowing specific key combinations."""

    def __init__(self, device: InputDevice, allowed_keys: set, hotkey_callback=None, pattern_id: str = "arrows"):
        """
        Initialize the selective blocker.

        Args:
            device: evdev InputDevice to block
            allowed_keys: Set of allowed key codes (hotkey)
            hotkey_callback: Callable invoked when the full hotkey is pressed
        """
        self.device = device
        # allowed_keys contiene las teclas del hotkey configurado
        self.allowed_keys = allowed_keys.copy()  # Hacer copia
        # Mantener un conjunto separado solo para comprobar el hotkey completo
        self.hotkey_keys = allowed_keys.copy()
        self.hotkey_callback = hotkey_callback
        self.thread = None
        self.running = False
        self.pressed_keys = set()
        self.hotkey_triggered = False
        self.virtual_device = None

        # ========================================
        # Pattern Unlocker (configurable pattern)
        # ========================================
        logger.info("🎮 Inicializando Pattern Unlocker...")

        # Map a small pattern id to a concrete key sequence
        if pattern_id == "wasd":
            pattern_keys = [
                ecodes.KEY_W,
                ecodes.KEY_W,
                ecodes.KEY_S,
                ecodes.KEY_S,
                ecodes.KEY_ENTER,
            ]
        else:
            # Default: arrows ↑ ↑ ↓ ↓ ENTER
            pattern_keys = [
                ecodes.KEY_UP,
                ecodes.KEY_UP,
                ecodes.KEY_DOWN,
                ecodes.KEY_DOWN,
                ecodes.KEY_ENTER,
            ]

        self.pattern_unlocker = PatternUnlocker(
            callback=hotkey_callback,
            pattern=pattern_keys,
            timeout=3.0,
        )

        # Add all pattern keys to the allowed set so they always pass
        self.allowed_keys.update(pattern_keys)
        logger.info("✓ Pattern keys added to allowed set")
        
        logger.info(f"SelectiveKeyboardBlocker creado para: {device.name}")
        logger.info(f"Teclas permitidas totales: {len(self.allowed_keys)}")
    
    def _create_virtual_device(self):
        """Create a virtual device to forward allowed events."""
        try:
            capabilities = self.device.capabilities()
            filtered_caps = {
                ev_type: codes for ev_type, codes in capabilities.items()
                if ev_type not in [ecodes.EV_SYN, ecodes.EV_FF]
            }
            
            self.virtual_device = UInput(
                events=filtered_caps,
                name=f"{self.device.name} (Virtual)",
                vendor=self.device.info.vendor,
                product=self.device.info.product,
                version=self.device.info.version
            )
            
            logger.info(f"✓ Dispositivo virtual creado para {self.device.name}")
            
        except Exception as e:
            logger.error(f"Error creando dispositivo virtual: {e}")
            raise
    
    def start(self):
        """Start selective blocking in a separate thread."""
        if self.running:
            logger.warning(f"Bloqueador ya está corriendo para {self.device.name}")
            return
        
        try:
            self._create_virtual_device()
            self.device.grab()
            logger.info(f"✓ Grab exclusivo obtenido: {self.device.name}")
            
            self.running = True
            self.pressed_keys.clear()
            self.hotkey_triggered = False
            
            # Resetear pattern unlocker
            self.pattern_unlocker.reset()
            
            self.thread = threading.Thread(target=self._process_events, daemon=True)
            self.thread.start()
            
            logger.info(f"✓ Bloqueador selectivo iniciado: {self.device.name}")
            logger.info("=" * 60)
            logger.info("🎮 PATRÓN DE DESBLOQUEO ACTIVO")
            logger.info("   Presiona: ↑ ↑ ↓ ↓ ENTER")
            logger.info("   (Flechas arriba, arriba, abajo, abajo, Enter)")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error iniciando bloqueador selectivo: {e}")
            self.running = False
            raise
    
    def stop(self):
        """Stop selective blocking."""
        if not self.running:
            return
        
        logger.info(f"Deteniendo bloqueador selectivo: {self.device.name}")
        
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        # IMPORTANTE: Liberar todas las teclas presionadas antes de cerrar
        # para evitar teclas "pegadas"
        if self.virtual_device and self.pressed_keys:
            logger.info(f"Liberando {len(self.pressed_keys)} teclas presionadas...")
            try:
                for key_code in list(self.pressed_keys):
                    self.virtual_device.write(ecodes.EV_KEY, key_code, 0)  # Release
                self.virtual_device.syn()
                logger.info("✓ Teclas presionadas liberadas")
            except Exception as e:
                logger.warning(f"Error liberando teclas: {e}")
        
        try:
            self.device.ungrab()
            logger.debug(f"✓ Grab liberado: {self.device.name}")
        except Exception as e:
            logger.warning(f"Error liberando grab: {e}")
        
        if self.virtual_device:
            try:
                self.virtual_device.close()
                self.virtual_device = None
                logger.debug(f"✓ Dispositivo virtual cerrado: {self.device.name}")
            except Exception as e:
                logger.warning(f"Error cerrando dispositivo virtual: {e}")
        
        self.pressed_keys.clear()
        self.hotkey_triggered = False
        self.pattern_unlocker.reset()
        
        logger.info(f"✓ Bloqueador selectivo detenido: {self.device.name}")
    
    def _is_hotkey_pressed(self) -> bool:
        """Check if all keys of the configured hotkey are currently pressed."""
        return self.hotkey_keys.issubset(self.pressed_keys)
    
    def _process_events(self):
        """Process keyboard events (runs in a separate thread)."""
        logger.info(f"Thread de eventos iniciado: {self.device.name}")
        
        try:
            while self.running:
                r, w, x = select([self.device.fd], [], [], 0.1)
                
                if not r:
                    continue
                
                try:
                    for event in self.device.read():
                        if not self.running:
                            break
                        
                        if event.type == ecodes.EV_KEY:
                            self._handle_key_event(event)
                        
                except BlockingIOError:
                    continue
                except OSError as e:
                    if self.running:
                        logger.error(f"Error leyendo dispositivo {self.device.name}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error en procesamiento de eventos: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info(f"Thread de eventos finalizado: {self.device.name}")
    
    def _handle_key_event(self, event):
        """Handle a key event."""
        key_code = event.code
        key_state = event.value
        
        # ========================================
        # PRIMERO: Verificar patrón
        # ========================================
        try:
            if self.pattern_unlocker.handle_key(key_code, key_state):
                logger.info("🔓 Patrón detectado - Pattern Unlocker activado")
                return  # Patrón detectado, ya se llamó al callback
        except Exception as e:
            logger.error(f"Error en pattern_unlocker: {e}")
        
        # ========================================
        # SEGUNDO: Lógica normal de hotkey
        # ========================================
        
        # Actualizar teclas presionadas
        if key_state == 1:  # Press
            self.pressed_keys.add(key_code)
        elif key_state == 0:  # Release
            self.pressed_keys.discard(key_code)
            if key_code in self.allowed_keys:
                self.hotkey_triggered = False
        
        # Si es tecla permitida
        if key_code in self.allowed_keys:
            # Reenviar al dispositivo virtual
            if self.virtual_device:
                try:
                    self.virtual_device.write(event.type, event.code, event.value)
                    self.virtual_device.syn()
                except Exception as e:
                    logger.error(f"Error reenviando tecla: {e}")
            
            # Verificar hotkey completo (Ctrl+Alt+L original)
            if key_state == 1 and not self.hotkey_triggered:
                if self._is_hotkey_pressed():
                    logger.info(f"🔓 HOTKEY ORIGINAL DETECTADO en {self.device.name}")
                    self.hotkey_triggered = True
                    
                    if self.hotkey_callback:
                        try:
                            self.hotkey_callback()
                        except Exception as e:
                            logger.error(f"Error en callback: {e}")