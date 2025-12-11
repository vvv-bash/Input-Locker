"""Charts and visualizations for statistics and analytics."""
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen, QBrush
from PyQt6.QtCore import Qt, QPointF

from ..utils.logger import logger


@dataclass
class EventRecord:
    """Record of a lock/unlock event."""
    timestamp: datetime
    device: str
    event_type: str
    device_type: str = "unknown"


class StatisticsCollector:
    """Collect statistics about lock/unlock events."""
    
    def __init__(self):
        """Initialize the statistics collector."""
        self.events: List[EventRecord] = []
        self.lock_count: int = 0
        self.unlock_count: int = 0

    def record(self, event: EventRecord):
        """Record a new event and update counters."""
        self.events.append(event)
        if event.event_type == "lock":
            self.lock_count += 1
        elif event.event_type == "unlock":
            self.unlock_count += 1


class AnalyticsPanel(QWidget):
    """Panel for displaying analytics and statistics."""
    
    def __init__(self):
        """Initialize analytics panel."""
        super().__init__()
        self.setObjectName("analyticsPanel")
        self.collector = StatisticsCollector()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("📊 Analytics & Statistics")
        title.setObjectName("lblSubtitle")
        title.setFont(QFont("Segoe UI", 12))
        layout.addWidget(title)

        self.total_label = QLabel("Total events: 0")
        self.total_label.setObjectName("lblBody")
        layout.addWidget(self.total_label)

        # Locks row with tiny bar "chart"
        lock_row = QHBoxLayout()
        lock_row.setSpacing(6)
        lock_text = QLabel("Locks")
        lock_text.setObjectName("lblBody")
        lock_row.addWidget(lock_text)

        self.lock_bar = QProgressBar()
        self.lock_bar.setRange(0, 1)
        self.lock_bar.setValue(0)
        self.lock_bar.setTextVisible(False)
        lock_row.addWidget(self.lock_bar, 1)
        layout.addLayout(lock_row)

        # Unlocks row with tiny bar "chart"
        unlock_row = QHBoxLayout()
        unlock_row.setSpacing(6)
        unlock_text = QLabel("Unlocks")
        unlock_text.setObjectName("lblBody")
        unlock_row.addWidget(unlock_text)

        self.unlock_bar = QProgressBar()
        self.unlock_bar.setRange(0, 1)
        self.unlock_bar.setValue(0)
        self.unlock_bar.setTextVisible(False)
        unlock_row.addWidget(self.unlock_bar, 1)
        layout.addLayout(unlock_row)
        
        # Trend chart for recent lock activity (inline implementation below)
        self.trend_chart = _TrendChart(self, max_points=30, color=QColor(59, 130, 246))
        layout.addWidget(self.trend_chart)

        self.last_event_label = QLabel("Last event: –")
        self.last_event_label.setObjectName("lblBody")
        layout.addWidget(self.last_event_label)

        hint = QLabel("Lock/unlock activity will appear here as you use the app.")
        hint.setObjectName("lblCaption")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addStretch(1)

    def record_event(self, event_type: str, metadata: Optional[Dict] = None):
        """Record a lock/unlock event coming from the UI."""
        try:
            device_name = "devices" if not metadata else metadata.get("device", "devices")
            record = EventRecord(
                timestamp=datetime.now(),
                device=device_name,
                event_type=event_type,
                device_type=str(metadata.get("device_type", "unknown")) if metadata else "unknown",
            )
            self.collector.record(record)
            self._update_labels(record)
        except Exception as e:
            logger.warning(f"Error recording analytics event: {e}")

    def _update_labels(self, last: Optional[EventRecord] = None):
        """Refresh the summary labels."""
        total = len(self.collector.events)
        self.total_label.setText(f"Total events: {total}")

        # Update bar "charts" to reflect relative proportions
        locks = self.collector.lock_count
        unlocks = self.collector.unlock_count
        max_value = max(1, locks + unlocks)
        self.lock_bar.setRange(0, max_value)
        self.unlock_bar.setRange(0, max_value)
        self.lock_bar.setValue(locks)
        self.unlock_bar.setValue(unlocks)

        # Feed recent lock count trend into the chart
        if self.collector.events:
            history = []
            running_locks = 0
            for ev in self.collector.events[-30:]:
                if ev.event_type == "lock":
                    running_locks += 1
                history.append(float(running_locks))
            self.trend_chart.set_values(history)

        if last is None and self.collector.events:
            last = self.collector.events[-1]
        if last is not None:
            ts = last.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            self.last_event_label.setText(f"Last event: {ts} ({last.event_type})")


class _TrendChart(QWidget):
    """Lightweight inline line chart for analytics history.

    This avoids an external module dependency while still giving a
    clean, glass-styled sparkline similar to the performance chart.
    """

    def __init__(self, parent=None, max_points: int = 60, color: QColor | None = None):
        super().__init__(parent)
        self._values: List[float] = []
        self._max_points = max_points
        self._color = color or QColor(59, 130, 246)
        self.setMinimumHeight(70)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_values(self, values):
        self._values = list(values)[-self._max_points :]
        self.update()

    def add_value(self, value: float):
        self._values.append(float(value))
        if len(self._values) > self._max_points:
            self._values = self._values[-self._max_points :]
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)

        bg_color = QColor(15, 23, 42, 210)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(148, 163, 184, 180), 1))
        radius = 10
        painter.drawRoundedRect(rect, radius, radius)

        if not self._values:
            painter.end()
            return

        min_val = min(self._values)
        max_val = max(self._values)
        if max_val - min_val < 1e-6:
            min_val -= 0.5
            max_val += 0.5

        width = rect.width()
        height = rect.height()
        count = len(self._values)
        step_x = width / max(count - 1, 1)

        path = QPainterPath()
        points = []
        for i, v in enumerate(self._values):
            norm = (v - min_val) / (max_val - min_val)
            x = rect.left() + i * step_x
            y = rect.bottom() - norm * height
            points.append(QPointF(x, y))

        if points:
            path.moveTo(points[0])
            for p in points[1:]:
                path.lineTo(p)

            pen = QPen(self._color, 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

            last = points[-1]
            highlight = QColor(self._color)
            highlight.setAlpha(230)
            painter.setBrush(QBrush(highlight))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(last, 3.5, 3.5)

        painter.end()
