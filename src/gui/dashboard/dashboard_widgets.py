from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from .dashboard_data import LockEvent
from ..glassmorphic_widgets import FrostedCard, DangerButton, SuccessButton, OutlineButton


class SystemStatusCard(FrostedCard):
    def __init__(self, parent=None):
        super().__init__(parent, variant="status")
        self.setObjectName("SystemStatusCard")

        layout = self.layout()

        header = QHBoxLayout()
        self.title_label = QLabel("System Status")
        self.title_label.setObjectName("DashboardTitle")
        header.addWidget(self.title_label)

        header.addStretch()

        self.status_pill = QLabel("ACTIVE")
        self.status_pill.setObjectName("StatusPill")
        header.addWidget(self.status_pill)

        layout.addLayout(header)

        self.subtitle = QLabel("Input monitoring is running")
        self.subtitle.setObjectName("DashboardSubtitle")
        layout.addWidget(self.subtitle)

        metrics = QHBoxLayout()
        self.session_label = QLabel("Session: 0m")
        self.devices_label = QLabel("Devices: 0")
        self.locked_label = QLabel("Locked: 0")

        for lbl in (self.session_label, self.devices_label, self.locked_label):
            lbl.setObjectName("MetricLabel")
            metrics.addWidget(lbl)

        metrics.addStretch()
        layout.addLayout(metrics)

        self.last_action_label = QLabel("Last action: App started")
        self.last_action_label.setObjectName("LastActionLabel")
        layout.addWidget(self.last_action_label)

    def update_from_data(self, data: Dict) -> None:
        locked = bool(data.get("locked", False))
        session_seconds = int(data.get("session_time", 0))
        devices = int(data.get("devices_managed", 0))
        locked_devices = int(data.get("locked_devices", 0))
        last_action = data.get("last_action", "-")

        self.status_pill.setText("LOCKED" if locked else "ACTIVE")
        self.status_pill.setProperty("state", "locked" if locked else "active")
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

        minutes, seconds = divmod(session_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            session_text = f"Session: {hours}h {minutes}m"
        elif minutes:
            session_text = f"Session: {minutes}m {seconds}s"
        else:
            session_text = f"Session: {seconds}s"

        self.session_label.setText(session_text)
        self.devices_label.setText(f"Devices: {devices}")
        self.locked_label.setText(f"Locked: {locked_devices}")
        self.last_action_label.setText(f"Last action: {last_action}")


class _TimelineChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._series: List[int] = []
        self.setMinimumHeight(120)

    def set_series(self, series: List[int]) -> None:
        self._series = list(series)
        self.update()

    def paintEvent(self, event):  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(12, 8, -12, -16)
        painter.setPen(Qt.PenStyle.NoPen)

        if not self._series:
            return

        max_val = max(self._series) or 1
        count = len(self._series)
        if count <= 1:
            return

        step = rect.width() / float(count - 1)

        path: List[Tuple[float, float]] = []
        for i, value in enumerate(self._series):
            x = rect.left() + i * step
            y = rect.bottom() - (value / max_val) * rect.height()
            path.append((x, y))

        color = QColor(99, 102, 241, 60)
        painter.setBrush(color)

        polygon: List[Tuple[float, float]] = []
        for x, y in path:
            polygon.append((x, y))
        polygon.append((rect.right(), rect.bottom()))
        polygon.append((rect.left(), rect.bottom()))

        points = [QRectF(x, y, 0.1, 0.1).topLeft() for x, y in polygon]
        painter.drawPolygon(*points)

        pen = QPen(QColor(129, 140, 248), 2.5)
        painter.setPen(pen)
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))


