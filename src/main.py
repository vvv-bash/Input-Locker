"""
Main entry point for Input Locker.
"""

import sys
import os
import signal
from pathlib import Path

# IMPORTANTE: Agregar el directorio raíz al path ANTES de cualquier import
APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal

# Imports de módulos propios
from src.core.device_manager import DeviceManager
from src.core.input_blocker import InputBlocker
from src.core.config_manager import ConfigManager
from src.core.hotkey_handler import HotkeyHandler
from src.gui.main_window import MainWindow
from src.utils.logger import logger
from src.utils.privileges import PrivilegeManager


class HotkeySignalBridge(QObject):
    """Bridge to safely invoke hotkey callback on Qt main thread."""
    hotkey_triggered = pyqtSignal()


class InputLockerApp:
    """Aplicación principal Input Locker."""
    
    def __init__(self):
        """Initialize the application."""
        logger.info("=" * 60)
        logger.info("Input Locker - Starting application")
        logger.info("=" * 60)
        
        # Check privileges
        if not self._check_privileges():
            sys.exit(1)
        
        # Crear aplicación Qt
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Input Locker")
        self.app.setOrganizationName("InputLocker")
        
        # Configurar estilo de aplicación
        self.app.setStyle("Fusion")
        
        # Signal bridge para hotkey
        self._signal_bridge = HotkeySignalBridge()
        
        # Componentes core
        self.config_manager = None
        self.device_manager = None
        self.input_blocker = None
        self.hotkey_handler = None
        self.main_window = None
        
        # Inicializar componentes
        self._init_components()
        
        # Configurar handlers de señales
        self._setup_signal_handlers()
        
        logger.info("Aplicación inicializada correctamente")
    
    def _check_privileges(self) -> bool:
        """
        Check and request necessary privileges.

        Returns:
            bool: True if running with sufficient privileges
        """
        if PrivilegeManager.is_root():
            logger.info("Running with root privileges ✓")
            return True
        
        logger.warning("No root privileges")
        
        # Mostrar diálogo en modo gráfico
        app = QApplication(sys.argv)
        reply = QMessageBox.question(
            None,
            "Privileges Required",
            "Input Locker requires administrator privileges to "
            "access input devices.\n\n"
            "Do you want to elevate privileges now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("User requested privilege elevation")
            if PrivilegeManager.elevate_privileges():
                return True
        
        QMessageBox.critical(
            None,
            "Error",
            "Cannot continue without administrator privileges.\n\n"
            "Please run the application with:\n"
            "sudo input-locker"
        )
        return False
    
    def _init_components(self):
        """Initialize all application components."""
        try:
            # Config Manager
            logger.info("Initializing configuration manager...")
            self.config_manager = ConfigManager()
            
            # Device Manager
            logger.info("Initializing device manager...")
            self.device_manager = DeviceManager()
            summary = self.device_manager.get_summary()
            logger.info(f"Devices detected: {summary}")
            
            # Hotkey Handler (for when NOT locked)
            logger.info("Initializing hotkey handler...")
            hotkey = self.config_manager.get_hotkey()
            self.hotkey_handler = HotkeyHandler(hotkey)
            
            # Input Blocker (pass the hotkey_handler)
            logger.info("Initializing input blocker...")
            self.input_blocker = InputBlocker(
                self.device_manager,
                self.config_manager,
                self.hotkey_handler  # ← Pasar el hotkey_handler
            )
            
            # Callback del hotkey cuando NO está bloqueado
            self._hotkey_lock = False
            
            def _on_hotkey_signal():
                """Handler that runs on Qt main thread."""
                logger.info("🎯 Hotkey signal received on main thread")
                logger.info(f"Current locked state: {self.input_blocker.is_locked}")
                
                try:
                    self._handle_hotkey()
                except Exception as e:
                    logger.error(f"Error en _on_hotkey_signal: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                finally:
                    # Reset lock after a short delay
                    QTimer.singleShot(300, self._reset_hotkey_lock)
            
            # Conectar la señal al handler que corre en el thread principal
            self._signal_bridge.hotkey_triggered.connect(_on_hotkey_signal, Qt.ConnectionType.QueuedConnection)
            
            def toggle_lock_from_global_hotkey():
                """Called from background thread, emits signal to main thread."""
                if self._hotkey_lock:
                    logger.debug("Hotkey already being processed, ignoring duplicate")
                    return
                self._hotkey_lock = True
                
                logger.info("🎯 Global hotkey callback - emitting signal")
                # Emit signal to handle on main thread (thread-safe)
                self._signal_bridge.hotkey_triggered.emit()
            
            self.hotkey_handler.set_callback(toggle_lock_from_global_hotkey)
            self.hotkey_handler.start()
            
            # Main Window
            logger.info("Initializing main window...")
            self.main_window = MainWindow(
                self.device_manager,
                self.input_blocker,
                self.config_manager,
                self.hotkey_handler
            )
            
            # Conectar señales del input_blocker con la UI
            self.input_blocker.lock_changed.connect(
                lambda locked: self._on_lock_changed(locked)
            )
            
            # Verificar si debe iniciar bloqueado
            if self.config_manager.get('general', 'autostart_blocked', False):
                logger.info("Config: start locked")
                QTimer.singleShot(100, self.input_blocker.lock_all)
            
            # Verificar si debe iniciar minimizado
            if self.config_manager.get('ui', 'start_minimized', False):
                logger.info("Config: start minimized")
                # Do not show window, only tray
            else:
                self.main_window.show()
                
        except Exception as e:
            logger.critical(f"Fatal error initializing components: {e}")
            import traceback
            logger.critical(traceback.format_exc())
            QMessageBox.critical(
                None,
                "Fatal Error",
                f"Could not initialize the application:\n\n{str(e)}"
            )
            sys.exit(1)
    
    def _on_lock_changed(self, locked):
        """Callback when the lock state changes."""
        logger.info(f"📢 lock_changed signal received: locked={locked}")
        if self.main_window:
            self.main_window._update_ui_state()
    
    def _handle_hotkey(self):
        """Handle the hotkey on the Qt main thread."""
        logger.info("🔧 _handle_hotkey called")
        
        try:
            current_state = self.input_blocker.is_locked
            logger.info(f"Current state: {'LOCKED' if current_state else 'UNLOCKED'}")
            
            if current_state:
                logger.info("→ Action: UNLOCK")
                self.input_blocker.unlock_all()
            else:
                logger.info("→ Action: LOCK")
                self.input_blocker.lock_all()
            
            logger.info(f"✓ Hotkey processed. New state: {'LOCKED' if self.input_blocker.is_locked else 'UNLOCKED'}")
            
        except Exception as e:
            logger.error(f"❌ Error handling hotkey: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _reset_hotkey_lock(self):
        """Reset the hotkey lock flag."""
        logger.debug("Resetting hotkey lock flag")
        self._hotkey_lock = False
    
    def _setup_signal_handlers(self):
        """Configura handlers para señales del sistema."""
        def signal_handler(sig, frame):
            logger.warning(f"Signal received: {sig}")
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def cleanup(self):
        """Limpia recursos antes de salir."""
        logger.info("Cleaning up resources...")
        try:
            # Desbloquear todos los dispositivos
            if self.input_blocker:
                self.input_blocker.unlock_all()
            
            # Detener hotkey handler
            if self.hotkey_handler:
                self.hotkey_handler.stop()
            
            logger.info("Resources released successfully")
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
    
    def run(self) -> int:
        """
        Ejecuta la aplicación.
        
        Returns:
            int: Código de salida
        """
        try:
            logger.info("Starting Qt event loop...")
            exit_code = self.app.exec()
            logger.info(f"Application exited with code: {exit_code}")
            return exit_code
        except Exception as e:
            logger.critical(f"Error in main loop: {e}")
            import traceback
            logger.critical(traceback.format_exc())
            return 1
        finally:
            self.cleanup()


def main():
    """Función principal."""
    try:
        app = InputLockerApp()
        sys.exit(app.run())
    except Exception as e:
        logger.critical(f"Unhandled fatal error: {e}")
        import traceback
        logger.critical(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()