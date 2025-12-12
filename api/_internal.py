"""
Internal module - all implementation details hidden from outline.
"""
import os
import sys
import time
import threading
import signal
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import BaseModel
import evdev
from evdev import ecodes, InputDevice
import socketio

from src.core.device_manager import DeviceManager, DeviceType
from src.core.config_manager import ConfigManager


# =============================================================================
# SIMPLE BLOCKER - Inline implementation for reliability
# =============================================================================

class _Blocker:
    def __init__(self, on_change: Optional[Callable[[bool], None]] = None):
        self.is_locked = False
        self.on_change = on_change
        self.grabbed: Dict[str, InputDevice] = {}
        self.hotkey_thread: Optional[threading.Thread] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.running = False
        self.reader_running = False
        self.pressed: set = set()
        self.pattern_seq: List[int] = []
        self.pattern_time = 0.0
        self.last_lock = 0.0
        
        # Pattern: Up Up Down Down Enter
        self.PATTERN = [ecodes.KEY_UP, ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_DOWN, ecodes.KEY_ENTER]
        # Default hotkey: Ctrl+Alt+L (can be overridden from config)
        self.hotkey_string = "Ctrl+Alt+L"
        self.HOTKEY = {ecodes.KEY_LEFTCTRL, ecodes.KEY_LEFTALT, ecodes.KEY_L}

    def set_hotkey_from_string(self, hotkey_string: str):
        """Update the hotkey key set based on a string like "Ctrl+Alt+L".

        For reliability across keyboard layouts we currently support:
        - Modifiers: Ctrl / Alt / Shift / Super
        - A single non-modifier key: letters A–Z

        If we cannot detect any non-modifier key (for example "Ctrl+Alt+Ç"),
        we fall back to the safe default Ctrl+Alt+L.
        """
        if not hotkey_string:
            hotkey_string = "Ctrl+Alt+L"

        key_map = {
            'ctrl': ecodes.KEY_LEFTCTRL,
            'control': ecodes.KEY_LEFTCTRL,
            'alt': ecodes.KEY_LEFTALT,
            'shift': ecodes.KEY_LEFTSHIFT,
            'super': ecodes.KEY_LEFTMETA,
            'win': ecodes.KEY_LEFTMETA,
            'cmd': ecodes.KEY_LEFTMETA,
            # Best-effort mapping for Ç / ç key on Latin layouts.
            # On many keyboards this shares the physical key with ';' or '''.
            'ç': getattr(ecodes, 'KEY_APOSTROPHE', None) or getattr(ecodes, 'KEY_SEMICOLON', None),
            'cedilla': getattr(ecodes, 'KEY_APOSTROPHE', None) or getattr(ecodes, 'KEY_SEMICOLON', None),
        }

        # Add letters a-z as valid non-modifier keys
        for i in range(ord('a'), ord('z') + 1):
            ch = chr(i)
            code = getattr(ecodes, f"KEY_{ch.upper()}", None)
            if code is not None:
                key_map[ch] = code

        parts = [p.strip().lower() for p in hotkey_string.split('+') if p.strip()]
        new_set = set()
        has_non_modifier = False

        modifier_codes = {
            ecodes.KEY_LEFTCTRL,
            ecodes.KEY_LEFTALT,
            ecodes.KEY_LEFTSHIFT,
            ecodes.KEY_LEFTMETA,
        }

        for part in parts:
            code = key_map.get(part)
            if code is None:
                continue
            new_set.add(code)
            if code not in modifier_codes:
                has_non_modifier = True

        # Require at least one non-modifier key; otherwise, fall back
        if not new_set or not has_non_modifier:
            new_set = {ecodes.KEY_LEFTCTRL, ecodes.KEY_LEFTALT, ecodes.KEY_L}
            hotkey_string = "Ctrl+Alt+L"

        self.HOTKEY = new_set
        self.hotkey_string = hotkey_string
    
    def _is_touchscreen(self, caps: Dict) -> bool:
        """Check if device is a touchscreen based on multi-touch capabilities."""
        if ecodes.EV_ABS not in caps:
            return False
        
        abs_events = caps[ecodes.EV_ABS]
        
        # Multi-touch events that identify touchscreens
        multitouch_events = {
            ecodes.ABS_MT_POSITION_X,
            ecodes.ABS_MT_POSITION_Y,
            ecodes.ABS_MT_SLOT,
            ecodes.ABS_MT_TRACKING_ID
        }
        
        # If has at least 2 multi-touch events, it's a touchscreen
        found = sum(1 for event in multitouch_events 
                   if any(e[0] == event if isinstance(e, tuple) else e == event for e in abs_events))
        return found >= 2
    
    def start(self):
        if self.running:
            return
        self.running = True
        self.hotkey_thread = threading.Thread(target=self._hotkey_loop, daemon=True)
        self.hotkey_thread.start()
        print(f"🎮 Hotkey listener active ({self.hotkey_string})")
    
    def stop(self):
        self.running = False
        self.reader_running = False
        self.unlock()
    
    def _find_keyboards(self) -> List[InputDevice]:
        kbs = []
        for p in evdev.list_devices():
            try:
                d = InputDevice(p)
                caps = d.capabilities(verbose=False)
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    if ecodes.KEY_A in keys and ecodes.KEY_ENTER in keys:
                        kbs.append(d)
                    else:
                        d.close()
                else:
                    d.close()
            except:
                pass
        return kbs
    
    def _hotkey_loop(self):
        import select
        while self.running:
            if self.is_locked:
                time.sleep(0.1)
                continue
            
            kbs = self._find_keyboards()
            if not kbs:
                time.sleep(1)
                continue
            
            try:
                fds = {kb.fd: kb for kb in kbs}
                while self.running and not self.is_locked:
                    r, _, _ = select.select(list(fds.keys()), [], [], 0.1)
                    for fd in r:
                        kb = fds.get(fd)
                        if kb:
                            try:
                                for ev in kb.read():
                                    if ev.type == ecodes.EV_KEY:
                                        self._check_hotkey(ev)
                            except:
                                pass
            finally:
                for kb in kbs:
                    try:
                        kb.close()
                    except:
                        pass
    
    def _check_hotkey(self, ev):
        code = ev.code
        if code == ecodes.KEY_RIGHTCTRL:
            code = ecodes.KEY_LEFTCTRL
        elif code == ecodes.KEY_RIGHTALT:
            code = ecodes.KEY_LEFTALT
        
        if ev.value == 1:
            self.pressed.add(code)
            if self.HOTKEY.issubset(self.pressed):
                now = time.time()
                if now - self.last_lock > 0.5:
                    self.last_lock = now
                    print(f"🔒 {self.hotkey_string} - Locking")
                    self.lock()
        elif ev.value == 0:
            self.pressed.discard(code)
    
    def lock(self):
        if self.is_locked:
            return
        
        self.pressed.clear()
        
        for p in evdev.list_devices():
            try:
                d = InputDevice(p)
                caps = d.capabilities(verbose=False)
                if ecodes.EV_KEY not in caps:
                    d.close()
                    continue
                
                keys = caps[ecodes.EV_KEY]
                is_kb = ecodes.KEY_A in keys and ecodes.KEY_ENTER in keys
                is_mouse = ecodes.BTN_LEFT in keys or ecodes.BTN_MOUSE in keys
                
                # Check if it's a touchscreen (has multi-touch absolute events)
                is_touchscreen = self._is_touchscreen(caps)
                
                if is_touchscreen:
                    print(f"  ⏭️ Skipping touchscreen: {d.name}")
                    d.close()
                    continue
                
                if is_kb or is_mouse:
                    d.grab()
                    self.grabbed[p] = d
                    print(f"  ✓ Grabbed: {d.name}")
                else:
                    d.close()
            except:
                pass
        
        self.is_locked = True
        self.pattern_seq = []
        
        # Start pattern detection
        self.reader_running = True
        self.reader_thread = threading.Thread(target=self._pattern_loop, daemon=True)
        self.reader_thread.start()
        
        print(f"🔐 Locked {len(self.grabbed)} devices. Press ↑↑↓↓Enter to unlock")
        
        if self.on_change:
            threading.Timer(0.05, lambda: self.on_change(True)).start()
    
    def lock_by_types(self, types: List[str], device_manager):
        """Lock only devices of specific types."""
        if self.is_locked:
            self.unlock()  # First unlock all
        
        self.pressed.clear()
        
        # Get all devices with their types from device_manager
        all_devices = device_manager.get_all_devices()
        device_types_map = {d.path: d.device_type.value for d in all_devices}
        
        print(f"🔒 Locking by types: {types}")
        
        for p in evdev.list_devices():
            try:
                d = InputDevice(p)
                caps = d.capabilities(verbose=False)
                if ecodes.EV_KEY not in caps:
                    d.close()
                    continue
                
                keys = caps[ecodes.EV_KEY]
                is_kb = ecodes.KEY_A in keys and ecodes.KEY_ENTER in keys
                is_mouse = ecodes.BTN_LEFT in keys or ecodes.BTN_MOUSE in keys
                is_touchscreen = self._is_touchscreen(caps)
                
                # Get device type from device_manager
                device_type = device_types_map.get(p, None)
                
                # Fallback classification if not in device_manager
                if not device_type:
                    if is_touchscreen:
                        device_type = 'touchscreen'
                    elif is_kb:
                        device_type = 'keyboard'
                    elif is_mouse:
                        device_type = 'mouse'
                
                # Check if this device type should be blocked
                should_block = device_type in types
                
                if not should_block:
                    d.close()
                    continue
                
                # Skip touchscreens if not explicitly requested
                if is_touchscreen and 'touchscreen' not in types:
                    print(f"  ⏭️ Skipping touchscreen: {d.name}")
                    d.close()
                    continue
                
                if is_kb or is_mouse or is_touchscreen:
                    d.grab()
                    self.grabbed[p] = d
                    print(f"  ✓ Grabbed ({device_type}): {d.name}")
                else:
                    d.close()
            except Exception as e:
                print(f"  ❌ Error with device: {e}")
        
        if self.grabbed:
            self.is_locked = True
            self.pattern_seq = []
            
            # Start pattern detection
            self.reader_running = True
            self.reader_thread = threading.Thread(target=self._pattern_loop, daemon=True)
            self.reader_thread.start()
            
            print(f"🔐 Profile locked {len(self.grabbed)} devices. Press ↑↑↓↓Enter to unlock")
            
            if self.on_change:
                threading.Timer(0.05, lambda: self.on_change(True)).start()
        else:
            print("⚠️ No devices matched the specified types")
    
    def unlock(self):
        if not self.is_locked:
            return
        
        self.reader_running = False
        
        for p, d in list(self.grabbed.items()):
            try:
                d.ungrab()
                d.close()
            except:
                pass
        
        self.grabbed.clear()
        self.is_locked = False
        self.pattern_seq = []
        
        # Clear stuck keys
        try:
            import subprocess
            for k in ['ctrl', 'alt', 'shift', 'super']:
                subprocess.run(['xdotool', 'keyup', k], capture_output=True, timeout=0.5)
        except:
            pass
        
        print("🔓 Unlocked")
        
        if self.on_change:
            threading.Timer(0.05, lambda: self.on_change(False)).start()
    
    def _pattern_loop(self):
        """Pattern detection loop - reads from grabbed keyboards."""
        import select
        
        print("📖 Pattern detection started")
        
        while self.reader_running and self.is_locked:
            # Get current keyboards from grabbed devices
            kbs = []
            for p, d in list(self.grabbed.items()):
                try:
                    caps = d.capabilities(verbose=False)
                    if ecodes.EV_KEY in caps:
                        keys = caps[ecodes.EV_KEY]
                        if ecodes.KEY_A in keys:
                            kbs.append(d)
                except:
                    pass
            
            if not kbs:
                time.sleep(0.1)
                continue
            
            try:
                fds = {kb.fd: kb for kb in kbs if kb.fd is not None}
                if not fds:
                    time.sleep(0.1)
                    continue
                
                # Use select with timeout
                r, _, _ = select.select(list(fds.keys()), [], [], 0.05)
                
                for fd in r:
                    if not self.reader_running:
                        return
                    
                    kb = fds.get(fd)
                    if not kb:
                        continue
                    
                    try:
                        # Read events
                        for ev in kb.read():
                            if ev.type == ecodes.EV_KEY and ev.value == 1:  # Key press
                                if self._check_pattern(ev.code):
                                    print("🎮 Pattern matched!")
                                    self.unlock()
                                    return
                    except BlockingIOError:
                        pass
                    except Exception as e:
                        print(f"Read error: {e}")
                        
            except Exception as e:
                print(f"Pattern loop error: {e}")
                time.sleep(0.05)
    
    def _check_pattern(self, code: int) -> bool:
        now = time.time()
        
        # Reset on timeout
        if now - self.pattern_time > 3.0:
            self.pattern_seq = []
        
        self.pattern_time = now
        
        pos = len(self.pattern_seq)
        if pos >= len(self.PATTERN):
            self.pattern_seq = []
            pos = 0
        
        expected = self.PATTERN[pos]
        
        if code == expected:
            self.pattern_seq.append(code)
            names = {ecodes.KEY_UP: "↑", ecodes.KEY_DOWN: "↓", ecodes.KEY_ENTER: "Enter"}
            print(f"  Pattern {len(self.pattern_seq)}/{len(self.PATTERN)}: {names.get(code, code)}")
            
            if len(self.pattern_seq) == len(self.PATTERN):
                self.pattern_seq = []
                return True
        else:
            # Reset on wrong key (ignore modifiers)
            if code not in [ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL, ecodes.KEY_LEFTALT, 
                           ecodes.KEY_RIGHTALT, ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT]:
                if self.pattern_seq:
                    print("  Pattern reset")
                self.pattern_seq = []
        
        return False