class LockTimelineCard(FrostedCard):
    def __init__(self, parent=None):
        super().__init__(parent, variant="timeline")
        self.setObjectName("LockTimelineCard")

        layout = self.layout()

        header = QHBoxLayout()
        title = QLabel("Lock / Unlock timeline (24h)")
        title.setObjectName("DashboardTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.chart = _TimelineChart(self)
        layout.addWidget(self.chart)

        self.summary_label = QLabel("0 events in last 24h")
        self.summary_label.setObjectName("DashboardCaption")
        layout.addWidget(self.summary_label)

    def update_from_events(self, events: List[LockEvent]) -> None:
        if not events:
            self.chart.set_series([])
            self.summary_label.setText("No events in last 24h")
            return

        buckets: Dict[int, int] = defaultdict(int)
        now = datetime.now()
        for ev in events:
            delta = now - ev.timestamp
            if 0 <= delta.total_seconds() <= 24 * 3600:
                hour = 24 - int(delta.total_seconds() // 3600)
                buckets[hour] += 1

        series = [buckets.get(i, 0) for i in range(1, 25)]
        step = max(1, len(series) // 12)
        reduced = [sum(series[i : i + step]) for i in range(0, len(series), step)]

        self.chart.set_series(reduced)
        self.summary_label.setText(f"{sum(series)} events in last 24h")


class _DonutChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments: List[Tuple[float, QColor]] = []
        self.setMinimumHeight(120)

    def set_segments(self, segments: List[Tuple[float, QColor]]) -> None:
        self._segments = segments
        self.update()

    def paintEvent(self, event):  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(16, 8, -16, -8)
        size = min(rect.width(), rect.height())
        radius = size
        center_x = rect.center().x() - radius / 2
        center_y = rect.center().y() - radius / 2
        draw_rect = QRectF(center_x, center_y, radius, radius)

        start_angle = 90 * 16

        for value, color in self._segments:
            span = -value * 360 * 16
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(draw_rect, int(start_angle), int(span))
            start_angle += span

        inner_rect = draw_rect.adjusted(radius * 0.28, radius * 0.28, -radius * 0.28, -radius * 0.28)
        painter.setBrush(QColor(10, 15, 30))
        painter.drawEllipse(inner_rect)


class DeviceDistributionCard(FrostedCard):
    COLORS: Dict[str, QColor] = {
        "keyboard": QColor(99, 102, 241),
        "mouse": QColor(139, 92, 246),
        "touchscreen": QColor(34, 211, 238),
        "touchpad": QColor(251, 146, 60),
        "unknown": QColor(100, 116, 139),
    }

    def __init__(self, parent=None):
        super().__init__(parent, variant="distribution")
        self.setObjectName("DeviceDistributionCard")

        layout = self.layout()

        header = QHBoxLayout()
        title = QLabel("Device distribution")
        title.setObjectName("DashboardTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        main_row = QHBoxLayout()

        self.chart = _DonutChart(self)
        main_row.addWidget(self.chart, 2)

        legend_col = QVBoxLayout()
        self.legend_labels: Dict[str, QLabel] = {}
        for key in ["keyboard", "mouse", "touchscreen", "touchpad", "unknown"]:
            lbl = QLabel(f"{key.title()}: 0")
            lbl.setObjectName("LegendLabel")
            legend_col.addWidget(lbl)
            self.legend_labels[key] = lbl
        legend_col.addStretch()

        main_row.addLayout(legend_col, 1)
        layout.addLayout(main_row)

    def update_from_distribution(self, distribution: Dict[str, int]) -> None:
        total = sum(distribution.values()) or 1
        segments: List[Tuple[float, QColor]] = []

        for key, count in distribution.items():
            frac = float(count) / float(total)
            color = self.COLORS.get(key, QColor(148, 163, 184))
            segments.append((frac, color))
            if key in self.legend_labels:
                self.legend_labels[key].setText(f"{key.title()}: {count}")

        self.chart.set_segments(segments)


class WeeklyActivityChart(FrostedCard):
    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, parent=None):
        super().__init__(parent, variant="weekly")
        self.setObjectName("WeeklyActivityCard")
        self.setMinimumHeight(180)

        layout = self.layout()
        layout.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        self.title_label = QLabel("Weekly activity")
        self.title_label.setObjectName("DashboardTitle")
        header.addWidget(self.title_label)
        header.addStretch()
        layout.addLayout(header)

        # Add stretch to push the chart area down
        layout.addStretch()

        self._values: List[int] = [0, 0, 0, 0, 0, 0, 0]  # Default values for all days

    def set_values(self, values: List[int]) -> None:
        # Ensure we always have 7 values
        self._values = (values[:7] + [0] * 7)[:7]
        self.update()

    def paintEvent(self, event):  # type: ignore[override]
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate chart area (below the title)
        card_rect = self.rect()
        # Leave space for title (top 50px) and day labels (bottom 20px)
        rect = card_rect.adjusted(28, 55, -28, -25)
        
        if rect.height() <= 0 or rect.width() <= 0:
            return

        max_val = max(self._values) if self._values else 1
        if max_val == 0:
            max_val = 1  # Prevent division by zero

        bar_count = 7
        total_gap = rect.width() * 0.3  # 30% of width for gaps
        bar_width = (rect.width() - total_gap) / bar_count
        gap = total_gap / (bar_count + 1)

        for i, value in enumerate(self._values):
            x = rect.left() + gap + i * (bar_width + gap)
            h = (value / max_val) * rect.height() if value > 0 else 4  # Minimum bar height
            y = rect.bottom() - h

            is_weekend = i >= 5
            color = QColor(99, 102, 241) if not is_weekend else QColor(139, 92, 246)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, y, bar_width, h), 4, 4)

            # Draw day label below the bar
            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("", 8))
            label_rect = QRectF(x, rect.bottom() + 4, bar_width, 16)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignHCenter, self.DAYS[i])


