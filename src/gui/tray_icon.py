"""
System tray icon with context menu.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject

from ..utils.logger import logger


class TrayIcon(QSystemTrayIcon):
    """System tray icon for Input Locker."""
    
    # Signals
    toggle_lock_requested = pyqtSignal()
    show_window_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    logs_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the tray icon."""
        super().__init__(parent)
        
        self.is_locked = False
        
        self._create_menu()
        self._update_icon()
        
        # Conectar señales
        self.activated.connect(self._on_activated)
        
        logger.info("Tray icon initialized")
    
    def _create_menu(self):
        """Create the context menu."""
        self.menu = QMenu()
        
        # Title
        self.title_action = self.menu.addAction("🔒 Input Locker")
        self.title_action.setEnabled(False)
        
        self.menu.addSeparator()
        
        # Status
        self.status_action = self.menu.addAction("● Status: Unlocked")
        self.status_action.setEnabled(False)
        
        self.menu.addSeparator()
        
        # Toggle lock
        self.toggle_action = QAction("⚡ Toggle Lock", self)
        self.toggle_action.triggered.connect(self.toggle_lock_requested.emit)
        self.menu.addAction(self.toggle_action)
        
        # Show window
        show_action = QAction("📋 Show Window", self)
        show_action.triggered.connect(self.show_window_requested.emit)
        self.menu.addAction(show_action)
        
        # Settings
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        self.menu.addAction(settings_action)
        
        self.menu.addSeparator()
        
        # Reload devices
        refresh_action = QAction("🔄 Reload Devices", self)
        refresh_action.triggered.connect(self.refresh_requested.emit)
        self.menu.addAction(refresh_action)
        
        # View logs
        logs_action = QAction("📊 View Logs", self)
        logs_action.triggered.connect(self.logs_requested.emit)
        self.menu.addAction(logs_action)
        
        self.menu.addSeparator()
        
        # Quit
        quit_action = QAction("❌ Quit", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)
        
        self.setContextMenu(self.menu)
    
    def _update_icon(self):
        """Update the icon according to the state."""
        try:
            style = None
            parent = self.parent()
            if parent is not None:
                style = parent.style()
            if style is None and hasattr(self, "menu") and self.menu is not None:
                style = self.menu.style()

            if style is not None:
                if self.is_locked:
                    icon = style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
                    self.setToolTip("Input Locker - 🔒 LOCKED")
                else:
                    icon = style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
                    self.setToolTip("Input Locker - 🔓 Unlocked")

                self.setIcon(icon)
            else:
                # As a last resort, update only the tooltip
                if self.is_locked:
                    self.setToolTip("Input Locker - 🔒 LOCKED")
                else:
                    self.setToolTip("Input Locker - 🔓 Unlocked")
        except Exception:
            if self.is_locked:
                self.setToolTip("Input Locker - 🔒 LOCKED")
            else:
                self.setToolTip("Input Locker - 🔓 Unlocked")
    
    def _on_activated(self, reason):
        """Callback when the icon is interacted with."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Click izquierdo - alternar bloqueo
            self.toggle_lock_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Doble click - mostrar ventana
            self.show_window_requested.emit()
    
    def update_status(self, is_locked: bool):
        """
        Update the visual state of the tray icon.

        Args:
            is_locked: True if locked
        """
        self.is_locked = is_locked
        
        # Actualizar texto del estado
        status_text = "🔒 Locked" if is_locked else "🔓 Unlocked"
        self.status_action.setText(f"● Status: {status_text}")
        
        # Actualizar texto del toggle
        toggle_text = "🔓 Unlock" if is_locked else "🔒 Lock"
        self.toggle_action.setText(f"⚡ {toggle_text}")
        
        # Actualizar icono y tooltip
        self._update_icon()
        
        logger.debug(f"Tray icon updated: {'Locked' if is_locked else 'Unlocked'}")
    
    def show_notification(self, title: str, message: str, icon=None):
        """
        Show a system notification.
        
        Args:
            title: Notification title
            message: Message body
            icon: Optional icon
        """
        if icon is None:
            icon = QSystemTrayIcon.MessageIcon.Information

        self.showMessage(title, message, icon, 3000)  # 3 seconds
        logger.debug(f"Notification shown: {title} - {message}")

