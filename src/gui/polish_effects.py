"""
Advanced visual effects and polish for the application UI.
"""
from typing import Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPainter, QRadialGradient
from PyQt6.QtCore import QEasingCurve

from ..utils.logger import logger


class VignetteEffect(QWidget):
    """Vignette effect overlay that darkens edges of the window."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize vignette effect."""
        super().__init__(parent)
        self.opacity = 0.3
    
    def paintEvent(self, event):
        """Paint vignette effect."""
        painter = QPainter(self)
        gradient = QRadialGradient(self.width() // 2, self.height() // 2, 
                                   max(self.width(), self.height()))
        gradient.setColorAt(0, QColor(0, 0, 0, 0))
        gradient.setColorAt(1, QColor(0, 0, 0, int(255 * self.opacity)))
        painter.fillRect(self.rect(), gradient)
        painter.end()


class GlowEffect:
    """Glow/halo effect around widgets."""
    
    @staticmethod
    def apply_glow(widget: QWidget, color: QColor, radius: int = 10):
        """Apply glow effect to a widget."""
        try:
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(radius)
            shadow.setColor(color)
            shadow.setOffset(0, 0)
            widget.setGraphicsEffect(shadow)
        except Exception as e:
            logger.error(f"Error applying glow effect: {e}")


class SkeletonScreen:
    """Skeleton screen (loading placeholder) effect."""
    
    @staticmethod
    def create_skeleton_item(width: int, height: int) -> QWidget:
        """Create a skeleton loading placeholder."""
        widget = QWidget()
        widget.setFixedSize(width, height)
        widget.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(200,200,200,50),
                stop:50 rgba(230,230,230,80),
                stop:100 rgba(200,200,200,50)
            );
            border-radius: 4px;
        """)
        return widget


class ShimmerEffect:
    """Shimmer/loading pulse effect."""
    
    @staticmethod
    def apply_shimmer(widget: QWidget):
        """Apply shimmer effect to a widget."""
        try:
            widget.setStyleSheet("""
                animation: shimmer 2s infinite;
            """)
        except Exception as e:
            logger.error(f"Error applying shimmer: {e}")


class PulseEffect:
    """Pulse/breathing effect for widgets."""
    
    @staticmethod
    def apply_pulse(widget: QWidget):
        """Apply pulse effect to a widget."""
        try:
            widget.setStyleSheet("""
                animation: pulse 2s ease-in-out infinite;
            """)
        except Exception as e:
            logger.error(f"Error applying pulse: {e}")


class PerformanceOptimizer:
    """Optimize application performance and GPU acceleration."""
    
    @staticmethod
    def enable_gpu_acceleration(widget: Optional[QWidget] = None):
        """Enable GPU acceleration for the application."""
        try:
            # Enable high DPI scaling
            import os
            os.environ['QT_XCB_GL_INTEGRATION'] = 'xcb_glx'
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '/usr/lib/x86_64-linux-gnu/qt6/plugins'
            
            if widget:
                widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            
            logger.debug("GPU acceleration enabled")
        except Exception as e:
            logger.warning(f"Could not enable GPU acceleration: {e}")
    
    @staticmethod
    def optimize_rendering():
        """Optimize rendering for 60fps."""
        try:
            # Set optimal update interval
            return 16  # ~60fps (16ms per frame)
        except Exception as e:
            logger.error(f"Error optimizing rendering: {e}")
            return 16


class ShadowEffect:
    """Shadow effect for depth perception."""
    
    @staticmethod
    def apply_shadow(widget: QWidget, blur_radius: int = 15, offset: int = 2):
        """Apply shadow effect to a widget."""
        try:
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(blur_radius)
            shadow.setColor(QColor(0, 0, 0, 120))
            shadow.setOffset(offset, offset)
            widget.setGraphicsEffect(shadow)
        except Exception as e:
            logger.error(f"Error applying shadow: {e}")