class _Sparkline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: List[int] = []
        self.setMinimumHeight(32)

    def push(self, value: int) -> None:
        self._values.append(value)
        self._values = self._values[-20:]
        self.update()

    def paintEvent(self, event):  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(4, 4, -4, -4)
        if len(self._values) < 2:
            return

        max_val = max(self._values) or 1
        step = rect.width() / (len(self._values) - 1)

        pen = QPen(QColor(129, 140, 248), 2.5)
        painter.setPen(pen)

        points: List[Tuple[float, float]] = []
        for i, val in enumerate(self._values):
            x = rect.left() + i * step
            y = rect.bottom() - (val / max_val) * rect.height()
            points.append((x, y))

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))


class ActiveDevicesMetric(FrostedCard):
    def __init__(self, parent=None):
        super().__init__(parent, variant="metric")
        self.setObjectName("ActiveDevicesCard")

        layout = self.layout()

        header = QHBoxLayout()
        title = QLabel("Locked devices")
        title.setObjectName("DashboardTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        main_row = QHBoxLayout()

        self.big_number = QLabel("0")
        self.big_number.setObjectName("BigMetric")
        main_row.addWidget(self.big_number, 0, Qt.AlignmentFlag.AlignVCenter)

        right_col = QVBoxLayout()
        self.sparkline = _Sparkline(self)
        right_col.addWidget(self.sparkline)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("LockedDevicesList")
        right_col.addWidget(self.list_widget)

        main_row.addLayout(right_col, 1)
        layout.addLayout(main_row)

    def update_from_data(self, total_locked: int, locked_names: List[str]) -> None:
        self.big_number.setText(str(total_locked))
        self.sparkline.push(total_locked)

        self.list_widget.clear()
        for name in locked_names[:6]:
            item = QListWidgetItem(name)
            self.list_widget.addItem(item)


class QuickActionsPanel(FrostedCard):
    lock_all_requested = pyqtSignal()
    unlock_all_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, variant="actions")
        self.setObjectName("QuickActionsCard")

        layout = self.layout()

        header = QHBoxLayout()
        title = QLabel("Quick actions")
        title.setObjectName("DashboardTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        row = QHBoxLayout()
        self.btn_lock = DangerButton("Lock all", self)
        self.btn_unlock = SuccessButton("Unlock all", self)

        self.btn_lock.clicked.connect(self.lock_all_requested)
        self.btn_unlock.clicked.connect(self.unlock_all_requested)

        row.addWidget(self.btn_lock)
        row.addWidget(self.btn_unlock)
        layout.addLayout(row)


class HotkeyStatusCard(FrostedCard):
    configure_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, variant="hotkeys")
        self.setObjectName("HotkeyStatusCard")

        layout = self.layout()

        header = QHBoxLayout()
        title = QLabel("Hotkey profile")
        title.setObjectName("DashboardTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.hotkey_label = QLabel("Current hotkey: -")
        self.hotkey_label.setObjectName("DashboardSubtitle")
        layout.addWidget(self.hotkey_label)

        self.configure_button = OutlineButton("Configure hotkeys", self)
        self.configure_button.clicked.connect(self.configure_requested)
        layout.addWidget(self.configure_button)

    def update_hotkey(self, hotkey: str) -> None:
        self.hotkey_label.setText(f"Current hotkey: {hotkey}")


__all__ = [
    "SystemStatusCard",
    "LockTimelineCard",
    "DeviceDistributionCard",
    "WeeklyActivityChart",
    "ActiveDevicesMetric",
    "QuickActionsPanel",
    "HotkeyStatusCard",
]
