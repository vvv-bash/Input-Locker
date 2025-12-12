from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


@dataclass
class LockEvent:
    timestamp: datetime
    action: str  # "lock" or "unlock"


class MockDataGenerator:
    """Generates synthetic analytics data when real history is unavailable."""

    @classmethod
    def generate_timeline_events(cls, hours: int = 24) -> List[LockEvent]:
        now = datetime.now()
        events: List[LockEvent] = []
        for h in range(hours):
            base_time = now - timedelta(hours=h)
            for i in range(2):
                ts = base_time - timedelta(minutes=i * 10)
                action = "lock" if i % 2 == 0 else "unlock"
                events.append(LockEvent(timestamp=ts, action=action))
        events.sort(key=lambda e: e.timestamp)
        return events

    @classmethod
    def generate_weekly_activity(cls) -> List[int]:
        base = 12
        return [max(0, base + i - 3) for i in range(7)]

    @classmethod
    def generate_device_distribution(cls) -> Dict[str, int]:
        return {
            "keyboard": 3,
            "mouse": 1,
            "touchscreen": 1,
            "touchpad": 0,
            "unknown": 2,
        }


class DashboardDataManager(QObject):
    """Aggregates real-time state + real analytics for the dashboard."""

    data_updated = pyqtSignal(dict)

    def __init__(self, device_manager, input_blocker, config_manager, parent=None):
        super().__init__(parent)
        self.device_manager = device_manager
        self.input_blocker = input_blocker
        self.config_manager = config_manager

        self._session_start = datetime.now()
        self._last_action = "App started"

        # Real event history
        self._lock_events: List[LockEvent] = []
        # Weekly activity: count of lock events per day of the week (Mon=0, Sun=6)
        self._weekly_counts: List[int] = [0, 0, 0, 0, 0, 0, 0]

        # Connect to input_blocker signals if available
        if hasattr(input_blocker, 'lock_changed'):
            input_blocker.lock_changed.connect(self._on_lock_changed)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._emit_data)
        self._timer.start(5000)

    def _on_lock_changed(self, locked: bool) -> None:
        """Record real lock/unlock events."""
        now = datetime.now()
        action = "lock" if locked else "unlock"
        self._lock_events.append(LockEvent(timestamp=now, action=action))
        self._last_action = f"Devices {'locked' if locked else 'unlocked'}"

        # Update weekly count (only for lock events)
        if locked:
            day_of_week = now.weekday()  # 0=Monday, 6=Sunday
            self._weekly_counts[day_of_week] += 1

        # Emit immediately on lock change
        self._emit_data()

    def record_action(self, description: str) -> None:
        self._last_action = description

    def _build_system_status(self) -> Dict:
        elapsed = datetime.now() - self._session_start
        locked = bool(getattr(self.input_blocker, "is_locked", False))

        devices_total = len(getattr(self.device_manager, "devices", {}))
        locked_devices = len(getattr(self.input_blocker, "locked_devices", set()))

        return {
            "locked": locked,
            "session_time": int(elapsed.total_seconds()),
            "devices_managed": devices_total,
            "locked_devices": locked_devices,
            "last_action": self._last_action,
        }

    def _build_distribution_from_manager(self) -> Dict[str, int]:
        # Local import to avoid circulars; note triple-dot from dashboard -> gui -> src
        from ...core.device_manager import DeviceType

        dist: Dict[str, int] = {
            "keyboard": 0,
            "mouse": 0,
            "touchscreen": 0,
            "touchpad": 0,
            "unknown": 0,
        }

        for info in getattr(self.device_manager, "devices", {}).values():
            if info.device_type == DeviceType.KEYBOARD:
                dist["keyboard"] += 1
            elif info.device_type == DeviceType.MOUSE:
                dist["mouse"] += 1
            elif info.device_type == DeviceType.TOUCHSCREEN:
                dist["touchscreen"] += 1
            elif info.device_type == DeviceType.TOUCHPAD:
                dist["touchpad"] += 1
            else:
                dist["unknown"] += 1
        return dist

    def _emit_data(self) -> None:
        system_status = self._build_system_status()

        # Use real lock events (filter to last 24h)
        now = datetime.now()
        recent_events = [
            e for e in self._lock_events
            if (now - e.timestamp).total_seconds() <= 24 * 3600
        ]

        # Use real weekly activity counts
        weekly_activity = self._weekly_counts[:]

        if getattr(self.device_manager, "devices", None):
            device_distribution = self._build_distribution_from_manager()
        else:
            device_distribution = MockDataGenerator.generate_device_distribution()

        hotkey = self.config_manager.get_hotkey()

        data = {
            "system_status": system_status,
            "timeline_events": recent_events,
            "weekly_activity": weekly_activity,
            "device_distribution": device_distribution,
            "hotkey": hotkey,
        }

        self.data_updated.emit(data)
