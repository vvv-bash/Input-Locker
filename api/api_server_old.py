"""
API Server for Input Locker Web Interface

This module provides a REST API and WebSocket server that integrates with the existing 
Input Locker Python modules (DeviceManager, InputBlocker, ConfigManager).

Run from project root: python api/api_server.py
"""

import os
import sys
import json
import time
import threading
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Add project root to path for imports (same pattern as main.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Socket.IO for real-time updates
import socketio

# Import existing modules
import evdev
from src.core.device_manager import DeviceManager, DeviceType
from src.core.config_manager import ConfigManager

# Import simple blocker
from api.simple_blocker import SimpleBlocker


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models for API
# ═══════════════════════════════════════════════════════════════════════════════

class DeviceBlockRequest(BaseModel):
    device_path: str


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


# ═══════════════════════════════════════════════════════════════════════════════
# Device Blocker Manager - Wraps existing modules
# ═══════════════════════════════════════════════════════════════════════════════

class DeviceBlockerManager:
    """Manages device blocking without requiring Qt - standalone for API"""
    
    def __init__(self):
        self.device_manager = DeviceManager()
        self.config_manager = ConfigManager()
        
        # Track blocked devices (path -> blocked state)
        self.blocked_devices: Dict[str, bool] = {}
        self.grabbed_devices: Dict[str, Any] = {}
        
        # Timer
        self.timer_active = False
        self.timer_end_time: Optional[float] = None
        self.timer_total_seconds = 0
        self.timer_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'total_blocked_time': 0,
            'blocked_events': 0,
            'block_history': [],
            'device_stats': {},
        }
        self.block_start_times: Dict[str, float] = {}
        
        # Server start time
        self.start_time = time.time()
        
        # Pending events queue for WebSocket emission
        self._pending_events: List[Dict] = []
        
        # Hotkey configuration
        try:
            hotkey_config = self.config_manager.config.get('hotkey', ['Ctrl', 'Alt', 'L'])
        except:
            hotkey_config = ['Ctrl', 'Alt', 'L']
        
        if hotkey_config is None or not isinstance(hotkey_config, list):
            hotkey_config = ['Ctrl', 'Alt', 'L']
        
        self.hotkey_string = '+'.join(hotkey_config)
        
        # Use lightweight hotkey handler that doesn't grab devices
        self.hotkey_handler = HotkeyHandlerLite(self.hotkey_string)
        self.hotkey_handler.set_callback(self._on_hotkey_triggered)
        self.hotkey_handler.start()
        
        # Pattern configuration
        try:
            pattern_config = self.config_manager.config.get('pattern_sequence', ['Up', 'Up', 'Down', 'Down', 'Enter'])
        except:
            pattern_config = ['Up', 'Up', 'Down', 'Down', 'Enter']
        
        if pattern_config is None or not isinstance(pattern_config, list):
            pattern_config = ['Up', 'Up', 'Down', 'Down', 'Enter']
        
        self.pattern_codes = self._parse_pattern(pattern_config)
        
        # Initialize pattern unlocker for detecting unlock sequence
        self.pattern_unlocker = PatternUnlocker(
            callback=self._on_pattern_unlock,
            pattern=self.pattern_codes,
            timeout=3.0
        )
        
        print("Hotkey listener started: Ctrl+Alt+L to lock")
        
    def _parse_pattern(self, pattern_list: List[str]) -> List[int]:
        """Convert pattern string list to evdev key codes"""
        from evdev import ecodes
        key_map = {
            'up': ecodes.KEY_UP,
            'down': ecodes.KEY_DOWN,
            'left': ecodes.KEY_LEFT,
            'right': ecodes.KEY_RIGHT,
            'enter': ecodes.KEY_ENTER,
            'space': ecodes.KEY_SPACE,
            'esc': ecodes.KEY_ESC,
            'escape': ecodes.KEY_ESC,
            'a': ecodes.KEY_A, 'b': ecodes.KEY_B, 'c': ecodes.KEY_C,
            'd': ecodes.KEY_D, 'e': ecodes.KEY_E, 'f': ecodes.KEY_F,
            'g': ecodes.KEY_G, 'h': ecodes.KEY_H, 'i': ecodes.KEY_I,
            'j': ecodes.KEY_J, 'k': ecodes.KEY_K, 'l': ecodes.KEY_L,
        }
        codes = []
        for key in pattern_list:
            key_lower = key.lower()
            if key_lower in key_map:
                codes.append(key_map[key_lower])
        return codes if codes else [ecodes.KEY_UP, ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_DOWN, ecodes.KEY_ENTER]
    
    def _on_hotkey_triggered(self):
        """Called when the lock hotkey (Ctrl+Alt+L) is pressed - ONLY LOCKS"""
        # Check if already blocked - if so, do nothing (use pattern to unlock)
        any_blocked = any(self.blocked_devices.values())
        
        if any_blocked:
            print("🔒 Devices already locked. Use pattern (↑↑↓↓Enter) to unlock.")
            return
        
        print("🔒 Hotkey triggered! Locking all devices...")
        self.block_all()
        print("🔐 All devices locked via Ctrl+Alt+L")
        print("💡 Use pattern ↑↑↓↓Enter to unlock")
        
        # Queue event for WebSocket emission
        self._pending_events.append({
            'type': 'hotkey_action',
            'action': 'locked',
            'devices': self.get_devices(),
            'status': self.get_system_status()
        })
    
    def _on_pattern_unlock(self):
        """Called when the unlock pattern (UP UP DOWN DOWN ENTER) is detected"""
        print("🔓 Pattern unlock triggered! Unlocking all devices...")
        self.unblock_all()
        print("✅ All devices unlocked via pattern")
        
        # Clear any stuck keys after unlock
        self._clear_stuck_keys()
        
        # Queue event for WebSocket emission
        self._pending_events.append({
            'type': 'pattern_unlock',
            'action': 'unlocked',
            'devices': self.get_devices(),
            'status': self.get_system_status()
        })
    
    def _clear_stuck_keys(self):
        """Clear any stuck modifier keys after unlock using xdotool"""
        import subprocess
        try:
            # Release common modifier keys that might be stuck
            for key in ['ctrl', 'alt', 'shift', 'super']:
                subprocess.run(['xdotool', 'keyup', key], 
                             capture_output=True, timeout=1)
            print("🧹 Cleared stuck modifier keys")
        except FileNotFoundError:
            # xdotool not installed - try with python-xlib
            try:
                from Xlib import X, display
                from Xlib.ext import xtest
                d = display.Display()
                # Send key release events for modifiers
                for keycode in [37, 64, 50, 133]:  # ctrl, alt, shift, super
                    xtest.fake_input(d, X.KeyRelease, keycode)
                d.sync()
                d.close()
                print("🧹 Cleared stuck modifier keys via Xlib")
            except:
                pass
        except Exception as e:
            print(f"Could not clear stuck keys: {e}")
    
    def get_pending_events(self) -> List[Dict]:
        """Get and clear pending events for WebSocket emission"""
        events = self._pending_events.copy()
        self._pending_events.clear()
        return events
        
    def get_devices(self) -> List[Dict]:
        """Get list of all input devices with their status"""
        devices = self.device_manager.get_all_devices()
        result = []
        
        for device in devices:
            device_dict = {
                'id': device.path,
                'path': device.path,
                'name': device.name,
                'type': device.device_type.value if hasattr(device.device_type, 'value') else str(device.device_type),
                'blocked': self.blocked_devices.get(device.path, False),
                'physicalPath': getattr(device, 'physical_path', ''),
                'capabilities': list(device.capabilities) if hasattr(device, 'capabilities') else [],
            }
            result.append(device_dict)
            
        return result
    
    def block_device(self, device_path: str) -> bool:
        """Block a specific device by grabbing it"""
        try:
            if device_path in self.blocked_devices and self.blocked_devices[device_path]:
                return True  # Already blocked
            
            device = evdev.InputDevice(device_path)
            device.grab()
            
            self.grabbed_devices[device_path] = device
            self.blocked_devices[device_path] = True
            self.block_start_times[device_path] = time.time()
            self.stats['blocked_events'] += 1
            
            # Check if this is a keyboard (has KEY_A capability)
            is_keyboard = False
            try:
                caps = device.capabilities(verbose=False)
                if evdev.ecodes.EV_KEY in caps:
                    keys = caps[evdev.ecodes.EV_KEY]
                    is_keyboard = evdev.ecodes.KEY_A in keys or evdev.ecodes.KEY_ENTER in keys
            except:
                pass
            
            # Start event reader thread for pattern detection (only for keyboards)
            if is_keyboard:
                self._start_event_reader(device_path, device, is_keyboard=True)
            
            # Add to history
            self.stats['block_history'].append({
                'timestamp': datetime.now().isoformat(),
                'device': device_path,
                'action': 'blocked'
            })
            
            return True
        except Exception as e:
            print(f"Error blocking device {device_path}: {e}")
            return False
    
    def _start_event_reader(self, device_path: str, device, is_keyboard: bool = False):
        """Start a thread to read events from blocked device for pattern detection"""
        def reader_thread():
            if is_keyboard:
                print(f"⌨️  Keyboard event reader started for {device_path}")
            try:
                for event in device.read_loop():
                    # Check if device was unblocked
                    if not self.blocked_devices.get(device_path, False):
                        break
                    
                    # Only process key events from keyboards for pattern detection
                    if is_keyboard and event.type == evdev.ecodes.EV_KEY:
                        # Pass to pattern unlocker
                        if self.pattern_unlocker and self.pattern_unlocker.handle_key(event.code, event.value):
                            # Pattern matched - unlock will be triggered by callback
                            print("🎮 Pattern detected!")
            except Exception as e:
                # Device was closed or error occurred
                pass
        
        thread = threading.Thread(target=reader_thread, daemon=True)
        thread.start()
    
    def unblock_device(self, device_path: str) -> bool:
        """Unblock a specific device by releasing the grab"""
        try:
            if device_path not in self.blocked_devices or not self.blocked_devices[device_path]:
                return True  # Already unblocked
            
            if device_path in self.grabbed_devices:
                try:
                    device = self.grabbed_devices[device_path]
                    
                    # Drain any pending events before ungrabbing to prevent key repeat issues
                    try:
                        while True:
                            # Non-blocking read to clear buffer
                            events = list(device.read())
                            if not events:
                                break
                    except BlockingIOError:
                        pass
                    except Exception:
                        pass
                    
                    # Send key up events for any potentially stuck keys
                    try:
                        from evdev import UInput, ecodes
                        # Common modifier keys that might be stuck
                        stuck_keys = [
                            ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL,
                            ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT,
                            ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT,
                            ecodes.KEY_L, ecodes.KEY_1
                        ]
                        # We don't inject - just ensure the device releases properly
                    except:
                        pass
                    
                    device.ungrab()
                    device.close()
                except Exception as e:
                    print(f"Error releasing device {device_path}: {e}")
                    pass
                del self.grabbed_devices[device_path]
            
            self.blocked_devices[device_path] = False
            
            # Calculate blocked time
            if device_path in self.block_start_times:
                blocked_time = time.time() - self.block_start_times[device_path]
                self.stats['total_blocked_time'] += blocked_time
                del self.block_start_times[device_path]
            
            # Add to history
            self.stats['block_history'].append({
                'timestamp': datetime.now().isoformat(),
                'device': device_path,
                'action': 'unblocked'
            })
            
            return True
        except Exception as e:
            print(f"Error unblocking device {device_path}: {e}")
            return False
    
    def toggle_device(self, device_path: str) -> bool:
        """Toggle block state of a device"""
        if self.blocked_devices.get(device_path, False):
            return self.unblock_device(device_path)
        else:
            return self.block_device(device_path)
    
    def block_all(self) -> bool:
        """Block only keyboard and mouse devices"""
        devices = self.device_manager.get_all_devices()
        success = True
        blocked_count = 0
        for device in devices:
            # Only block keyboards and mice
            if device.device_type in [DeviceType.KEYBOARD, DeviceType.MOUSE]:
                if self.block_device(device.path):
                    blocked_count += 1
                else:
                    success = False
        print(f"📊 Blocked {blocked_count} devices (keyboards and mice only)")
        return success
    
    def unblock_all(self) -> bool:
        """Unblock all devices"""
        paths = list(self.blocked_devices.keys())
        success = True
        for path in paths:
            if not self.unblock_device(path):
                success = False
        return success
    
    def set_timer(self, minutes: int) -> Dict:
        """Set a timer to unblock after specified minutes"""
        self.timer_total_seconds = minutes * 60
        self.timer_end_time = time.time() + self.timer_total_seconds
        self.timer_active = True
        
        # Block all devices
        self.block_all()
        
        # Start timer thread
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_active = False
            self.timer_thread.join(timeout=1)
        
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
        
        return self.get_timer_status()
    
    def _timer_loop(self):
        """Timer loop that runs in background"""
        while self.timer_active and self.timer_end_time:
            if time.time() >= self.timer_end_time:
                self.unblock_all()
                self.timer_active = False
                self.timer_end_time = None
                break
            time.sleep(1)
    
    def cancel_timer(self) -> bool:
        """Cancel the current timer"""
        self.timer_active = False
        self.timer_end_time = None
        return True
    
    def get_timer_status(self) -> Dict:
        """Get current timer status"""
        if not self.timer_active or not self.timer_end_time:
            return {
                'active': False,
                'remainingSeconds': 0,
                'totalSeconds': 0
            }
        
        remaining = max(0, int(self.timer_end_time - time.time()))
        return {
            'active': True,
            'remainingSeconds': remaining,
            'totalSeconds': self.timer_total_seconds
        }
    
    def get_statistics(self) -> Dict:
        """Get blocking statistics"""
        # Calculate current blocked time for active blocks
        current_blocked_time = self.stats['total_blocked_time']
        for path, start_time in self.block_start_times.items():
            current_blocked_time += time.time() - start_time
        
        # Get device-specific stats
        device_stats = []
        for device in self.device_manager.get_all_devices():
            device_stats.append({
                'deviceId': device.path,
                'deviceName': device.name,
                'blockedTime': 0,  # Would need persistent storage
                'blockedEvents': 0,
            })
        
        return {
            'totalBlockedTime': int(current_blocked_time),
            'blockedEvents': self.stats['blocked_events'],
            'blockHistory': self.stats['block_history'][-50:],  # Last 50 events
            'deviceStats': device_stats,
        }
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        devices = self.device_manager.get_all_devices()
        active_blocks = sum(1 for v in self.blocked_devices.values() if v)
        
        return {
            'running': True,
            'activeBlocks': active_blocks,
            'connectedDevices': len(devices),
            'uptime': int(time.time() - self.start_time),
        }
    
    def get_settings(self) -> Dict:
        """Get current settings from config manager"""
        return {
            'hotkey': self.config_manager.get('hotkey', ['Ctrl', 'Alt', 'L']),
            'emergencyPattern': self.config_manager.get('pattern_sequence', ['Up', 'Up', 'Down', 'Down', 'Enter']),
            'autoBlockOnStart': self.config_manager.get('auto_block_on_start', False),
            'showNotifications': self.config_manager.get('show_notifications', True),
            'allowTouchscreenUnlock': self.config_manager.get('allow_touchscreen_unlock', True),
            'theme': self.config_manager.get('theme', 'dark'),
        }
    
    def update_settings(self, settings: Dict) -> Dict:
        """Update settings in config manager"""
        mapping = {
            'hotkey': 'hotkey',
            'emergencyPattern': 'pattern_sequence',
            'autoBlockOnStart': 'auto_block_on_start',
            'showNotifications': 'show_notifications',
            'allowTouchscreenUnlock': 'allow_touchscreen_unlock',
            'theme': 'theme',
        }
        
        for key, value in settings.items():
            if key in mapping and value is not None:
                self.config_manager.set(mapping[key], value)
        
        self.config_manager.save()
        return self.get_settings()


# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI Application
# ═══════════════════════════════════════════════════════════════════════════════

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Create FastAPI app
app = FastAPI(
    title="Input Locker API",
    description="REST API for Input Locker device blocking system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create device manager instance
manager = DeviceBlockerManager()


# ═══════════════════════════════════════════════════════════════════════════════
# API Routes
# ═══════════════════════════════════════════════════════════════════════════════

def api_response(success: bool, data: Any = None, message: str = ""):
    """Standard API response format"""
    return {"success": success, "data": data, "message": message}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "input-locker-api"}


@app.get("/api/health")
async def api_health_check():
    """API Health check endpoint"""
    return api_response(True, {"status": "ok"})


# Device endpoints
@app.get("/api/devices/list")
async def get_devices():
    """Get list of all input devices"""
    try:
        devices = manager.get_devices()
        return api_response(True, devices)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/devices/status/{device_path:path}")
async def get_device_status(device_path: str):
    """Get status of a specific device"""
    devices = manager.get_devices()
    device = next((d for d in devices if d['path'] == f"/dev/input/{device_path}"), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return api_response(True, device)


@app.post("/api/device/block")
async def block_device(request: DeviceBlockRequest):
    """Block a specific device"""
    success = manager.block_device(request.device_path)
    if success:
        await sio.emit('device_update', {'path': request.device_path, 'blocked': True})
    return api_response(success)


@app.post("/api/device/unblock")
async def unblock_device(request: DeviceBlockRequest):
    """Unblock a specific device"""
    success = manager.unblock_device(request.device_path)
    if success:
        await sio.emit('device_update', {'path': request.device_path, 'blocked': False})
    return api_response(success)


@app.post("/api/device/toggle")
async def toggle_device(request: DeviceBlockRequest):
    """Toggle block state of a device"""
    is_blocked = manager.blocked_devices.get(request.device_path, False)
    success = manager.toggle_device(request.device_path)
    if success:
        await sio.emit('device_update', {'path': request.device_path, 'blocked': not is_blocked})
    return api_response(success)


@app.post("/api/devices/block-all")
async def block_all_devices():
    """Block all devices"""
    success = manager.block_all()
    await sio.emit('status_update', manager.get_system_status())
    return api_response(success)


@app.post("/api/devices/unblock-all")
async def unblock_all_devices():
    """Unblock all devices"""
    success = manager.unblock_all()
    await sio.emit('status_update', manager.get_system_status())
    return api_response(success)


# Timer endpoints
@app.post("/api/timer/set")
async def set_timer(request: TimerRequest):
    """Set a block timer"""
    timer = manager.set_timer(request.minutes)
    await sio.emit('timer_update', timer)
    return api_response(True, timer)


@app.post("/api/timer/cancel")
async def cancel_timer():
    """Cancel the current timer"""
    success = manager.cancel_timer()
    await sio.emit('timer_update', manager.get_timer_status())
    return api_response(success)


@app.get("/api/timer/status")
async def get_timer_status():
    """Get current timer status"""
    return api_response(True, manager.get_timer_status())


# Statistics endpoints
@app.get("/api/stats")
async def get_statistics():
    """Get blocking statistics"""
    return api_response(True, manager.get_statistics())


@app.post("/api/stats/clear")
async def clear_statistics():
    """Clear blocking statistics"""
    manager.stats = {
        'total_blocked_time': 0,
        'blocked_events': 0,
        'block_history': [],
        'device_stats': {},
    }
    return api_response(True)


# System status
@app.get("/api/system/status")
async def get_system_status():
    """Get overall system status"""
    return api_response(True, manager.get_system_status())


# Settings endpoints
@app.get("/api/settings")
async def get_settings():
    """Get current settings"""
    return api_response(True, manager.get_settings())


@app.put("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """Update settings"""
    updated = manager.update_settings(settings.dict(exclude_none=True))
    return api_response(True, updated)


# Whitelist endpoints (simplified - store in memory for now)
whitelist: List[Dict] = []
whitelist_counter = 0


@app.get("/api/whitelist")
async def get_whitelist():
    """Get whitelist entries"""
    return api_response(True, whitelist)


@app.post("/api/whitelist")
async def add_to_whitelist(entry: WhitelistEntry):
    """Add entry to whitelist"""
    global whitelist_counter
    whitelist_counter += 1
    new_entry = {
        'id': str(whitelist_counter),
        'devicePath': entry.devicePath,
        'deviceName': entry.deviceName,
        'enabled': entry.enabled,
    }
    whitelist.append(new_entry)
    return api_response(True, new_entry)


@app.delete("/api/whitelist/{entry_id}")
async def remove_from_whitelist(entry_id: str):
    """Remove entry from whitelist"""
    global whitelist
    whitelist = [e for e in whitelist if e['id'] != entry_id]
    return api_response(True)


@app.post("/api/whitelist/{entry_id}/toggle")
async def toggle_whitelist_entry(entry_id: str):
    """Toggle whitelist entry"""
    for entry in whitelist:
        if entry['id'] == entry_id:
            entry['enabled'] = not entry['enabled']
            return api_response(True, entry)
    raise HTTPException(status_code=404, detail="Entry not found")


# ═══════════════════════════════════════════════════════════════════════════════
# Socket.IO Events
# ═══════════════════════════════════════════════════════════════════════════════

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('status_update', manager.get_system_status(), room=sid)
    await sio.emit('devices_update', manager.get_devices(), room=sid)


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


# Background task to emit pending events from hotkey/pattern actions
async def emit_pending_events():
    """Background task that checks for pending events and emits them"""
    import asyncio
    while True:
        try:
            events = manager.get_pending_events()
            for event in events:
                print(f"📡 Emitting event: {event['type']} - {event['action']}")
                # Emit to all connected clients
                await sio.emit('hotkey_action', {
                    'type': event['type'],
                    'action': event['action']
                })
                await sio.emit('devices_update', event['devices'])
                await sio.emit('status_update', event['status'])
        except Exception as e:
            print(f"Error emitting events: {e}")
        await asyncio.sleep(0.1)  # Check every 100ms


# Background task to emit timer and stats updates
async def emit_periodic_updates():
    """Background task that emits timer and stats every second"""
    import asyncio
    last_timer_state = None
    
    while True:
        try:
            # Get timer status
            timer_status = manager.get_timer_status()
            
            # Only emit if timer is active or state changed
            if timer_status['active'] or last_timer_state != timer_status:
                await sio.emit('timer_update', timer_status)
                last_timer_state = timer_status.copy()
            
            # Emit stats update every second
            await sio.emit('stats_update', manager.get_statistics())
            
            # Emit system status
            await sio.emit('status_update', manager.get_system_status())
            
        except Exception as e:
            pass  # Silently ignore errors in periodic updates
        
        await asyncio.sleep(1)  # Update every second


@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    import asyncio
    asyncio.create_task(emit_pending_events())
    asyncio.create_task(emit_periodic_updates())


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown - stop hotkey handler and unblock devices"""
    print("🛑 Shutting down Input Locker API...")
    try:
        # Stop hotkey handler first
        if locker.hotkey_handler:
            locker.hotkey_handler.stop()
        
        # Unblock all devices
        locker.unblock_all()
        
        # Clear any stuck keys
        locker._clear_stuck_keys()
        
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"Cleanup error: {e}")


# Wrap FastAPI with Socket.IO
socket_app = socketio.ASGIApp(sio, app)


# ═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def cleanup_and_exit(signum=None, frame=None):
    """Emergency cleanup on signal"""
    print("\n🛑 Signal received, cleaning up...")
    try:
        if locker.hotkey_handler:
            locker.hotkey_handler.stop()
        locker.unblock_all()
        locker._clear_stuck_keys()
    except:
        pass
    print("✅ Cleanup done, exiting...")
    import os
    os._exit(0)

def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the API server"""
    import signal
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║               Input Locker API Server                            ║
╠══════════════════════════════════════════════════════════════════╣
║  REST API:    http://{host}:{port}/api                              ║
║  WebSocket:   ws://{host}:{port}/socket.io                          ║
║  API Docs:    http://{host}:{port}/docs                             ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(socket_app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Input Locker API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    run_server(args.host, args.port)
