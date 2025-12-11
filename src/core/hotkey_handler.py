"""
Global hotkey manager using evdev.
"""

import threading
from typing import Callable, Optional, Set, Tuple
import evdev
from evdev import InputDevice, categorize, ecodes
import select

from ..utils.logger import logger


class HotkeyHandler:
    """
    Gestor de hotkeys globales que funciona incluso cuando dispositivos están bloqueados.
    Usa evdev directamente para capturar teclas a bajo nivel.
    """
    
    def __init__(self, hotkey_string: str = "Ctrl+Alt+L"):
        """
        Initialize the hotkey handler.

        Args:
            hotkey_string: Hotkey string (e.g. "Ctrl+Alt+L")
        """
        self.hotkey_string = hotkey_string
        self.callback: Optional[Callable] = None
        self.listener_thread: Optional[threading.Thread] = None
        self.is_running = False
        self._stop_event = threading.Event()
        self._last_trigger_time = 0.0  # Debounce timestamp
        self._debounce_interval = 0.5  # 500ms debounce
        
        # Dispositivos de teclado
        self.keyboard_devices = []
        
        # Parsear hotkey
        self.required_keys = self._parse_hotkey(hotkey_string)
        # Si la combinación es inválida y no produce códigos, forzar valor por defecto
        if not self.required_keys:
            logger.warning(
                f"Hotkey '{hotkey_string}' no produjo códigos válidos; usando Ctrl+Alt+L por defecto"
            )
            self.hotkey_string = "Ctrl+Alt+L"
            self.required_keys = self._parse_hotkey(self.hotkey_string)
        self.pressed_keys: Set[int] = set()
        
        logger.info(f"HotkeyHandler inicializado con: {hotkey_string}")
        logger.debug(f"Códigos de teclas requeridos: {self.required_keys}")
    
    def _parse_hotkey(self, hotkey_string: str) -> Set[int]:
        """
        Convert a hotkey string to evdev key codes.

        Args:
            hotkey_string: String like "Ctrl+Alt+L"

        Returns:
            Set of evdev key codes
        """
        # Mapa de nombres a códigos evdev
        key_map = {
            'ctrl': ecodes.KEY_LEFTCTRL,
            'control': ecodes.KEY_LEFTCTRL,
            'alt': ecodes.KEY_LEFTALT,
            'shift': ecodes.KEY_LEFTSHIFT,
            'super': ecodes.KEY_LEFTMETA,
            'win': ecodes.KEY_LEFTMETA,
            'cmd': ecodes.KEY_LEFTMETA,
            # Letras
            'a': ecodes.KEY_A, 'b': ecodes.KEY_B, 'c': ecodes.KEY_C,
            'd': ecodes.KEY_D, 'e': ecodes.KEY_E, 'f': ecodes.KEY_F,
            'g': ecodes.KEY_G, 'h': ecodes.KEY_H, 'i': ecodes.KEY_I,
            'j': ecodes.KEY_J, 'k': ecodes.KEY_K, 'l': ecodes.KEY_L,
            'm': ecodes.KEY_M, 'n': ecodes.KEY_N, 'o': ecodes.KEY_O,
            'p': ecodes.KEY_P, 'q': ecodes.KEY_Q, 'r': ecodes.KEY_R,
            's': ecodes.KEY_S, 't': ecodes.KEY_T, 'u': ecodes.KEY_U,
            'v': ecodes.KEY_V, 'w': ecodes.KEY_W, 'x': ecodes.KEY_X,
            'y': ecodes.KEY_Y, 'z': ecodes.KEY_Z,
        }
        
        # Separar y convertir
        parts = [part.strip().lower() for part in hotkey_string.split('+')]
        codes = set()
        
        for part in parts:
            if part in key_map:
                codes.add(key_map[part])
            else:
                logger.warning(f"Tecla desconocida en hotkey: {part}")
        
        return codes
    
    def _find_keyboard_devices(self):
        """Find all keyboard devices."""
        self.keyboard_devices = []
        
        try:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            
            for device in devices:
                # Verificar si tiene capacidades de teclado
                caps = device.capabilities(verbose=False)
                if ecodes.EV_KEY in caps:
                    # Verificar que tenga teclas de teclado (no solo botones de mouse)
                    keys = caps[ecodes.EV_KEY]
                    if ecodes.KEY_A in keys or ecodes.KEY_ENTER in keys:
                        # NO grab - solo lectura pasiva sin bloquear el dispositivo
                        self.keyboard_devices.append(device)
                        logger.debug(f"Teclado encontrado: {device.name} ({device.path})")
            
            logger.info(f"Encontrados {len(self.keyboard_devices)} dispositivos de teclado")
            
        except Exception as e:
            logger.error(f"Error buscando teclados: {e}")
    
    def set_callback(self, callback: Callable):
        """
        Set the callback function to execute when the hotkey is pressed.

        Args:
            callback: Callable to be executed
        """
        self.callback = callback
        logger.debug("Callback de hotkey registrado")
    
    def start(self) -> bool:
        """
        Start the hotkey listener.

        Returns:
            bool: True if started successfully
        """
        if self.is_running:
            logger.warning("Listener de hotkeys ya está corriendo")
            return False
        
        if not self.callback:
            logger.error("No hay callback registrado")
            return False
        
        try:
            # Limpiar estado anterior
            self.pressed_keys.clear()
            self._last_trigger_time = 0.0
            
            # Encontrar dispositivos de teclado
            self._find_keyboard_devices()
            
            if not self.keyboard_devices:
                logger.error("No se encontraron dispositivos de teclado")
                return False
            
            # Iniciar thread de escucha
            self._stop_event.clear()
            self.is_running = True
            self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listener_thread.start()
            
            logger.info(f"✓ Listener de hotkeys iniciado: {self.hotkey_string}")
            return True
            
        except Exception as e:
            logger.error(f"Error iniciando listener de hotkeys: {e}")
            self.is_running = False
            return False
    
    def stop(self):
        """Stop the hotkey listener."""
        if not self.is_running:
            return
        
        try:
            self.is_running = False
            self._stop_event.set()
            
            # Esperar a que termine el thread
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.join(timeout=2.0)
            
            # Cerrar dispositivos
            for device in self.keyboard_devices:
                try:
                    device.close()
                except:
                    pass
            
            self.keyboard_devices = []
            self.pressed_keys.clear()
            self._pending_callback = False  # Limpiar cualquier callback pendiente
            logger.info("Listener de hotkeys detenido")
            
        except Exception as e:
            logger.error(f"Error deteniendo listener: {e}")
    
    def _listen_loop(self):
        """Main listening loop for events."""
        logger.debug("Thread de escucha de hotkeys iniciado")
        
        while not self._stop_event.is_set():
            try:
                # Usar select para esperar eventos de cualquier teclado
                readable_devices = select.select(self.keyboard_devices, [], [], 0.5)[0]
                
                for device in readable_devices:
                    try:
                        for event in device.read():
                            if event.type == ecodes.EV_KEY:
                                self._handle_key_event(event)
                    except OSError:
                        # Dispositivo desconectado
                        logger.warning(f"Dispositivo desconectado: {device.name}")
                        self.keyboard_devices.remove(device)
                        if not self.keyboard_devices:
                            logger.error("No quedan dispositivos de teclado")
                            self._stop_event.set()
            
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"Error en loop de escucha: {e}")
        
        logger.debug("Thread de escucha de hotkeys finalizado")
    
    def _handle_key_event(self, event):
        """Handle a key event."""
        import time
        key_code = event.code
        
        # 1 = presionada, 0 = soltada, 2 = repetición
        if event.value == 1:  # Tecla presionada
            self.pressed_keys.add(key_code)
            
            # Verificar si se cumple la combinación EXACTA
            # (all required keys pressed and nothing extra from required set)
            if self.required_keys.issubset(self.pressed_keys):
                # Debounce: prevent rapid re-triggers
                current_time = time.time()
                if current_time - self._last_trigger_time < self._debounce_interval:
                    logger.debug(f"Hotkey debounced (too soon since last trigger)")
                    return
                
                self._last_trigger_time = current_time
                logger.info(f"Hotkey detectado: {self.hotkey_string}")
                
                # Marcar que necesitamos ejecutar callback cuando se suelten las teclas
                self._pending_callback = True
                
        elif event.value == 0:  # Tecla soltada
            self.pressed_keys.discard(key_code)
            
            # Si tenemos un callback pendiente y todas las teclas requeridas se soltaron
            if getattr(self, '_pending_callback', False) and len(self.pressed_keys) == 0:
                self._pending_callback = False
                logger.info(f"Todas las teclas soltadas, ejecutando callback")
                
                if self.callback:
                    try:
                        # Ejecutar callback en thread separado (sin delay)
                        threading.Thread(target=self.callback, daemon=True).start()
                    except Exception as e:
                        logger.error(f"Error ejecutando callback: {e}")
    
    def update_hotkey(self, new_hotkey: str) -> bool:
        """
        Update the hotkey while running.

        Args:
            new_hotkey: New hotkey string

        Returns:
            bool: True if updated successfully
        """
        was_running = self.is_running
        
        # Detener si está corriendo
        if was_running:
            self.stop()
        
        # Actualizar
        self.hotkey_string = new_hotkey
        self.required_keys = self._parse_hotkey(new_hotkey)
        if not self.required_keys:
            logger.warning(
                f"Hotkey '{new_hotkey}' no produjo códigos válidos; ignorando cambio y manteniendo {self.hotkey_string}"
            )
        else:
            self.pressed_keys.clear()
        
        # Reiniciar si estaba corriendo
        if was_running:
            return self.start()
        
        return True
    
    @staticmethod
    def is_valid_hotkey(hotkey_string: str) -> bool:
        """
        Validate whether a hotkey string is valid.

        Args:
            hotkey_string: String to validate

        Returns:
            bool: True if valid
        """
        if not hotkey_string or not isinstance(hotkey_string, str):
            return False
        
        # Debe tener al menos un modificador + una tecla
        parts = [p.strip().lower() for p in hotkey_string.split('+')]
        
        if len(parts) < 2:
            return False
        
        # Verificar que tenga modificadores válidos
        valid_modifiers = {'ctrl', 'control', 'alt', 'shift', 'super', 'win', 'cmd'}
        has_modifier = any(part in valid_modifiers for part in parts[:-1])
        
        return has_modifier


