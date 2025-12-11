from __future__ import annotations

from typing import Dict, List

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel

from .dashboard_data import DashboardDataManager
from .dashboard_widgets import (
    SystemStatusCard,
    LockTimelineCard,
    DeviceDistributionCard,
    WeeklyActivityChart,
    ActiveDevicesMetric,
    QuickActionsPanel,
    HotkeyStatusCard,
)
from ..glassmorphic_widgets import GradientBackground


class DashboardWindow(QMainWindow):
    """Standalone dashboard window with glassmorphic layout."""

    def __init__(self, device_manager, input_blocker, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Input Locker – Dashboard")
        self.setMinimumSize(1024, 640)

        self.device_manager = device_manager
        self.input_blocker = input_blocker
        self.config_manager = config_manager

        self.data_manager = DashboardDataManager(device_manager, input_blocker, config_manager, self)
        self.data_manager.data_updated.connect(self._on_data_updated)

        self._init_ui()

    def _init_ui(self) -> None:
        central = GradientBackground(self)
        central.setObjectName("DashboardBackground")
        self.setCentralWidget(central)

        # Root layout: header bar + grid of cards
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # Simple header row to give structure
        header_row = QHBoxLayout()
        title = QLabel("Dashboard overview")
        title.setObjectName("DashboardTitle")
        subtitle = QLabel("Real‑time lock status, devices and activity")
        subtitle.setObjectName("DashboardSubtitle")
        header_text = QVBoxLayout()
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()
        root.addLayout(header_row)

        container = QWidget()
        container.setObjectName("DashboardContainer")
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        root.addWidget(container)

        # Top row: large status card on the left, donut on the right
        self.card_status = SystemStatusCard(container)
        self.card_timeline = LockTimelineCard(container)
        self.card_distribution = DeviceDistributionCard(container)

        grid.addWidget(self.card_status, 0, 0, 1, 2)        # hero card spanning two columns
        grid.addWidget(self.card_distribution, 0, 2, 2, 1)  # tall donut card on the right

        # Middle row: timeline + weekly activity
        self.card_weekly = WeeklyActivityChart(container)
        self.card_active_devices = ActiveDevicesMetric(container)

        grid.addWidget(self.card_timeline, 1, 0, 1, 1)
        grid.addWidget(self.card_weekly, 1, 1, 1, 1)

        # Third row: locked devices metric wide across left + center
        grid.addWidget(self.card_active_devices, 2, 0, 1, 2)

        # Bottom row: quick actions and hotkey profile as call‑to‑action strip
        self.card_actions = QuickActionsPanel(container)
        self.card_hotkeys = HotkeyStatusCard(container)

        grid.addWidget(self.card_actions, 3, 0, 1, 1)
        grid.addWidget(self.card_hotkeys, 3, 1, 1, 2)

        # Column weights: slightly emphasize center and right
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        grid.setRowStretch(0, 3)
        grid.setRowStretch(1, 3)
        grid.setRowStretch(2, 2)
        grid.setRowStretch(3, 1)

        self.card_actions.lock_all_requested.connect(self._lock_all)
        self.card_actions.unlock_all_requested.connect(self._unlock_all)

        self.card_hotkeys.configure_requested.connect(self._open_settings)

    def _on_data_updated(self, payload: Dict) -> None:
        system_status = payload.get("system_status", {})
        self.card_status.update_from_data(system_status)

        events = payload.get("timeline_events", [])
        self.card_timeline.update_from_events(events)

        distribution = payload.get("device_distribution", {})
        self.card_distribution.update_from_distribution(distribution)

        weekly: List[int] = payload.get("weekly_activity", [])
        self.card_weekly.set_values(weekly)

        locked_total = int(system_status.get("locked_devices", 0))
        locked_names: List[str] = []
        for dev_id in getattr(self.input_blocker, "locked_devices", set()):
            device_info = getattr(self.input_blocker, "devices", {}).get(dev_id, {})
            name = device_info.get("name", dev_id)
            locked_names.append(name)

        self.card_active_devices.update_from_data(locked_total, locked_names)

        hotkey = payload.get("hotkey", "-")
        self.card_hotkeys.update_hotkey(hotkey)

    def _lock_all(self) -> None:
        try:
            self.data_manager.record_action("Locked all devices")
            self.input_blocker.lock_all()
        except Exception:
            pass

    def _unlock_all(self) -> None:
        try:
            self.data_manager.record_action("Unlocked all devices")
            self.input_blocker.unlock_all()
        except Exception:
            pass

    def _open_settings(self) -> None:
        parent = self.parent()
        if parent is not None and hasattr(parent, "_show_settings"):
            try:
                parent._show_settings()
            except Exception:
                pass