# =============================================================================
# DEVICE MANAGER WRAPPER
# =============================================================================

class _Manager:
    def __init__(self):
        self.device_manager = DeviceManager()
        self.config_manager = ConfigManager()
        self.blocker = _Blocker(on_change=self._on_change)
        self.pending: List[Dict] = []
        self.lock = threading.Lock()
        self.timer_active = False
        self.timer_end: Optional[float] = None
        self.timer_total = 0
        self.timer_thread: Optional[threading.Thread] = None
        self.start_time = time.time()
        self.stats = {'total_blocked_time': 0, 'blocked_events': 0, 'block_history': []}
        self.block_start: Optional[float] = None
        
        # Initialize hotkey from config (default Ctrl+Alt+L) and normalize
        try:
            hotkey_raw = self.config_manager.get('general', 'hotkey', 'Ctrl+Alt+L')
            if isinstance(hotkey_raw, list):
                requested = ' + '.join(str(p).strip() for p in hotkey_raw if str(p).strip()) or 'Ctrl+Alt+L'
            else:
                requested = str(hotkey_raw) or 'Ctrl+Alt+L'

            # Configure blocker from requested string
            self.blocker.set_hotkey_from_string(requested)

            # If the blocker had to fall back (e.g. unsupported key like Ç),
            # persist the canonical hotkey so API/UI reflect the real combo.
            if self.blocker.hotkey_string != requested:
                self.config_manager.set('general', 'hotkey', self.blocker.hotkey_string)
                self.config_manager.save()
        except Exception:
            # Fallback to default if config is missing or invalid
            self.blocker.set_hotkey_from_string('Ctrl+Alt+L')

        self.blocker.start()
        print("✅ Manager ready")
    
    def _on_change(self, locked: bool):
        action = 'locked' if locked else 'unlocked'
        
        if locked:
            self.block_start = time.time()
            self.stats['blocked_events'] += 1
        else:
            if self.block_start:
                self.stats['total_blocked_time'] += time.time() - self.block_start
                self.block_start = None
        
        self.stats['block_history'].append({'timestamp': datetime.now().isoformat(), 'action': action})
        
        with self.lock:
            self.pending.append({
                'type': 'pattern' if not locked else 'hotkey',
                'action': action,
            })
    
    def get_pending(self) -> List[Dict]:
        with self.lock:
            events = self.pending.copy()
            self.pending.clear()
            return events
    
    def get_devices(self) -> List[Dict]:
        devices = self.device_manager.get_all_devices()
        result = []
        for d in devices:
            blocked = d.path in self.blocker.grabbed
            result.append({
                'id': d.path,
                'path': d.path,
                'name': d.name,
                'type': d.device_type.value if hasattr(d.device_type, 'value') else str(d.device_type),
                'blocked': blocked,
                'physicalPath': getattr(d, 'physical_path', ''),
                'capabilities': list(d.capabilities) if hasattr(d, 'capabilities') else [],
            })
        return result
    
    def block_all(self) -> bool:
        if not self.blocker.is_locked:
            self.blocker.lock()
        return True
    
    def unblock_all(self) -> bool:
        if self.blocker.is_locked:
            self.blocker.unlock()
        return True
    
    def toggle(self) -> bool:
        if self.blocker.is_locked:
            return self.unblock_all()
        return self.block_all()
    
    def lock_by_types(self, types: List[str]) -> bool:
        """Lock only devices of specific types."""
        self.blocker.lock_by_types(types, self.device_manager)
        return True
    
    def set_timer(self, minutes: int) -> Dict:
        self.timer_total = minutes * 60
        self.timer_end = time.time() + self.timer_total
        self.timer_active = True
        self.block_all()
        
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_active = False
            self.timer_thread.join(timeout=1)
            self.timer_active = True
        
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
        return self.timer_status()
    
    def _timer_loop(self):
        while self.timer_active and self.timer_end:
            if time.time() >= self.timer_end:
                self.unblock_all()
                self.timer_active = False
                self.timer_end = None
                break
            time.sleep(1)
    
    def cancel_timer(self) -> bool:
        self.timer_active = False
        self.timer_end = None
        return True
    
    def timer_status(self) -> Dict:
        if not self.timer_active or not self.timer_end:
            return {'active': False, 'remainingSeconds': 0, 'totalSeconds': 0}
        remaining = max(0, int(self.timer_end - time.time()))
        return {'active': True, 'remainingSeconds': remaining, 'totalSeconds': self.timer_total}
    
    def statistics(self) -> Dict:
        t = self.stats['total_blocked_time']
        if self.block_start:
            t += time.time() - self.block_start
        return {
            'totalBlockedTime': int(t),
            'blockedEvents': self.stats['blocked_events'],
            'blockHistory': self.stats['block_history'][-50:],
            'deviceStats': [],
        }
    
    def system_status(self) -> Dict:
        return {
            'running': True,
            'activeBlocks': len(self.blocker.grabbed),
            'connectedDevices': len(self.device_manager.get_all_devices()),
            'uptime': int(time.time() - self.start_time),
        }
    
    def get_settings(self) -> Dict:
        # Hotkey is stored as a single string like "Ctrl+Alt+L" under general.hotkey
        hotkey_raw = self.config_manager.get('general', 'hotkey', 'Ctrl+Alt+L')
        if isinstance(hotkey_raw, str):
            hotkey = [p.strip() for p in hotkey_raw.split('+') if p.strip()]
            if not hotkey:
                hotkey = ['Ctrl', 'Alt', 'L']
        elif isinstance(hotkey_raw, list):
            # Backward compatibility with older flat list configs
            hotkey = [str(p).strip() for p in hotkey_raw if str(p).strip()]
        else:
            hotkey = ['Ctrl', 'Alt', 'L']

        # Emergency pattern: keep as list of human-readable steps
        pattern = self.config_manager.get(
            'general',
            'pattern_sequence',
            ['Up', 'Up', 'Down', 'Down', 'Enter'],
        )
        if not isinstance(pattern, list):
            pattern = ['Up', 'Up', 'Down', 'Down', 'Enter']

        auto_block = bool(self.config_manager.get('general', 'autostart_blocked', False))
        show_notif = bool(self.config_manager.get('general', 'show_notifications', True))
        allow_touch = bool(self.config_manager.get('devices', 'allow_touchscreens', True))
        theme = self.config_manager.get('ui', 'theme', 'dark')

        return {
            'hotkey': hotkey,
            'emergencyPattern': pattern,
            'autoBlockOnStart': auto_block,
            'showNotifications': show_notif,
            'allowTouchscreenUnlock': allow_touch,
            'theme': theme,
        }
    
    def update_settings(self, settings: Dict) -> Dict:
        # Map API keys to (section, key) in the JSON config
        mapping: Dict[str, tuple[str, str]] = {
            'hotkey': ('general', 'hotkey'),
            'emergencyPattern': ('general', 'pattern_sequence'),
            'autoBlockOnStart': ('general', 'autostart_blocked'),
            'showNotifications': ('general', 'show_notifications'),
            'allowTouchscreenUnlock': ('devices', 'allow_touchscreens'),
            'theme': ('ui', 'theme'),
        }

        # Track whether we changed the hotkey so we can re-apply it live
        hotkey_updated = False
        requested_hotkey_str: Optional[str] = None

        for k, v in settings.items():
            if k not in mapping or v is None:
                continue

            section, key = mapping[k]

            # Hotkey: convert list of parts to single string "Ctrl+Alt+L"
            if k == 'hotkey':
                if isinstance(v, list):
                    value = ' + '.join(str(p).strip() for p in v if str(p).strip()) or 'Ctrl+Alt+L'
                else:
                    value = str(v) or 'Ctrl+Alt+L'
                hotkey_updated = True
                requested_hotkey_str = value
            else:
                value = v

            try:
                self.config_manager.set(section, key, value)
            except Exception:
                # Do not fail the whole request if one field cannot be written
                continue

        self.config_manager.save()

        # If the hotkey changed, update the live blocker configuration
        if hotkey_updated and requested_hotkey_str is not None:
            try:
                # Configure blocker from the requested string
                self.blocker.set_hotkey_from_string(requested_hotkey_str)

                # If the blocker had to fall back (e.g. unsupported key),
                # persist the canonical hotkey so API/UI reflect reality.
                if self.blocker.hotkey_string != requested_hotkey_str:
                    self.config_manager.set('general', 'hotkey', self.blocker.hotkey_string)
                    self.config_manager.save()
            except Exception:
                pass

        return self.get_settings()
    
    def cleanup(self):
        self.blocker.stop()


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class DeviceBlockRequest(BaseModel):
    device_path: str

class LockTypesRequest(BaseModel):
    types: List[str]  # ['keyboard', 'mouse', 'touchpad', 'touchscreen']

class TimerRequest(BaseModel):
    minutes: int
    device_path: Optional[str] = None

class SettingsUpdate(BaseModel):
    hotkey: Optional[List[str]] = None
    emergencyPattern: Optional[List[str]] = None
    autoBlockOnStart: Optional[bool] = None
    showNotifications: Optional[bool] = None
    allowTouchscreenUnlock: Optional[bool] = None
    theme: Optional[str] = None

class WhitelistEntry(BaseModel):
    devicePath: str
    deviceName: str
    enabled: bool = True


# Singleton manager
_manager_instance: Optional[_Manager] = None

def get_manager() -> _Manager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = _Manager()
    return _manager_instance