class HotkeyCapture:
    """Utilidad para capturar combinaciones de teclas del usuario usando evdev."""
    
    def __init__(self):
        """Inicializa el capturador de hotkeys."""
        self.captured_keys = set()
        self.listener_thread: Optional[threading.Thread] = None
        self.is_capturing = False
        self._stop_event = threading.Event()
        self.result_callback: Optional[Callable] = None
        self.keyboard_devices = []
        self.pressed_codes: Set[int] = set()
    
    def start_capture(self, callback: Callable[[str], None]):
        """
        Start hotkey capture.

        Args:
            callback: Function that will receive the captured hotkey string
        """
        self.result_callback = callback
        self.captured_keys.clear()
        self.pressed_codes.clear()
        self.is_capturing = True
        self._stop_event.clear()
        
        # Encontrar dispositivos de teclado
        self._find_keyboard_devices()
        
        # Iniciar thread de captura
        self.listener_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.listener_thread.start()
        
        logger.debug("Captura de hotkey iniciada")
    
    def stop_capture(self):
        """Stop the capture."""
        self.is_capturing = False
        self._stop_event.set()
        
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1.0)
        
        # Cerrar dispositivos
        for device in self.keyboard_devices:
            try:
                device.close()
            except:
                pass
        
        self.keyboard_devices = []
        logger.debug("Captura de hotkey detenida")
    
    def _find_keyboard_devices(self):
        """Encuentra todos los dispositivos de teclado."""
        self.keyboard_devices = []
        
        try:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            
            for device in devices:
                caps = device.capabilities(verbose=False)
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    if ecodes.KEY_A in keys or ecodes.KEY_ENTER in keys:
                        self.keyboard_devices.append(device)
        except Exception as e:
            logger.error(f"Error buscando teclados para captura: {e}")
    
    def _capture_loop(self):
        """Event capture loop."""
        while not self._stop_event.is_set() and self.is_capturing:
            try:
                readable_devices = select.select(self.keyboard_devices, [], [], 0.5)[0]
                
                for device in readable_devices:
                    try:
                        for event in device.read():
                            if event.type == ecodes.EV_KEY:
                                self._handle_capture_event(event)
                    except OSError:
                        pass
            
            except Exception as e:
                if self.is_capturing:
                    logger.error(f"Error en captura: {e}")
    
    def _handle_capture_event(self, event):
        """Handle events during capture."""
        key_code = event.code
        
        if event.value == 1:  # Tecla presionada
            key_name = self._get_key_name(key_code)
            if key_name:
                self.captured_keys.add(key_name)
                self.pressed_codes.add(key_code)
                logger.debug(f"Tecla capturada: {key_name}")
        
        elif event.value == 0:  # Tecla soltada
            self.pressed_codes.discard(key_code)
            
            # Si se soltaron todas las teclas y había algo capturado
            if not self.pressed_codes and len(self.captured_keys) >= 2:
                hotkey = self._build_hotkey_string()
                
                # Detener captura
                self.stop_capture()
                
                # Llamar callback con resultado
                if self.result_callback:
                    self.result_callback(hotkey)
    
    def _get_key_name(self, key_code: int) -> Optional[str]:
        """Obtiene el nombre normalizado de una tecla desde su código."""
        # Mapa inverso de códigos a nombres
        code_map = {
            ecodes.KEY_LEFTCTRL: 'Ctrl',
            ecodes.KEY_RIGHTCTRL: 'Ctrl',
            ecodes.KEY_LEFTALT: 'Alt',
            ecodes.KEY_RIGHTALT: 'Alt',
            ecodes.KEY_LEFTSHIFT: 'Shift',
            ecodes.KEY_RIGHTSHIFT: 'Shift',
            ecodes.KEY_LEFTMETA: 'Super',
            ecodes.KEY_RIGHTMETA: 'Super',
        }
        
        if key_code in code_map:
            return code_map[key_code]
        
        # Intentar obtener nombre de tecla
        try:
            key_name = ecodes.KEY[key_code]
            # Convertir KEY_A -> A, KEY_ENTER -> Enter
            if key_name.startswith('KEY_'):
                name = key_name[4:]
                return name.capitalize() if len(name) > 1 else name.upper()
        except:
            pass
        
        return None
    
    def _build_hotkey_string(self) -> str:
        """Construye el string del hotkey desde las teclas capturadas."""
        # Ordenar: modificadores primero, luego tecla principal
        modifiers = {'Ctrl', 'Alt', 'Shift', 'Super'}
        mod_keys = sorted([k for k in self.captured_keys if k in modifiers])
        normal_keys = sorted([k for k in self.captured_keys if k not in modifiers])
        
        all_keys = mod_keys + normal_keys
        return '+'.join(all_keys)