"""
Simple device blocker with hotkey support.
Ctrl+Alt+L to lock, Up+Up+Down+Down+Enter to unlock.
"""

import threading
import time
import evdev
from evdev import ecodes, InputDevice
from typing import Optional, Callable, Dict, Set
import sys

def log(msg):
    """Log to stderr and flush immediately."""
    print(msg, file=sys.stderr, flush=True)
    print(msg, flush=True)

class SimpleBlocker:
    """Simple device blocker that actually works."""
    
    def __init__(self, on_lock_change: Optional[Callable[[bool], None]] = None):
        self.is_locked = False
        self.on_lock_change = on_lock_change
        
        # Grabbed devices
        self.grabbed_devices: Dict[str, InputDevice] = {}
        
        # Hotkey detection (Ctrl+Alt+L)
        self.hotkey_thread: Optional[threading.Thread] = None
        self.hotkey_running = False
        self.pressed_keys: Set[int] = set()
        self.hotkey_keys = {ecodes.KEY_LEFTCTRL, ecodes.KEY_LEFTALT, ecodes.KEY_L}
        
        # Pattern detection (Up Up Down Down Enter)
        self.pattern = [ecodes.KEY_UP, ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_DOWN, ecodes.KEY_ENTER]
        self.pattern_sequence = []
        self.pattern_last_time = 0
        self.pattern_timeout = 3.0
        
        # Event reader thread for blocked devices
        self.reader_thread: Optional[threading.Thread] = None
        self.reader_running = False
        
        # Debounce
        self.last_lock_time = 0
        self.debounce_interval = 0.5
    
    def start_hotkey_listener(self):
        """Start listening for Ctrl+Alt+L to lock."""
        if self.hotkey_running:
            return
        
        self.hotkey_running = True
        self.hotkey_thread = threading.Thread(target=self._hotkey_loop, daemon=True)
        self.hotkey_thread.start()
        print("🎮 Hotkey listener started (Ctrl+Alt+L to lock)")
    
    def stop_hotkey_listener(self):
        """Stop the hotkey listener."""
        self.hotkey_running = False
        if self.hotkey_thread:
            self.hotkey_thread.join(timeout=0.5)
    
    def _find_keyboards(self):
        """Find all keyboard devices."""
        keyboards = []
        for path in evdev.list_devices():
            try:
                device = InputDevice(path)
                caps = device.capabilities(verbose=False)
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    if ecodes.KEY_A in keys and ecodes.KEY_ENTER in keys:
                        keyboards.append(device)
            except:
                pass
        return keyboards
    
    def _hotkey_loop(self):
        """Listen for Ctrl+Alt+L when not locked."""
        import selectors
        
        while self.hotkey_running:
            if self.is_locked:
                time.sleep(0.1)
                continue
            
            keyboards = self._find_keyboards()
            if not keyboards:
                time.sleep(1)
                continue
            
            sel = selectors.DefaultSelector()
            for kb in keyboards:
                try:
                    sel.register(kb, selectors.EVENT_READ)
                except:
                    pass
            
            try:
                while self.hotkey_running and not self.is_locked:
                    events = sel.select(timeout=0.1)
                    for key, _ in events:
                        try:
                            for event in key.fileobj.read():
                                if event.type == ecodes.EV_KEY:
                                    self._check_hotkey(event)
                        except:
                            pass
            except:
                pass
            finally:
                sel.close()
                for kb in keyboards:
                    try:
                        kb.close()
                    except:
                        pass
    
    def _check_hotkey(self, event):
        """Check if Ctrl+Alt+L is pressed."""
        code = event.code
        # Normalize right modifiers to left
        if code == ecodes.KEY_RIGHTCTRL:
            code = ecodes.KEY_LEFTCTRL
        elif code == ecodes.KEY_RIGHTALT:
            code = ecodes.KEY_LEFTALT
        
        if event.value == 1:  # Press
            self.pressed_keys.add(code)
            if self.hotkey_keys.issubset(self.pressed_keys):
                now = time.time()
                if now - self.last_lock_time >= self.debounce_interval:
                    self.last_lock_time = now
                    print("🔒 Ctrl+Alt+L detected - Locking...")
                    self.lock_all()
        elif event.value == 0:  # Release
            self.pressed_keys.discard(code)
    
    def lock_all(self):
        """Lock all keyboard and mouse devices."""
        if self.is_locked:
            return
        
        self.pressed_keys.clear()
        
        # Find and grab keyboards and mice
        for path in evdev.list_devices():
            try:
                device = InputDevice(path)
                caps = device.capabilities(verbose=False)
                
                if ecodes.EV_KEY not in caps:
                    device.close()
                    continue
                
                keys = caps[ecodes.EV_KEY]
                
                # Is it a keyboard?
                is_keyboard = ecodes.KEY_A in keys and ecodes.KEY_ENTER in keys
                # Is it a mouse?
                is_mouse = ecodes.BTN_LEFT in keys or ecodes.BTN_MOUSE in keys
                
                if is_keyboard or is_mouse:
                    device.grab()
                    self.grabbed_devices[path] = device
                    device_type = "keyboard" if is_keyboard else "mouse"
                    print(f"  ✓ Grabbed {device_type}: {device.name}")
                else:
                    device.close()
            except Exception as e:
                pass
        
        self.is_locked = True
        self.pattern_sequence = []
        
        # Start reading events for pattern detection
        self.reader_running = True
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()
        
        print(f"🔐 Locked {len(self.grabbed_devices)} devices")
        print("💡 Use ↑↑↓↓Enter to unlock")
        
        # Notify after a small delay to ensure state is fully updated
        if self.on_lock_change:
            import threading
            threading.Timer(0.05, lambda: self.on_lock_change(True)).start()
    
    def unlock_all(self):
        """Unlock all devices."""
        if not self.is_locked:
            return
        
        self.reader_running = False
        
        # Release all grabbed devices
        for path, device in list(self.grabbed_devices.items()):
            try:
                device.ungrab()
                device.close()
                print(f"  ✓ Released: {device.name}")
            except:
                pass
        
        self.grabbed_devices.clear()
        self.is_locked = False
        self.pattern_sequence = []
        
        # Clear any stuck keys
        self._clear_stuck_keys()
        
        print("🔓 All devices unlocked")
        
        # Notify after state is fully updated
        if self.on_lock_change:
            threading.Timer(0.05, lambda: self.on_lock_change(False)).start()
    
    def _reader_loop(self):
        """Read events from grabbed devices to detect unlock pattern."""
        log("📖 Reader loop started for pattern detection")
        
        while self.reader_running and self.is_locked:
            devices = list(self.grabbed_devices.values())
            if not devices:
                log("⚠️ No grabbed devices found")
                time.sleep(0.1)
                continue
            
            # Only use keyboards for pattern detection
            keyboards = []
            for dev in devices:
                try:
                    caps = dev.capabilities(verbose=False)
                    if ecodes.EV_KEY in caps:
                        keys = caps[ecodes.EV_KEY]
                        if ecodes.KEY_A in keys:
                            keyboards.append(dev)
                except Exception as e:
                    log(f"⚠️ Error checking device caps: {e}")
            
            if not keyboards:
                log("⚠️ No keyboards found in grabbed devices")
                time.sleep(0.1)
                continue
            
            log(f"⌨️ Monitoring {len(keyboards)} keyboard(s): {[kb.name for kb in keyboards]}")
            
            # Read from each keyboard in a simple loop
            try:
                # Keep checking all keyboards
                while self.reader_running and self.is_locked:
                    found_event = False
                    for kb in keyboards:
                        try:
                            # Try to read one event (non-blocking)
                            event = kb.read_one()
                            if event is not None:
                                found_event = True
                                if event.type == ecodes.EV_KEY and event.value == 1:
                                    key_name = ecodes.KEY.get(event.code, event.code)
                                    log(f"🔑 Key: {key_name} ({event.code})")
                                    if self._check_pattern(event.code):
                                        log("🎮 Pattern complete - Unlocking...")
                                        self.unlock_all()
                                        return
                        except BlockingIOError:
                            # No events available, continue
                            pass
                        except OSError as e:
                            if e.errno == 19:  # No such device
                                log(f"⚠️ Device disconnected: {kb.name}")
                            else:
                                log(f"⚠️ OSError reading {kb.name}: {e}")
                        except Exception as e:
                            log(f"⚠️ Error reading from {kb.name}: {e}")
                    
                    # Small sleep if no events found to avoid busy-wait
                    if not found_event:
                        time.sleep(0.01)
                        
            except Exception as e:
                log(f"⚠️ Reader loop error: {e}")
                time.sleep(0.1)
    
    def _check_pattern(self, key_code) -> bool:
        """Check if the unlock pattern is being entered."""
        now = time.time()
        
        # Reset if timeout
        if now - self.pattern_last_time > self.pattern_timeout:
            self.pattern_sequence = []
        
        self.pattern_last_time = now
        
        expected_pos = len(self.pattern_sequence)
        if expected_pos >= len(self.pattern):
            self.pattern_sequence = []
            expected_pos = 0
        
        expected_key = self.pattern[expected_pos]
        
        if key_code == expected_key:
            self.pattern_sequence.append(key_code)
            key_name = {
                ecodes.KEY_UP: "↑",
                ecodes.KEY_DOWN: "↓",
                ecodes.KEY_ENTER: "Enter"
            }.get(key_code, str(key_code))
            print(f"  Pattern: {len(self.pattern_sequence)}/{len(self.pattern)} - {key_name}")
            
            if len(self.pattern_sequence) == len(self.pattern):
                self.pattern_sequence = []
                return True
        else:
            # Wrong key - only reset if it's not a modifier
            if key_code not in [ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL, 
                               ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT,
                               ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT]:
                if self.pattern_sequence:
                    print(f"  Pattern reset (wrong key)")
                self.pattern_sequence = []
        
        return False
    
    def _clear_stuck_keys(self):
        """Clear any stuck modifier keys."""
        import subprocess
        try:
            for key in ['ctrl', 'alt', 'shift', 'super']:
                subprocess.run(['xdotool', 'keyup', key], 
                             capture_output=True, timeout=0.5)
            print("🧹 Cleared stuck keys")
        except:
            pass
    
    def cleanup(self):
        """Clean shutdown."""
        print("🛑 Cleaning up...")
        self.hotkey_running = False
        self.reader_running = False
        self.unlock_all()
        if self.hotkey_thread:
            self.hotkey_thread.join(timeout=0.3)
        print("✅ Cleanup complete")
