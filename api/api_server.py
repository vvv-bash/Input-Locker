"""Input Locker API Server - Ctrl+Alt+L to lock, ↑↑↓↓Enter to unlock."""
import os, sys, signal, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import socketio, uvicorn

from api._internal import get_manager, DeviceBlockRequest, LockTypesRequest, TimerRequest, SettingsUpdate, WhitelistEntry

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI(title="Input Locker API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

mgr = get_manager()
whitelist, wl_counter = [], 0

_r = lambda ok, data=None, msg="": {"success": ok, "data": data, "message": msg}

app.get("/health")(lambda: {"status": "ok"})
app.get("/api/health")(lambda: _r(True, {"status": "ok"}))

@app.post("/api/shutdown")
async def _shutdown():
    import asyncio, threading
    mgr.cleanup()
    # Force exit in a separate thread to ensure it happens
    threading.Thread(target=lambda: (time.sleep(0.1), os._exit(0)), daemon=True).start()
    return _r(True, None, "Shutting down...")

app.get("/api/devices/list")(lambda: _r(True, mgr.get_devices()))

@app.get("/api/devices/status/{device_path:path}")
async def _dev_status(device_path: str):
    d = next((x for x in mgr.get_devices() if x['path'] == f"/dev/input/{device_path}"), None)
    if not d: raise HTTPException(404, "Not found")
    return _r(True, d)

@app.post("/api/device/block")
async def _dev_block(r: DeviceBlockRequest):
    mgr.block_all()
    await sio.emit('device_update', {'path': r.device_path, 'blocked': True})
    return _r(True)

@app.post("/api/device/unblock")
async def _dev_unblock(r: DeviceBlockRequest):
    mgr.unblock_all()
    await sio.emit('device_update', {'path': r.device_path, 'blocked': False})
    return _r(True)

@app.post("/api/device/toggle")
async def _dev_toggle(r: DeviceBlockRequest):
    was = r.device_path in mgr.blocker.grabbed
    mgr.toggle()
    await sio.emit('device_update', {'path': r.device_path, 'blocked': not was})
    return _r(True)

@app.post("/api/devices/block-all")
async def _block_all():
    mgr.block_all()
    await sio.emit('status_update', mgr.system_status())
    return _r(True)

@app.post("/api/devices/unblock-all")
async def _unblock_all():
    mgr.unblock_all()
    await sio.emit('status_update', mgr.system_status())
    return _r(True)

@app.post("/api/devices/lock-by-types")
async def _lock_by_types(r: LockTypesRequest):
    """Lock only devices of specific types (keyboard, mouse, touchpad, touchscreen)."""
    mgr.lock_by_types(r.types)
    await sio.emit('status_update', mgr.system_status())
    return _r(True, {"types": r.types})

@app.post("/api/timer/set")
async def _timer_set(r: TimerRequest):
    t = mgr.set_timer(r.minutes)
    await sio.emit('timer_update', t)
    return _r(True, t)

@app.post("/api/timer/cancel")
async def _timer_cancel():
    mgr.cancel_timer()
    await sio.emit('timer_update', mgr.timer_status())
    return _r(True)

app.get("/api/timer/status")(lambda: _r(True, mgr.timer_status()))
app.get("/api/stats")(lambda: _r(True, mgr.statistics()))

@app.post("/api/stats/clear")
async def _stats_clear():
    mgr.stats = {'total_blocked_time': 0, 'blocked_events': 0, 'block_history': []}
    return _r(True)

app.get("/api/system/status")(lambda: _r(True, mgr.system_status()))
app.get("/api/settings")(lambda: _r(True, mgr.get_settings()))

@app.put("/api/settings")
async def _put_settings(s: SettingsUpdate): return _r(True, mgr.update_settings(s.dict(exclude_none=True)))

app.get("/api/whitelist")(lambda: _r(True, whitelist))

@app.post("/api/whitelist")
async def _wl_add(e: WhitelistEntry):
    global wl_counter
    wl_counter += 1
    entry = {'id': str(wl_counter), 'devicePath': e.devicePath, 'deviceName': e.deviceName, 'enabled': e.enabled}
    whitelist.append(entry)
    return _r(True, entry)

@app.delete("/api/whitelist/{eid}")
async def _wl_del(eid: str):
    global whitelist
    whitelist = [x for x in whitelist if x['id'] != eid]
    return _r(True)

@app.post("/api/whitelist/{eid}/toggle")
async def _wl_toggle(eid: str):
    for e in whitelist:
        if e['id'] == eid:
            e['enabled'] = not e['enabled']
            return _r(True, e)
    raise HTTPException(404, "Not found")

@sio.event
async def connect(sid, env):
    await sio.emit('status_update', mgr.system_status(), room=sid)
    await sio.emit('devices_update', mgr.get_devices(), room=sid)

@sio.event
async def disconnect(sid): pass

async def _bg_events():
    import asyncio
    while True:
        for ev in mgr.get_pending():
            await sio.emit('hotkey_action', {'type': ev['type'], 'action': ev['action']})
            await sio.emit('devices_update', mgr.get_devices())
            await sio.emit('status_update', mgr.system_status())
            # Also push updated statistics so the web UI stays in sync
            await sio.emit('stats_update', mgr.statistics())
        await asyncio.sleep(0.1)

async def _bg_updates():
    import asyncio
    last_lock = None
    while True:
        t = mgr.timer_status()
        if t['active']: await sio.emit('timer_update', t)
        curr = mgr.blocker.is_locked
        if last_lock is not None and last_lock != curr:
            await sio.emit('devices_update', mgr.get_devices())
            await sio.emit('hotkey_action', {'type': 'timer', 'action': 'locked' if curr else 'unlocked'})
        last_lock = curr
        await asyncio.sleep(1)

@app.on_event("startup")
async def _startup():
    import asyncio
    asyncio.create_task(_bg_events())
    asyncio.create_task(_bg_updates())

@app.on_event("shutdown")
async def _shutdown_ev(): mgr.cleanup()

socket_app = socketio.ASGIApp(sio, app)

def run(host="0.0.0.0", port=8080):
    signal.signal(signal.SIGINT, lambda *_: os._exit(0))
    signal.signal(signal.SIGTERM, lambda *_: os._exit(0))
    print(f"\n🔐 Input Locker API @ http://{host}:{port}\n   Ctrl+Alt+L=Lock | ↑↑↓↓Enter=Unlock\n")
    uvicorn.run(socket_app, host=host, port=port)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080)
    a = p.parse_args()
    run(a.host, a.port)
