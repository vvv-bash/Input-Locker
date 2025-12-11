"""Profiling viewer for monitoring application performance.

This panel shows lightweight, live CPU and memory usage for the
current process so you can quickly spot abnormal behavior while
keeping the UI clean and modern.
"""

import os
import time
from typing import Deque
from collections import deque
from dataclasses import dataclass

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, QTimer, Qt, QPointF
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen, QBrush

from ..utils.logger import logger


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    thread_count: int


class TrendChart(QWidget):
    """Lightweight line chart for performance history.

    Implemented inline to avoid external module dependencies in
    constrained environments, while still giving a modern, clean graph.
    """

    def __init__(self, parent=None, max_points: int = 60, color: QColor | None = None):
        super().__init__(parent)
        self._values: Deque[float] = deque(maxlen=max_points)
        self._color = color or QColor(59, 130, 246)
        self.setMinimumHeight(70)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_values(self, values):
        self._values.clear()
        for v in list(values)[-self._values.maxlen :]:
            self._values.append(float(v))
        self.update()

    def add_value(self, value: float):
        self._values.append(float(value))
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)

        # Glass-like card background
        bg_color = QColor(15, 23, 42, 210)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(148, 163, 184, 180), 1))
        radius = 10
        painter.drawRoundedRect(rect, radius, radius)

        if not self._values:
            painter.end()
            return

        values = list(self._values)
        min_val = min(values)
        max_val = max(values)
        if max_val - min_val < 1e-6:
            min_val -= 0.5
            max_val += 0.5

        width = rect.width()
        height = rect.height()
        count = len(values)
        step_x = width / max(count - 1, 1)

        path = QPainterPath()
        points = []
        for i, v in enumerate(values):
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


class ProfilingViewer(QWidget):
    """Widget for monitoring application performance."""
    
    metrics_updated = pyqtSignal(PerformanceMetrics)
    
    def __init__(self, update_interval: int = 1000):
        """Initialize the profiling viewer."""
        super().__init__()
        self.setObjectName("profilingPanel")
        self.metrics_history: Deque[PerformanceMetrics] = deque(maxlen=60)
        self._pid = os.getpid()
        self._update_interval = update_interval

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("📈 Performance Monitor")
        title.setObjectName("lblSubtitle")
        layout.addWidget(title)

        # CPU row with visual bar
        cpu_row = QHBoxLayout()
        cpu_row.setSpacing(6)
        cpu_label = QLabel("CPU Usage")
        cpu_label.setObjectName("lblBody")
        cpu_row.addWidget(cpu_label)

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setValue(0)
        self.cpu_bar.setTextVisible(False)
        cpu_row.addWidget(self.cpu_bar, 1)
        layout.addLayout(cpu_row)

        # Memory row with visual bar
        mem_row = QHBoxLayout()
        mem_row.setSpacing(6)
        mem_label = QLabel("Memory Usage")
        mem_label.setObjectName("lblBody")
        mem_row.addWidget(mem_label)

        self.mem_bar = QProgressBar()
        self.mem_bar.setRange(0, 100)
        self.mem_bar.setValue(0)
        self.mem_bar.setTextVisible(False)
        mem_row.addWidget(self.mem_bar, 1)
        layout.addLayout(mem_row)

        # CPU trend chart below bars
        self.cpu_chart = TrendChart(self, max_points=60, color=QColor(59, 130, 246))
        layout.addWidget(self.cpu_chart)

        self.summary_label = QLabel("Collecting metrics…")
        self.summary_label.setObjectName("lblBody")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.detail_label = QLabel("")
        self.detail_label.setObjectName("lblCaption")
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)

        layout.addStretch(1)

        # Timer to periodically sample metrics
        self._timer = QTimer(self)
        self._timer.setInterval(self._update_interval)
        self._timer.timeout.connect(self._sample_metrics)
        self._timer.start()

        # Take an initial sample so the panel is not empty
        self._sample_metrics()

    def _sample_metrics(self):
        """Sample CPU and memory usage for the current process."""
        try:
            # We use psutil if available for accuracy; otherwise fall back
            # to /proc-based approximations.
            try:
                import psutil  # type: ignore[import]

                proc = psutil.Process(self._pid)
                cpu = proc.cpu_percent(interval=0.0)
                mem_info = proc.memory_info()
                mem_mb = mem_info.rss / (1024 * 1024)
                mem_percent = proc.memory_percent()
                threads = proc.num_threads()
            except Exception:
                cpu = 0.0
                mem_mb = 0.0
                mem_percent = 0.0
                threads = 0

            snapshot = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu,
                memory_percent=mem_percent,
                memory_mb=mem_mb,
                thread_count=threads,
            )
            self.metrics_history.append(snapshot)
            self.metrics_updated.emit(snapshot)

            # Update labels with a compact, modern summary
            self.cpu_bar.setValue(int(max(0.0, min(snapshot.cpu_percent, 100.0))))
            self.mem_bar.setValue(int(max(0.0, min(snapshot.memory_percent, 100.0))))

            self.summary_label.setText(
                f"CPU: {snapshot.cpu_percent:.1f}%   •   "
                f"Memory: {snapshot.memory_mb:.1f} MB ({snapshot.memory_percent:.1f}%)   •   "
                f"Threads: {snapshot.thread_count}"
            )

            if self.metrics_history:
                avg_cpu = sum(m.cpu_percent for m in self.metrics_history) / len(self.metrics_history)
                self.detail_label.setText(
                    f"Last {len(self.metrics_history)} samples — Avg CPU: {avg_cpu:.1f}%"
                )
                # Update CPU trend line
                history = [m.cpu_percent for m in self.metrics_history]
                self.cpu_chart.set_values(history)
        except Exception as e:
            logger.warning(f"Error sampling performance metrics: {e}")
