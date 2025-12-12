"""
Lightweight global hotkey handler using evdev.
"""

import threading
import time
import selectors
from typing import Callable, Optional, Set
import evdev
from evdev import ecodes

from ..utils.logger import logger


class HotkeyHandlerLite:
    def __init__(self, hotkey_string: str = "Ctrl+Alt+L"):
        self.hotkey_string = hotkey_string
        self.callback: Optional[Callable] = None
        self.listener_thread: Optional[threading.Thread] = None
        self.is_running = False
        self._stop_event = threading.Event()
        self._last_trigger_time = 0.0
        self._debounce_interval = 0.4
        self.keyboard_devices = []
        self.selector = None
        self.required_keys = self._parse_hotkey(hotkey_string)
        self.pressed_keys: Set[int] = set()
        logger.info(f"HotkeyHandlerLite initialized: {hotkey_string}")
    
    def _parse_hotkey(self, hotkey_string: str) -> Set[int]:
        key_map = {
            'ctrl': ecodes.KEY_LEFTCTRL, 'control': ecodes.KEY_LEFTCTRL,
            'alt': ecodes.KEY_LEFTALT, 'shift': ecodes.KEY_LEFTSHIFT, 'super': ecodes.KEY_LEFTMETA,
            'a': ecodes.KEY_A, 'b': ecodes.KEY_B, 'c': ecodes.KEY_C, 'd': ecodes.KEY_D,
            'e': ecodes.KEY_E, 'f': ecodes.KEY_F, 'g': ecodes.KEY_G, 'h': ecodes.KEY_H,
            'i': ecodes.KEY_I, 'j': ecodes.KEY_J, 'k': ecodes.KEY_K, 'l': ecodes.KEY_L,
            'm': ecodes.KEY_M, 'n': ecodes.KEY_N, 'o': ecodes.KEY_O, 'p': ecodes.KEY_P,
            'q': ecodes.KEY_Q, 'r': ecodes.KEY_R, 's': ecodes.KEY_S, 't': ecodes.KEY_T,
            'u': ecodes.KEY_U, 'v': ecodes.KEY_V, 'w': ecodes.KEY_W, 'x': ecodes.KEY_X,
            'y': ecodes.KEY_Y, 'z': ecodes.KEY_Z,
        }
        codes = set()
        for part in [p.strip().lower() for p in hotkey_string.split('+')]:
            if part in key_map:
                codes.add(key_map[part])
        return codes if codes else {ecodes.KEY_LEFTCTRL, ecodes.KEY_LEFTALT, ecodes.KEY_L}
    
    def _find_keyboards(self):
        self.keyboard_devices = []
        for path in evdev.list_devices():
            try:
                device = evdev.InputDevice(path)
                caps = device.capabilities(verbose=False)
                if ecodes.EV_KEY in caps and (ecodes.KEY_A in caps[ecodes.EV_KEY] or ecodes.KEY_ENTER in caps[ecodes.EV_KEY]):
                    self.keyboard_devices.append(device)
            except:
                pass
        logger.info(f"Found {len(self.keyboard_devices)} keyboard(s)")
    
    def set_callback(self, callback: Callable):
        self.callback = callback
    
    def start(self) -> bool:
        if self.is_running or not self.callback:
            return False
        self._find_keyboards()
        if not self.keyboard_devices:
            return False
        self._stop_event.clear()
        self.is_running = True
        self.pressed_keys.clear()
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        logger.info(f"Hotkey listener started: {self.hotkey_string}")
        return True
    
    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        self._stop_event.set()
        if self.selector:
            try: self.selector.close()
            except: pass
            self.selector = None
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=0.3)
        for device in self.keyboard_devices:
            try: device.close()
            except: pass
        self.keyboard_devices = []
        self.pressed_keys.clear()
        logger.info("Hotkey listener stopped")
    
    def _listen_loop(self):
        self.selector = selectors.DefaultSelector()
        try:
            for device in self.keyboard_devices:
                try: self.selector.register(device, selectors.EVENT_READ)
                except: pass
            while not self._stop_event.is_set():
                try:
                    for key, _ in self.selector.select(timeout=0.1):
                        if self._stop_event.is_set(): break
                        try:
                            for event in key.fileobj.read():
                                if event.type == ecodes.EV_KEY:
                                    self._handle_key(event)
                        except: pass
                except: break
        finally:
            try: self.selector.close()
            except: pass
            self.selector = None
    
    def _handle_key(self, event):
        modifier_map = {ecodes.KEY_RIGHTCTRL: ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTALT: ecodes.KEY_LEFTALT,
                        ecodes.KEY_RIGHTSHIFT: ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTMETA: ecodes.KEY_LEFTMETA}
        code = modifier_map.get(event.code, event.code)
        if event.value == 1:
            self.pressed_keys.add(code)
            if self.required_keys.issubset(self.pressed_keys):
                now = time.time()
                if now - self._last_trigger_time >= self._debounce_interval:
                    self._last_trigger_time = now
                    logger.info(f"Hotkey triggered: {self.hotkey_string}")
                    if self.callback:
                        threading.Thread(target=self.callback, daemon=True).start()
        elif event.value == 0:
            self.pressed_keys.discard(code)
