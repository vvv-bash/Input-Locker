from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QPushButton


class GradientBackground(QWidget):
	"""Animated gradient background for the dashboard and hero areas.

	Provides a subtle diagonal movement using a multi-stop blue/indigo
	gradient that reinforces the premium dashboard look.
	"""

	def __init__(self, parent=None):
		super().__init__(parent)
		self._phase = 0.0
		self._timer = QTimer(self)
		self._timer.timeout.connect(self._advance_phase)
		self._timer.start(40)  # ~25 FPS for smooth but cheap animation
		self.setObjectName("DashboardBackground")

	def _advance_phase(self) -> None:
		self._phase = (self._phase + 0.004) % 1.0
		self.update()

	def paintEvent(self, event) -> None:  # type: ignore[override]
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)

		rect = self.rect()
		gradient = QLinearGradient(float(rect.left()), float(rect.top()), float(rect.right()), float(rect.bottom()))

		p = self._phase
		# Deep navy to cyan-ish gradient, slowly shifting mid stops
		gradient.setColorAt(0.0, QColor(2, 6, 23))          # #020617
		gradient.setColorAt(max(0.2, 0.35 - 0.1 * p), QColor(15, 23, 42))
		gradient.setColorAt(min(0.9, 0.65 + 0.15 * p), QColor(8, 47, 73))
		gradient.setColorAt(1.0, QColor(15, 23, 42))

		painter.fillRect(rect, gradient)


class FrostedCard(QFrame):
	"""Glassmorphic card container used across the dashboard.

	Styling is provided via QSS using the objectName and a custom
	"variant" property that can distinguish card roles (status, metric, etc.).
	"""

	def __init__(self, parent=None, variant: str | None = None):
		super().__init__(parent)
		self.setObjectName("FrostedCard")
		if variant:
			self.setProperty("variant", variant)
		layout = QVBoxLayout(self)
		layout.setContentsMargins(16, 16, 16, 16)
		layout.setSpacing(8)


class ModernButton(QPushButton):
	"""Base modern button with rounded corners and bold typography.

	Concrete variants are styled via objectName in QSS.
	"""

	def __init__(self, label: str, parent=None):
		super().__init__(label, parent)
		self.setMinimumHeight(32)
		self.setCursor(Qt.CursorShape.PointingHandCursor)


class PrimaryButton(ModernButton):
	def __init__(self, label: str, parent=None):
		super().__init__(label, parent)
		self.setObjectName("PrimaryButton")


class DangerButton(ModernButton):
	def __init__(self, label: str, parent=None):
		super().__init__(label, parent)
		self.setObjectName("DangerButton")


class SuccessButton(ModernButton):
	def __init__(self, label: str, parent=None):
		super().__init__(label, parent)
		self.setObjectName("SuccessButton")


class OutlineButton(ModernButton):
	def __init__(self, label: str, parent=None):
		super().__init__(label, parent)
		self.setObjectName("OutlineButton")

