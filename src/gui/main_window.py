"""
Main application window for Input Locker.
"""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QCloseEvent, QPalette, QColor, QFontDatabase
from PyQt6.QtWidgets import QGraphicsOpacityEffect

from .device_list_widget import DeviceListWidget
from .settings_dialog import SettingsDialog
from .settings_widget import SettingsWidget
from .log_viewer import LogViewer
from .tray_icon import TrayIcon

# Phase 0-7 Integration
from .theme_manager import ThemeManager
from .animations import AnimationManager
from .help_system import HelpPanel, HelpSystem
from .dependency_viewer import DependencyViewer
from .profiling_viewer import ProfilingViewer
from .charts import AnalyticsPanel
from .polish_effects import PerformanceOptimizer, ShadowEffect
from .glassmorphic_widgets import GradientBackground
from .dashboard.dashboard_window import DashboardWindow

from ..core.device_manager import DeviceManager
from ..core.input_blocker import InputBlocker
from ..core.config_manager import ConfigManager
from ..core.hotkey_handler import HotkeyHandler
from ..core.power_manager import PowerManager
from ..utils.logger import logger
from ..utils.hotkey_manager import HotkeyManager
from ..utils.conflict_detector import ConflictDetector
from .animation_utils import fade_transition


class MainWindow(QMainWindow):
    """Main window for Input Locker."""
    
    # Señales
    lock_state_changed = pyqtSignal(bool)  # True = bloqueado
    
    def __init__(
        self,
        device_manager: DeviceManager,
        input_blocker: InputBlocker,
        config_manager: ConfigManager,
        hotkey_handler: HotkeyHandler
    ):
        """
        Initialize the main window.

        Args:
            device_manager: Device manager
            input_blocker: Input blocker
            config_manager: Configuration manager
            hotkey_handler: Hotkey handler
        """
        super().__init__()
        
        self.device_manager = device_manager
        self.input_blocker = input_blocker
        self.config_manager = config_manager
        self.hotkey_handler = hotkey_handler
        
        # Phase 0-7 Managers
        self.theme_manager = ThemeManager()
        self.hotkey_manager = HotkeyManager()
        self.power_manager = PowerManager()
        self.conflict_detector = ConflictDetector()
        
        self.tray_icon = None
        self.dashboard_window = None
        # Last bulk action for undo support
        self._last_bulk_action = None
        
        # Enable GPU acceleration for smooth animations (Phase 7)
        PerformanceOptimizer.enable_gpu_acceleration(self.parent())
        
        self._init_ui()
        self._setup_tray()
        self._apply_theme()
        self._update_ui_state()
        
        # Timer for device refresh (initialized after UI creation)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._refresh_device_list)
        self.update_timer.start(5000)

    def _init_ui(self):
        """Initialize the user interface with a modern sidebar + pages layout."""
        self.setWindowTitle("Input Locker")
        self.setMinimumSize(900, 640)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        # ══════════════════════════════════════════════════════════════════
        # SIDEBAR — dark nav rail inspired by the reference design
        # ══════════════════════════════════════════════════════════════════
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(6)
        self.sidebar.setFixedWidth(200)

        # Brand row
        brand_row = QHBoxLayout()
        brand_icon = QLabel("🔒")
        brand_icon.setStyleSheet("font-size: 22px;")
        brand_row.addWidget(brand_icon)
        brand_name = QLabel("Input Locker")
        brand_name.setObjectName("sidebarBrand")
        brand_row.addWidget(brand_name)
        brand_row.addStretch()
        sidebar_layout.addLayout(brand_row)

        sidebar_layout.addSpacing(24)

        # ── Main nav group ──
        self.btn_nav_dashboard = QPushButton("Dashboard")
        self.btn_nav_dashboard.setObjectName("navBtn")
        self.btn_nav_dashboard.setCheckable(True)
        self.btn_nav_dashboard.setChecked(True)
        self.btn_nav_dashboard.clicked.connect(self._show_dashboard)
        sidebar_layout.addWidget(self.btn_nav_dashboard)

        self.btn_nav_status = QPushButton("Status")
        self.btn_nav_status.setObjectName("navBtn")
        self.btn_nav_status.setCheckable(True)
        self.btn_nav_status.clicked.connect(lambda: self._switch_to_page(0))
        sidebar_layout.addWidget(self.btn_nav_status)

        self.btn_nav_devices = QPushButton("Devices")
        self.btn_nav_devices.setObjectName("navBtn")
        self.btn_nav_devices.setCheckable(True)
        self.btn_nav_devices.clicked.connect(lambda: self._switch_to_page(1))
        sidebar_layout.addWidget(self.btn_nav_devices)

        self.btn_nav_analytics = QPushButton("Analytics")
        self.btn_nav_analytics.setObjectName("navBtn")
        self.btn_nav_analytics.setCheckable(True)
        self.btn_nav_analytics.clicked.connect(lambda: self._switch_to_page(3))
        sidebar_layout.addWidget(self.btn_nav_analytics)

        self.btn_nav_settings = QPushButton("Settings")
        self.btn_nav_settings.setObjectName("navBtn")
        self.btn_nav_settings.setCheckable(True)
        self.btn_nav_settings.clicked.connect(lambda: self._switch_to_page(2))
        sidebar_layout.addWidget(self.btn_nav_settings)

        sidebar_layout.addSpacing(18)

        # ── Others section ──
        others_label = QLabel("Others")
        others_label.setObjectName("sidebarSection")
        sidebar_layout.addWidget(others_label)

        self.btn_nav_logs = QPushButton("Logs")
        self.btn_nav_logs.setObjectName("navBtn")
        self.btn_nav_logs.setCheckable(True)
        self.btn_nav_logs.clicked.connect(self._show_logs)
        sidebar_layout.addWidget(self.btn_nav_logs)

        self.btn_nav_help = QPushButton("Help")
        self.btn_nav_help.setObjectName("navBtn")
        self.btn_nav_help.setCheckable(True)
        self.btn_nav_help.clicked.connect(lambda: self._switch_to_page(4))
        sidebar_layout.addWidget(self.btn_nav_help)

        self.btn_nav_diagnostics = QPushButton("Diagnostics")
        self.btn_nav_diagnostics.setObjectName("navBtn")
        self.btn_nav_diagnostics.setCheckable(True)
        self.btn_nav_diagnostics.clicked.connect(lambda: self._switch_to_page(5))
        sidebar_layout.addWidget(self.btn_nav_diagnostics)

        sidebar_layout.addStretch()

        # ── Lock action button ──
        self.btn_quick_lock = QPushButton("Lock Now")
        self.btn_quick_lock.setObjectName("lockBtn")
        self.btn_quick_lock.clicked.connect(self._toggle_lock)
        sidebar_layout.addWidget(self.btn_quick_lock)

        root_layout.addWidget(self.sidebar, 0)

        # Stacked pages area (wrapped in a vertical container so we can show an undo bar)
        from PyQt6.QtWidgets import QStackedWidget
        self.pages = QStackedWidget()

        # Container to hold pages + transient undo bar
        pages_container = QWidget()
        pages_container_layout = QVBoxLayout(pages_container)
        pages_container_layout.setContentsMargins(0, 0, 0, 0)
        pages_container_layout.setSpacing(6)
        pages_container_layout.addWidget(self.pages)

        # Undo bar (hidden by default) — non-blocking temporary notification with Undo
        from PyQt6.QtWidgets import QFrame, QSpacerItem, QSizePolicy
        self.undo_bar = QFrame()
        self.undo_bar.setObjectName("undoBar")
        self.undo_bar.hide()
        undo_layout = QHBoxLayout(self.undo_bar)
        undo_layout.setContentsMargins(8, 6, 8, 6)

        self.undo_label = QLabel("")
        undo_layout.addWidget(self.undo_label)

        undo_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.undo_button = QPushButton("Undo")
        self.undo_button.setObjectName("btnSecondary")
        self.undo_button.clicked.connect(self._perform_undo)
        undo_layout.addWidget(self.undo_button)

        pages_container_layout.addWidget(self.undo_bar)

        # Confirm bar (for inline confirmation of bulk actions)
        self.confirm_bar = QFrame()
        self.confirm_bar.setObjectName("confirmBar")
        self.confirm_bar.hide()
        confirm_layout = QHBoxLayout(self.confirm_bar)
        confirm_layout.setContentsMargins(8, 6, 8, 6)

        self.confirm_label = QLabel("")
        confirm_layout.addWidget(self.confirm_label)

        confirm_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setObjectName("btnPrimary")
        self.confirm_button.clicked.connect(self._confirm_action)
        confirm_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("btnSecondary")
        self.cancel_button.clicked.connect(self._cancel_action)
        confirm_layout.addWidget(self.cancel_button)

        pages_container_layout.addWidget(self.confirm_bar)

        # Page 0: Status (Enhanced)
        status_page = self._create_status_page()
        self.pages.addWidget(status_page)

        # Page 1: Devices
        devices_page = QWidget()
        devices_page_layout = QHBoxLayout(devices_page)
        devices_page_layout.setContentsMargins(8, 8, 8, 8)
        devices_page_layout.setSpacing(8)

        # Left: list and controls
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Devices actions: search, filter, bulk block/unblock
        control_row = QHBoxLayout()

        from PyQt6.QtWidgets import QLineEdit, QComboBox
        self.device_search = QLineEdit()
        self.device_search.setPlaceholderText("Search devices by name or path...")
        self.device_search.textChanged.connect(self._filter_devices)
        control_row.addWidget(self.device_search)

        self.device_type_filter = QComboBox()
        self.device_type_filter.addItems(["All", "Keyboards", "Mice", "Touchscreens", "Touchpads", "Unknown"])
        self.device_type_filter.currentIndexChanged.connect(self._filter_devices)
        control_row.addWidget(self.device_type_filter)

        btn_block_sel = QPushButton("🔒 Block Selected")
        btn_block_sel.setObjectName("btnSecondary")
        btn_block_sel.clicked.connect(self._block_selected)
        control_row.addWidget(btn_block_sel)

        btn_unblock_sel = QPushButton("🔓 Unblock Selected")
        btn_unblock_sel.setObjectName("btnSecondary")
        btn_unblock_sel.clicked.connect(self._unblock_selected)
        control_row.addWidget(btn_unblock_sel)

        left_layout.addLayout(control_row)

        # Device list
        self.device_list = DeviceListWidget()
        self.device_list.device_selected.connect(self._on_device_selected)
        self.device_list.selection_changed.connect(self._on_device_selection_changed)
        left_layout.addWidget(self.device_list)

        devices_page_layout.addWidget(left_col, 3)

        # Right: device details / actions
        details_col = QWidget()
        details_layout = QVBoxLayout(details_col)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        self.device_details_title = QLabel("Device Details")
        self.device_details_title.setObjectName("lblTitle")
        details_layout.addWidget(self.device_details_title)

        self.device_details_info = QLabel("Select a device to view details")
        self.device_details_info.setWordWrap(True)
        details_layout.addWidget(self.device_details_info)

        # Whitelist actions
        self.btn_add_whitelist = QPushButton("+ Add to Whitelist")
        self.btn_add_whitelist.setObjectName("btnSecondary")
        self.btn_add_whitelist.clicked.connect(self._add_selected_to_whitelist)
        self.btn_add_whitelist.setEnabled(False)
        details_layout.addWidget(self.btn_add_whitelist)

        self.btn_remove_whitelist = QPushButton("- Remove from Whitelist")
        self.btn_remove_whitelist.setObjectName("btnSecondary")
        self.btn_remove_whitelist.clicked.connect(self._remove_selected_from_whitelist)
        self.btn_remove_whitelist.setEnabled(False)
        details_layout.addWidget(self.btn_remove_whitelist)

        details_layout.addStretch()

        devices_page_layout.addWidget(details_col, 2)

        self.pages.addWidget(devices_page)

        # Page 2: Settings (show summary + open dialog)
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setContentsMargins(8, 8, 8, 8)
        settings_layout.setSpacing(8)

        # Inline settings widget
        self.settings_widget = SettingsWidget(self.config_manager)
        self.settings_widget.settings_changed.connect(self._on_settings_changed)
        self.settings_widget.hotkey_changed.connect(self._on_hotkey_changed)
        settings_layout.addWidget(self.settings_widget)

        self.pages.addWidget(settings_page)

        # Page 3: Analytics (Phase 6)
        analytics_page = QWidget()
        analytics_layout = QVBoxLayout(analytics_page)
        analytics_layout.setContentsMargins(8, 8, 8, 8)
        self.analytics_panel = AnalyticsPanel()
        analytics_layout.addWidget(self.analytics_panel)
        self.pages.addWidget(analytics_page)

        # Page 4: Help & Documentation (Phase 5)
        help_page = QWidget()
        help_layout = QVBoxLayout(help_page)
        help_layout.setContentsMargins(8, 8, 8, 8)
        self.help_panel = HelpPanel()
        help_layout.addWidget(self.help_panel)
        self.pages.addWidget(help_page)

        # Page 5: Diagnostics (Phase 5-6)
        diagnostics_page = QWidget()
        diagnostics_layout = QVBoxLayout(diagnostics_page)
        diagnostics_layout.setContentsMargins(8, 8, 8, 8)
        diagnostics_layout.setSpacing(8)
        
        # Create tabbed diagnostics interface
        from PyQt6.QtWidgets import QTabWidget
        diagnostics_tabs = QTabWidget()
        
        # Dependency viewer
        self.dependency_viewer = DependencyViewer()
        diagnostics_tabs.addTab(self.dependency_viewer, "Dependencies")
        
        # Performance profiler
        self.profiling_viewer = ProfilingViewer()
        diagnostics_tabs.addTab(self.profiling_viewer, "Performance")
        
        diagnostics_layout.addWidget(diagnostics_tabs)
        self.pages.addWidget(diagnostics_page)

        root_layout.addWidget(pages_container, 1)

        # Initialize hotkey label and device list
        self._update_hotkey_label()
        self._refresh_device_list()

        # Start on the Status page by default
        try:
            self._switch_to_page(0)
            self.btn_nav_status.setChecked(True)
        except Exception:
            pass

    def _show_dashboard(self):
        """Show the modern analytics dashboard window."""
        if self.dashboard_window is None:
            self.dashboard_window = DashboardWindow(
                self.device_manager,
                self.input_blocker,
                self.config_manager,
                self,
            )

        self.dashboard_window.show()
        self.dashboard_window.raise_()
        self.dashboard_window.activateWindow()
    
    def _create_status_page(self) -> QWidget:
        """Create the enhanced status page with app info and statistics."""
        from PyQt6.QtWidgets import QScrollArea, QGridLayout, QSizePolicy
        import platform
        import datetime
        import os
        import subprocess
        
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # ═══════════════════════════════════════════════════════════════
        # TOP SECTION: System Info (neofetch style)
        # ═══════════════════════════════════════════════════════════════
        top_section = QWidget()
        top_section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        
        # System Info Card (neofetch style) - full width
        sys_info_card = self._create_system_info_card()
        sys_info_card.setMinimumWidth(280)
        sys_info_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_layout.addWidget(sys_info_card)
        
        # Session Stats Card
        session_card = self._create_session_stats_card()
        session_card.setMinimumWidth(280)
        session_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_layout.addWidget(session_card)
        
        layout.addWidget(top_section)
        
        # ═══════════════════════════════════════════════════════════════
        # MIDDLE SECTION: Security + Status + Unlockable (unified row)
        # ═══════════════════════════════════════════════════════════════
        center_section = QWidget()
        center_section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        center_layout = QHBoxLayout(center_section)
        center_layout.setContentsMargins(0, 16, 0, 16)
        center_layout.setSpacing(0)  # No spacing - cards will be joined
        
        # Feature card left - Security First (expands to fill)
        security_card = self._create_feature_card(
            "🛡️", "Security First",
            "Block keyboard and mouse input with low-level evdev control.",
            "#6366f1"
        )
        security_card.setMinimumWidth(180)
        security_card.setMinimumHeight(200)
        security_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        security_card.setStyleSheet(security_card.styleSheet() + """
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
        """)
        center_layout.addWidget(security_card, 1)
        
        # CENTER: Main Status Card (the main focus - slightly larger)
        self.status_frame = self._create_status_frame()
        self.status_frame.setMinimumWidth(280)
        self.status_frame.setMinimumHeight(200)
        self.status_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status_frame.setStyleSheet(self.status_frame.styleSheet() + """
            border-radius: 0px;
            border-left: 1px solid rgba(255,255,255,0.1);
            border-right: 1px solid rgba(255,255,255,0.1);
        """)
        center_layout.addWidget(self.status_frame, 2)  # Stretch factor 2 = larger
        
        # Feature card right - Always Unlockable (expands to fill)
        safety_card = self._create_feature_card(
            "🔐", "Always Unlockable",
            "Multiple unlock methods: hotkey, pattern, or touchscreen.",
            "#a855f7"
        )
        safety_card.setMinimumWidth(180)
        safety_card.setMinimumHeight(200)
        safety_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        safety_card.setStyleSheet(safety_card.styleSheet() + """
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
        """)
        center_layout.addWidget(safety_card, 1)
        
        layout.addWidget(center_section, 1)  # Give it stretch priority
        
        # ═══════════════════════════════════════════════════════════════
        # BOTTOM ROW: About + Tech Stack + Quick Actions
        # ═══════════════════════════════════════════════════════════════
        bottom_section = QWidget()
        bottom_section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bottom_layout = QHBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(12)
        
        # About Card
        about_card = self._create_about_card()
        about_card.setMinimumWidth(220)
        about_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bottom_layout.addWidget(about_card, 1)
        
        # Tech Stack Card
        tech_card = self._create_tech_stack_card()
        tech_card.setMinimumWidth(200)
        tech_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bottom_layout.addWidget(tech_card, 1)
        
        # Quick Actions Card
        actions_card = self._create_quick_actions_card()
        actions_card.setMinimumWidth(180)
        actions_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bottom_layout.addWidget(actions_card, 1)
        
        layout.addWidget(bottom_section)
        
        # ═══════════════════════════════════════════════════════════════
        # FIFTH ROW: Tips & Shortcuts
        # ═══════════════════════════════════════════════════════════════
        tips_card = self._create_tips_card()
        tips_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(tips_card)
        
        # Flexible stretch
        layout.addStretch(1)
        
        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        
        # Hidden label for hotkey (used by other parts of the app)
        self.hotkey_label = QLabel()
        self.hotkey_label.setVisible(False)
        
        return page
    
    def _create_system_info_card(self) -> QFrame:
        """Create a neofetch-style system info card."""
        import platform
        import os
        import subprocess
        from PyQt6.QtWidgets import QGridLayout
        
        card = QFrame()
        card.setObjectName("statusFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        title = QLabel("🖥️ System Information")
        title.setObjectName("lblTitle")
        layout.addWidget(title)
        
        # Get system info
        def get_cmd_output(cmd):
            try:
                return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
            except:
                return "N/A"
        
        # Gather system data
        hostname = platform.node() or "localhost"
        username = os.environ.get('SUDO_USER', os.environ.get('USER', 'root'))
        distro = get_cmd_output("lsb_release -d 2>/dev/null | cut -f2") or platform.system()
        kernel = platform.release()
        arch = platform.machine()
        
        # CPU info
        cpu = get_cmd_output("grep 'model name' /proc/cpuinfo | head -1 | cut -d':' -f2")
        if not cpu or cpu == "N/A":
            cpu = platform.processor() or "Unknown CPU"
        cpu = cpu.strip()[:35] + "..." if len(cpu.strip()) > 35 else cpu.strip()
        
        # Memory info
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            total = int([l for l in meminfo.split('\n') if 'MemTotal' in l][0].split()[1]) // 1024
            available = int([l for l in meminfo.split('\n') if 'MemAvailable' in l][0].split()[1]) // 1024
            used = total - available
            mem_str = f"{used}MB / {total}MB ({100*used//total}%)"
        except:
            mem_str = "N/A"
        
        # Uptime
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime_str = f"{hours}h {minutes}m"
        except:
            uptime_str = "N/A"
        
        # Desktop environment
        de = os.environ.get('XDG_CURRENT_DESKTOP', os.environ.get('DESKTOP_SESSION', 'Unknown'))
        
        # Shell
        shell = os.path.basename(os.environ.get('SHELL', '/bin/bash'))
        
        # Create info grid
        info_grid = QGridLayout()
        info_grid.setSpacing(4)
        
        info_items = [
            ("👤", f"{username}@{hostname}"),
            ("🐧", distro[:30]),
            ("⚙️", f"Kernel {kernel}"),
            ("💻", f"{arch} architecture"),
            ("🧠", cpu),
            ("💾", mem_str),
            ("⏱️", f"Uptime: {uptime_str}"),
            ("🖼️", de),
            ("📟", shell),
        ]
        
        for i, (icon, text) in enumerate(info_items):
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 12px;")
            text_label = QLabel(text)
            text_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px; font-family: monospace;")
            text_label.setWordWrap(True)
            info_grid.addWidget(icon_label, i, 0)
            info_grid.addWidget(text_label, i, 1)
        
        layout.addLayout(info_grid)
        layout.addStretch()
        
        try:
            ShadowEffect.apply_shadow(card, blur_radius=24, offset=4)
        except Exception:
            pass
        
        return card
    
    def _create_session_stats_card(self) -> QFrame:
        """Create session statistics card."""
        import datetime
        
        card = QFrame()
        card.setObjectName("statusFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        title = QLabel("📊 Session")
        title.setObjectName("lblTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addStretch(1)
        
        self.session_start = datetime.datetime.now()
        self.session_stats_label = QLabel()
        self.session_stats_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px;")
        self.session_stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_session_stats()
        layout.addWidget(self.session_stats_label)
        
        layout.addStretch(1)
        
        # Timer to update session stats
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_session_stats)
        self.stats_timer.start(30000)  # Update every 30 seconds
        
        try:
            ShadowEffect.apply_shadow(card, blur_radius=16, offset=2)
        except Exception:
            pass
        
        return card
    
    def _create_about_card(self) -> QFrame:
        """Create about card."""
        card = QFrame()
        card.setObjectName("statusFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        
        title = QLabel("📋 About")
        title.setObjectName("lblTitle")
        layout.addWidget(title)
        
        version = QLabel("Input Locker v2.0.0")
        version.setStyleSheet("color: #a78bfa; font-weight: bold; font-size: 12px;")
        layout.addWidget(version)
        
        desc = QLabel("Professional-grade input device management for Linux systems.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px;")
        layout.addWidget(desc)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.1);")
        layout.addWidget(sep)
        
        dev_info = QLabel("👨‍💻 Input Locker Team\n© 2024-2025")
        dev_info.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px;")
        layout.addWidget(dev_info)
        
        layout.addStretch()
        
        try:
            ShadowEffect.apply_shadow(card, blur_radius=16, offset=2)
        except Exception:
            pass
        
        return card
    
    def _create_tech_stack_card(self) -> QFrame:
        """Create tech stack card."""
        from PyQt6.QtWidgets import QGridLayout
        
        card = QFrame()
        card.setObjectName("statusFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        title = QLabel("🔧 Tech Stack")
        title.setObjectName("lblTitle")
        layout.addWidget(title)
        
        tech_grid = QGridLayout()
        tech_grid.setSpacing(6)
        
        techs = [
            ("Python", "#3776ab"),
            ("PyQt6", "#41cd52"),
            ("evdev", "#ff6b6b"),
            ("Linux", "#fcc624"),
            ("Qt", "#41cd52"),
            ("uinput", "#f97316"),
        ]
        
        for i, (name, color) in enumerate(techs):
            badge = QLabel(name)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"""
                background-color: {color}20;
                color: {color};
                border: 1px solid {color}40;
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: bold;
            """)
            tech_grid.addWidget(badge, i // 2, i % 2)
        
        layout.addLayout(tech_grid)
        layout.addStretch()
        
        try:
            ShadowEffect.apply_shadow(card, blur_radius=16, offset=2)
        except Exception:
            pass
        
        return card
    
    def _create_quick_actions_card(self) -> QFrame:
        """Create quick actions card."""
        card = QFrame()
        card.setObjectName("statusFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        title = QLabel("⚡ Quick Actions")
        title.setObjectName("lblTitle")
        layout.addWidget(title)
        
        # Refresh button
        btn_refresh = QPushButton("🔄 Refresh Devices")
        btn_refresh.setObjectName("btnSecondary")
        btn_refresh.clicked.connect(self._refresh_devices)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(btn_refresh)
        
        # Settings button
        btn_settings = QPushButton("⚙️ Settings")
        btn_settings.setObjectName("btnSecondary")
        btn_settings.clicked.connect(self._show_settings)
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(btn_settings)
        
        # Logs button
        btn_logs = QPushButton("📋 View Logs")
        btn_logs.setObjectName("btnSecondary")
        btn_logs.clicked.connect(self._show_logs)
        btn_logs.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(btn_logs)
        
        layout.addStretch()
        
        try:
            ShadowEffect.apply_shadow(card, blur_radius=16, offset=2)
        except Exception:
            pass
        
        return card
    
    def _create_tips_card(self) -> QFrame:
        """Create tips and shortcuts card."""
        card = QFrame()
        card.setObjectName("statusFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        title = QLabel("💡 Tips & Info")
        title.setObjectName("lblTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addStretch(1)
        
        tips_layout = QHBoxLayout()
        tips_layout.setSpacing(24)
        
        tips = [
            ("🔒", "Lock Protection", "Blocks all input except unlock methods"),
            ("🖱️", "Mouse Blocking", "Full grab prevents all mouse input"),
            ("⌨️", "Keyboard Filter", "Allows only hotkey combinations"),
            ("📱", "Touchscreen", "Always accessible for emergency unlock"),
            ("⚡", "Quick Toggle", "Use tray icon for fast access"),
        ]
        
        # Add stretch before tips to center them
        tips_layout.addStretch(1)
        
        for i, (icon, title_text, desc) in enumerate(tips):
            tip_widget = QWidget()
            tip_layout = QVBoxLayout(tip_widget)
            tip_layout.setContentsMargins(0, 0, 0, 0)
            tip_layout.setSpacing(2)
            
            header = QLabel(f"{icon} {title_text}")
            header.setStyleSheet("color: #c4b5fd; font-size: 11px; font-weight: bold;")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tip_layout.addWidget(header)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 10px;")
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tip_layout.addWidget(desc_label)
            
            tips_layout.addWidget(tip_widget)
        
        # Add stretch after tips to center them
        tips_layout.addStretch(1)
        layout.addLayout(tips_layout)
        
        layout.addStretch(1)
        
        try:
            ShadowEffect.apply_shadow(card, blur_radius=16, offset=2)
        except Exception:
            pass
        
        return card

    def _create_feature_card(self, icon: str, title: str, description: str, color: str) -> QFrame:
        """Create a feature highlight card."""
        card = QFrame()
        card.setObjectName("statusFrame")
        card.setMinimumHeight(140)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 28))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px;")
        layout.addWidget(desc_label)
        
        try:
            ShadowEffect.apply_shadow(card, blur_radius=16, offset=2)
        except Exception:
            pass
        
        return card
    
    def _update_session_stats(self):
        """Update session statistics."""
        import datetime
        try:
            now = datetime.datetime.now()
            uptime = now - self.session_start
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            lock_count = getattr(self, '_lock_count', 0)
            unlock_count = getattr(self, '_unlock_count', 0)
            
            self.session_stats_label.setText(
                f"⏱️ Session Time: {hours}h {minutes}m\n"
                f"🔒 Lock Events: {lock_count}\n"
                f"🔓 Unlock Events: {unlock_count}\n"
                f"📅 Started: {self.session_start.strftime('%H:%M')}"
            )
        except Exception:
            pass

    def _create_header(self) -> QWidget:
        """Create the application header."""
        header = QWidget()
        layout = QVBoxLayout(header)
        
        # Top row: title and theme toggle
        top_row = QHBoxLayout()
        
        title = QLabel("🔒 Input Locker")
        title.setObjectName("lblTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_row.addWidget(title, 1)
        
        # Theme toggle button
        self.btn_theme_toggle = QPushButton("🌙")
        self.btn_theme_toggle.setObjectName("btnSecondary")
        self.btn_theme_toggle.setMaximumWidth(50)
        self.btn_theme_toggle.setToolTip("Toggle theme (Light/Dark)")
        self.btn_theme_toggle.clicked.connect(self._toggle_theme)
        # Set initial icon based on current theme
        try:
            current_theme = self.config_manager.get_theme()
            self.btn_theme_toggle.setText("☀️" if current_theme == "dark" else "🌙")
        except Exception:
            pass
        top_row.addWidget(self.btn_theme_toggle, 0)
        
        layout.addLayout(top_row)
        
        subtitle = QLabel("Input Devices Control")
        subtitle.setObjectName("lblSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        return header
    
    def _create_status_frame(self) -> QFrame:
        """Create the current status frame."""
        frame = QFrame()
        frame.setObjectName("statusFrame")
        frame.setMinimumHeight(200)
        
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Status label
        status_label = QLabel("CURRENT STATUS")
        status_label.setObjectName("lblSubtitle")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        # Icono de estado grande
        self.status_icon = QLabel("🔓")
        self.status_icon.setFont(QFont("Segoe UI Emoji", 48))
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_icon)
        
        # Status text
        self.status_text = QLabel("UNLOCKED")
        self.status_text.setObjectName("lblStatus")
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_text)
        
        # Main action button
        self.btn_main_action = QPushButton("🔒 LOCK NOW")
        self.btn_main_action.setObjectName("btnMainAction")
        self.btn_main_action.clicked.connect(self._toggle_lock)
        layout.addWidget(self.btn_main_action)
        
        # Apply a subtle shadow for a modern, elevated look
        try:
            ShadowEffect.apply_shadow(frame, blur_radius=24, offset=4)
        except Exception:
            pass
        
        return frame
    
    def _setup_tray(self):
        """Configura el icono de bandeja del sistema."""
        self.tray_icon = TrayIcon(self)
        
        # Conectar señales
        self.tray_icon.toggle_lock_requested.connect(self._toggle_lock)
        self.tray_icon.show_window_requested.connect(self.show)
        self.tray_icon.settings_requested.connect(self._show_settings)
        self.tray_icon.logs_requested.connect(self._show_logs)
        self.tray_icon.refresh_requested.connect(self._refresh_devices)
        self.tray_icon.quit_requested.connect(self._quit_application)
        
        # Mostrar icono
        self.tray_icon.show()
        
        logger.info("Tray icon configured")
    
    def _apply_theme(self):
        """Apply the configured theme."""
        theme = self.config_manager.get_theme()

        # Attempt to register bundled fonts (if present)
        try:
            from pathlib import Path
            fonts_dir = Path(__file__).parent / 'resources' / 'fonts'
            if fonts_dir.exists() and fonts_dir.is_dir():
                for font_path in fonts_dir.glob("*.ttf"):
                    QFontDatabase.addApplicationFont(str(font_path))
        except Exception:
            pass

        # Cargar stylesheet principal + dashboard
        style_file = self._get_style_file()

        try:
            with open(style_file, 'r', encoding='utf-8') as f:
                stylesheet = f.read()

            # Append dashboard-specific styles if available
            try:
                from pathlib import Path
                dashboard_qss = Path(__file__).parent / 'resources' / 'styles_dashboard_dark.qss'
                if dashboard_qss.exists():
                    with open(dashboard_qss, 'r', encoding='utf-8') as df:
                        stylesheet += "\n\n" + df.read()
            except Exception:
                pass
            
            self.setStyleSheet(stylesheet)
            # Apply basic palette differences for light/dark and a
            # modern, unified application font.
            app = QApplication.instance()
            if app is not None:
                # Choose the best available family for a premium look
                try:
                    families = QFontDatabase().families()
                    preferred = [
                        "Poppins",
                        "Montserrat",
                        "Segoe UI",
                        "SF Pro Text",
                        "Ubuntu",
                        "Roboto",
                    ]
                    chosen = None
                    for fam in preferred:
                        if fam in families:
                            chosen = fam
                            break
                    if chosen is not None:
                        app.setFont(QFont(chosen, 10))
                except Exception:
                    pass

                palette = QPalette()
                if theme == "light":
                    palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
                    palette.setColor(QPalette.ColorRole.WindowText, QColor(20, 20, 20))
                    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
                    palette.setColor(QPalette.ColorRole.Text, QColor(20, 20, 20))
                else:
                    # Dark theme
                    palette.setColor(QPalette.ColorRole.Window, QColor(18, 18, 18))
                    palette.setColor(QPalette.ColorRole.WindowText, QColor(230, 230, 230))
                    palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
                    palette.setColor(QPalette.ColorRole.Text, QColor(230, 230, 230))
                app.setPalette(palette)

            # Update theme toggle button icon
            if hasattr(self, 'btn_theme_toggle'):
                self.btn_theme_toggle.setText("☀️" if theme == "dark" else "🌙")

            logger.info(f"Theme applied: {theme}")
            
        except Exception as e:
            logger.error(f"Error applying theme: {e}")
    
    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        try:
            current_theme = self.config_manager.get_theme()
            new_theme = "light" if current_theme == "dark" else "dark"
            
            self.config_manager.set_theme(new_theme)
            self._apply_theme()
            
            # Update theme toggle button
            if hasattr(self, 'btn_theme_toggle'):
                self.btn_theme_toggle.setText("☀️" if new_theme == "dark" else "🌙")
            
            logger.info(f"Theme switched to: {new_theme}")
        except Exception as e:
            logger.error(f"Error toggling theme: {e}")

    def _switch_to_page(self, index: int):
        """Switch the central stacked pages to the given index."""
        try:
            if hasattr(self, 'pages'):
                # Use a smooth fade transition between pages
                try:
                    fade_transition(self.pages, index)
                except Exception:
                    self.pages.setCurrentIndex(index)
                # Update nav button checked state
                try:
                    self.btn_nav_status.setChecked(index == 0)
                    self.btn_nav_devices.setChecked(index == 1)
                    self.btn_nav_settings.setChecked(index == 2)
                    self.btn_nav_analytics.setChecked(index == 3)
                    self.btn_nav_help.setChecked(index == 4)
                    self.btn_nav_diagnostics.setChecked(index == 5)
                    # logs opens dialog, do not set checked for logs
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error switching page: {e}")

    def _toggle_sidebar(self):
        """Animate collapse/expand of the sidebar."""
        try:
            target = 64 if self._sidebar_expanded else 260
            start = self.sidebar.width() if self._sidebar_expanded else self.sidebar.maximumWidth()
            anim = QPropertyAnimation(self.sidebar, b"maximumWidth")
            anim.setDuration(260)
            anim.setStartValue(start)
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.start()
            self._sidebar_anim = anim
            # toggle state
            self._sidebar_expanded = not self._sidebar_expanded
            # update button glyph
            try:
                self.btn_collapse.setText("⯈" if not self._sidebar_expanded else "⯇")
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error toggling sidebar: {e}")

    def _get_style_file(self):
        """Return the stylesheet file path."""
        from pathlib import Path
        
        base_dir = Path(__file__).parent / 'resources'
        theme = self.config_manager.get_theme() if hasattr(self, 'config_manager') else 'dark'

        # Explicitly map light to the new light stylesheet, and
        # use the original styles.qss for the dark/default theme.
        if theme == 'light':
            light_file = base_dir / 'styles_light.qss'
            if light_file.exists():
                return light_file

        # Fallback and default: dark/original theme
        return base_dir / 'styles.qss'
    
    def _update_ui_state(self):
        """Update the visual state of the UI."""
        is_locked = self.input_blocker.is_locked
        
        # Initialize counters if not exist
        if not hasattr(self, '_lock_count'):
            self._lock_count = 0
        if not hasattr(self, '_unlock_count'):
            self._unlock_count = 0
        if not hasattr(self, '_last_lock_state'):
            self._last_lock_state = None
        
        # Track lock/unlock events
        if self._last_lock_state is not None and self._last_lock_state != is_locked:
            if is_locked:
                self._lock_count += 1
            else:
                self._unlock_count += 1
            # Update session stats if available
            if hasattr(self, 'session_stats_label'):
                self._update_session_stats()
        
        self._last_lock_state = is_locked
        
        # Update icon and text
        if is_locked:
            self.status_icon.setText("🔒")
            self.status_text.setText("LOCKED")
            self.status_text.setObjectName("lblStatusLocked")
            self.btn_main_action.setText("🔓 UNLOCK")
            self.btn_main_action.setObjectName("btnUnlock")
        else:
            self.status_icon.setText("🔓")
            self.status_text.setText("UNLOCKED")
            self.status_text.setObjectName("lblStatusUnlocked")
            self.btn_main_action.setText("🔒 LOCK NOW")
            self.btn_main_action.setObjectName("btnLock")
        
        # Re-apply styles
        self.status_text.style().unpolish(self.status_text)
        self.status_text.style().polish(self.status_text)
        self.btn_main_action.style().unpolish(self.btn_main_action)
        self.btn_main_action.style().polish(self.btn_main_action)
        
        # Actualizar tray icon
        if self.tray_icon:
            self.tray_icon.update_status(is_locked)
        
        # Update device list
        self._refresh_device_list()
        
        # Update device stats if available
        if hasattr(self, 'device_stats_label'):
            self._update_device_stats()
        
        # Emitir señal
        self.lock_state_changed.emit(is_locked)
        
        logger.debug(f"UI updated: {'Locked' if is_locked else 'Unlocked'}")
    
    def _refresh_device_list(self):
        """Refresca la lista de dispositivos en la UI."""
        devices = self.device_manager.get_all_devices()
        blocked_devices = set(self.input_blocker.get_blocked_devices())
        
        self.device_list.update_devices(devices, blocked_devices)
    
    def _update_hotkey_label(self):
        """Update the hotkey label with current configuration and profile."""
        try:
            hotkey = self.config_manager.get_hotkey()
            
            # Get active hotkey profile if available
            profile_info = ""
            try:
                if hasattr(self, 'hotkey_manager'):
                    active_profile = self.hotkey_manager.get_active_profile()
                    profile_info = f" [{active_profile}]"
            except Exception:
                pass
            
            self.hotkey_label.setText(f"Configured shortcut: {hotkey}{profile_info}")
        except Exception as e:
            logger.warning(f"Error updating hotkey label: {e}")

    def _filter_devices(self):
        """Filter device list based on search text and type filter."""
        all_devices = self.device_manager.get_all_devices()
        text = self.device_search.text().strip().lower() if hasattr(self, 'device_search') else ''
        type_idx = self.device_type_filter.currentIndex() if hasattr(self, 'device_type_filter') else 0

        def matches(dev: 'InputDeviceInfo'):
            if text:
                if text not in dev.name.lower() and text not in dev.path.lower():
                    return False
            if type_idx == 0:
                return True
            mapping = {
                1: 'keyboard',
                2: 'mouse',
                3: 'touchscreen',
                4: 'touchpad',
                5: 'unknown'
            }
            expected = mapping.get(type_idx, None)
            return dev.device_type.value == expected

        filtered = [d for d in all_devices if matches(d)]
        blocked = set(self.input_blocker.get_blocked_devices())
        self.device_list.update_devices(filtered, blocked)

    def _show_undo(self, message: str, timeout: int = 8000):
        """Show the transient undo bar with the given message for `timeout` ms."""
        try:
            self.undo_label.setText(message)

            # Animated show: animate maximumHeight from 0 to target
            try:
                self.undo_bar.setMaximumHeight(0)
                self.undo_bar.show()
                anim = QPropertyAnimation(self.undo_bar, b"maximumHeight")
                anim.setDuration(220)
                anim.setStartValue(0)
                anim.setEndValue(56)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.start()
                # keep reference to avoid GC
                self._undo_anim = anim
                # Fade in
                try:
                    effect = QGraphicsOpacityEffect(self.undo_bar)
                    self.undo_bar.setGraphicsEffect(effect)
                    fade = QPropertyAnimation(effect, b"opacity")
                    fade.setDuration(220)
                    fade.setStartValue(0.0)
                    fade.setEndValue(1.0)
                    fade.start()
                    self._undo_fade = fade
                except Exception:
                    pass
            except Exception:
                self.undo_bar.show()

            # Cancel any existing hide timer and start a new one
            try:
                self._undo_timer.stop()
            except Exception:
                pass

            self._undo_timer = QTimer()
            self._undo_timer.setSingleShot(True)
            self._undo_timer.timeout.connect(self._hide_undo)
            self._undo_timer.start(timeout)
        except Exception as e:
            logger.error(f"Error showing undo bar: {e}")

    def _hide_undo(self):
        try:
            # Animate hide then clear
            try:
                anim = QPropertyAnimation(self.undo_bar, b"maximumHeight")
                anim.setDuration(180)
                anim.setStartValue(self.undo_bar.maximumHeight() or 56)
                anim.setEndValue(0)
                anim.setEasingCurve(QEasingCurve.Type.InCubic)

                def _on_finished():
                    try:
                        self.undo_bar.hide()
                    except:
                        pass
                    self._clear_last_action()

                anim.finished.connect(_on_finished)
                anim.start()
                self._undo_anim = anim
                try:
                    effect = self.undo_bar.graphicsEffect()
                    if effect is None:
                        effect = QGraphicsOpacityEffect(self.undo_bar)
                        self.undo_bar.setGraphicsEffect(effect)
                    fade = QPropertyAnimation(effect, b"opacity")
                    fade.setDuration(160)
                    fade.setStartValue(1.0)
                    fade.setEndValue(0.0)
                    fade.start()
                    self._undo_fade = fade
                except Exception:
                    pass
            except Exception:
                self.undo_bar.hide()
                self._clear_last_action()
        except Exception as e:
            logger.error(f"Error hiding undo bar: {e}")

    def _perform_undo(self):
        """Perform undo for the last recorded bulk action."""
        if not self._last_bulk_action:
            return

        action = self._last_bulk_action.get('type')
        paths = list(self._last_bulk_action.get('paths', []))

        try:
            if action == 'block':
                # Undo blocking -> unblock any currently blocked in paths
                for p in paths:
                    if p in self.input_blocker.get_blocked_devices():
                        try:
                            self.input_blocker.toggle_device(p)
                        except Exception as e:
                            logger.error(f"Error undo-unblocking {p}: {e}")

            elif action == 'unblock':
                # Undo unblocking -> block any currently unblocked in paths
                for p in paths:
                    if p not in self.input_blocker.get_blocked_devices():
                        try:
                            self.input_blocker.toggle_device(p)
                        except Exception as e:
                            logger.error(f"Error undo-blocking {p}: {e}")

            # Refresh UI
            self._update_ui_state()
        finally:
            self._hide_undo()

    def _show_confirm(self, action_type: str, paths: list):
        """Show inline confirm bar for bulk action (non-modal).

        action_type: 'block' or 'unblock'
        paths: list of device paths
        """
        if not paths:
            return

        self._pending_confirm = {'type': action_type, 'paths': paths}
        verb = 'block' if action_type == 'block' else 'unblock'
        self.confirm_label.setText(f"Confirm: {verb} {len(paths)} device(s)?")

        # Animate show similar to undo
        try:
            self.confirm_bar.setMaximumHeight(0)
            self.confirm_bar.show()
            anim = QPropertyAnimation(self.confirm_bar, b"maximumHeight")
            anim.setDuration(200)
            anim.setStartValue(0)
            anim.setEndValue(56)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.start()
            self._confirm_anim = anim
        except Exception:
            self.confirm_bar.show()
        # Fade in confirm bar
        try:
            effect = QGraphicsOpacityEffect(self.confirm_bar)
            self.confirm_bar.setGraphicsEffect(effect)
            fade = QPropertyAnimation(effect, b"opacity")
            fade.setDuration(200)
            fade.setStartValue(0.0)
            fade.setEndValue(1.0)
            fade.start()
            self._confirm_fade = fade
        except Exception:
            pass

    def _confirm_action(self):
        """User confirmed inline action; execute and show undo."""
        pending = getattr(self, '_pending_confirm', None)
        if not pending:
            return

        action = pending['type']
        paths = pending['paths']

        try:
            if action == 'block':
                for p in paths:
                    if p not in self.input_blocker.get_blocked_devices():
                        try:
                            self.input_blocker.toggle_device(p)
                        except Exception as e:
                            logger.error(f"Error blocking device {p}: {e}")

            else:
                for p in paths:
                    if p in self.input_blocker.get_blocked_devices():
                        try:
                            self.input_blocker.toggle_device(p)
                        except Exception as e:
                            logger.error(f"Error unblocking device {p}: {e}")

            self._update_ui_state()

            # record last action for undo
            self._last_bulk_action = {'type': action, 'paths': paths}
            self._show_undo(f"{action.capitalize()}ed {len(paths)} device(s)")

        finally:
            # hide confirm bar
            try:
                anim = QPropertyAnimation(self.confirm_bar, b"maximumHeight")
                anim.setDuration(160)
                anim.setStartValue(self.confirm_bar.maximumHeight() or 56)
                anim.setEndValue(0)

                def _on_finished():
                    try:
                        self.confirm_bar.hide()
                    except:
                        pass

                anim.finished.connect(_on_finished)
                anim.start()
                self._confirm_anim = anim
            except Exception:
                self.confirm_bar.hide()
            self._pending_confirm = None

    def _cancel_action(self):
        """Cancel a pending inline confirm action."""
        self._pending_confirm = None
        try:
            anim = QPropertyAnimation(self.confirm_bar, b"maximumHeight")
            anim.setDuration(160)
            anim.setStartValue(self.confirm_bar.maximumHeight() or 56)
            anim.setEndValue(0)

            def _on_finished():
                try:
                    self.confirm_bar.hide()
                except:
                    pass

            anim.finished.connect(_on_finished)
            anim.start()
            self._confirm_anim = anim
        except Exception:
            self.confirm_bar.hide()

    def _clear_last_action(self):
        self._last_bulk_action = None

    def _block_selected(self):
        """Block the currently selected devices (bulk)."""
        paths = self.device_list.get_selected_device_paths()
        if not paths:
            QMessageBox.information(self, "No Selection", "No devices selected.")
            return

        # Show inline confirmation bar for bulk block
        self._show_confirm('block', paths)

        # Record last bulk action for possible undo
        self._last_bulk_action = {'type': 'block', 'paths': paths}
        self._show_undo(f"Blocked {len(paths)} device(s)")

    def _unblock_selected(self):
        """Unblock the currently selected devices (bulk)."""
        paths = self.device_list.get_selected_device_paths()
        if not paths:
            QMessageBox.information(self, "No Selection", "No devices selected.")
            return

        # Show inline confirmation bar for bulk unblock
        self._show_confirm('unblock', paths)

        # Record last bulk action for possible undo
        self._last_bulk_action = {'type': 'unblock', 'paths': paths}
        self._show_undo(f"Unblocked {len(paths)} device(s)")
    
    def _toggle_lock(self):
        """Toggle between lock and unlock."""
        logger.info("Toggle lock requested from UI")
        
        try:
            self.input_blocker.toggle_lock()
            self._update_ui_state()
            
            # Record event to analytics
            try:
                if hasattr(self, 'analytics_panel'):
                    event_type = "lock" if self.input_blocker.is_locked else "unlock"
                    device_count = self.input_blocker.get_blocked_count()
                    self.analytics_panel.record_event(
                        event_type,
                        {"device_count": device_count, "source": "ui"}
                    )
            except Exception as e:
                logger.warning(f"Could not record analytics event: {e}")
            
            # Mostrar notificación
            if self.config_manager.get('general', 'show_notifications', True):
                if self.input_blocker.is_locked:
                    self._show_notification(
                        "Devices Locked",
                        f"{self.input_blocker.get_blocked_count()} device(s) locked"
                    )
                else:
                    self._show_notification(
                        "Devices Unlocked",
                        "All devices are available"
                    )
        
        except Exception as e:
            logger.error(f"Error toggling lock: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error changing lock state:\n{str(e)}"
            )
    
    def _show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self.config_manager, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.hotkey_changed.connect(self._on_hotkey_changed)
        dialog.exec()
    
    def _show_logs(self):
        """Show the log viewer."""
        dialog = LogViewer(self)
        dialog.exec()
    
    def _show_help(self):
        """Show the help dialog."""
        help_text = """
        <h2>Input Locker - Help</h2>
        
        <h3>What does this application do?</h3>
        <p>Input Locker selectively blocks physical keyboards and mice while
        allowing the use of touchscreens.</p>
        
        <h3>Basic usage:</h3>
        <ul>
            <li><b>Lock/Unlock:</b> Use the main button or the keyboard shortcut</li>
            <li><b>Keyboard shortcut:</b> Default Ctrl+Alt+L (configurable)</li>
            <li><b>Device list:</b> Shows all detected input devices</li>
            <li><b>System tray:</b> Left click to toggle lock</li>
        </ul>
        
        <h3>Configuration:</h3>
        <ul>
            <li><b>Settings:</b> Hotkey, startup options, notifications</li>
            <li><b>Devices:</b> What to block, whitelist</li>
            <li><b>Appearance:</b> Light/dark theme</li>
        </ul>
        
        <h3>Permissions:</h3>
        <p>This application requires root permissions to access
        input devices under /dev/input/</p>
        
        <h3>Troubleshooting:</h3>
        <ul>
            <li>If the hotkey doesn't work, check that it's not used by another app</li>
            <li>If devices are not detected, verify root permissions</li>
            <li>Check the logs for more information about errors</li>
        </ul>
        
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Support:</b> github.com/usuario/input-locker</p>
        """
        
        QMessageBox.about(self, "Help - Input Locker", help_text)
    
    def _refresh_devices(self):
        """Refresh device detection."""
        logger.info("Refreshing devices...")
        
        try:
            self.device_manager.refresh()
            self._refresh_device_list()
            
            summary = self.device_manager.get_summary()
            
            QMessageBox.information(
                self,
                "Devices Updated",
                f"Detected:\n"
                f"• Keyboards: {summary['keyboards']}\n"
                f"• Mice: {summary['mice']}\n"
                f"• Touchscreens: {summary['touchscreens']}\n"
                f"• Total: {summary['total']}"
            )
            
        except Exception as e:
            logger.error(f"Error refreshing devices: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error refreshing devices:\n{str(e)}"
            )
    
    def _on_device_selected(self, device_path: str):
        """Callback when a device is selected."""
        device_info = self.device_manager.get_device_by_path(device_path)
        
        if not device_info:
            return
        
        # Show options
        is_in_whitelist = device_path in self.config_manager.get_whitelist()
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Device Options")
        msg.setText(f"{device_info.icon} {device_info.name}")
        msg.setInformativeText(
            f"Tipo: {device_info.device_type.value}\n"
            f"Path: {device_info.path}\n"
            f"Vendor: {device_info.vendor}\n"
            f"Product: {device_info.product}"
        )
        
        if is_in_whitelist:
            btn_whitelist = msg.addButton("Remove from Whitelist", QMessageBox.ButtonRole.ActionRole)
        else:
            btn_whitelist = msg.addButton("Add to Whitelist", QMessageBox.ButtonRole.ActionRole)
        
        msg.addButton(QMessageBox.StandardButton.Close)
        
        msg.exec()
        
        if msg.clickedButton() == btn_whitelist:
            if is_in_whitelist:
                self.config_manager.remove_from_whitelist(device_path)
                logger.info(f"Device removed from whitelist: {device_path}")
            else:
                self.config_manager.add_to_whitelist(device_path)
                logger.info(f"Device added to whitelist: {device_path}")
            
            self._refresh_device_list()

    def _on_device_selection_changed(self, selected_paths: list):
        """Callback when multiple selection changes in the device list."""
        if not selected_paths:
            # Clear details
            self.device_details_title.setText("Device Details")
            self.device_details_info.setText("Select a device to view details")
            self.btn_add_whitelist.setEnabled(False)
            self.btn_remove_whitelist.setEnabled(False)
            return

        # Show the first selected device details
        first = selected_paths[0]
        info = self.device_manager.get_device_by_path(first)

        if not info:
            self.device_details_info.setText("No information available")
            self.btn_add_whitelist.setEnabled(False)
            self.btn_remove_whitelist.setEnabled(False)
            return

        self.device_details_title.setText(f"{info.icon} {info.name}")
        self.device_details_info.setText(
            f"Type: {info.device_type.value}\n"
            f"Path: {info.path}\n"
            f"Vendor: {info.vendor}  Product: {info.product}"
        )

        in_whitelist = info.path in self.config_manager.get_whitelist()
        self.btn_add_whitelist.setEnabled(not in_whitelist)
        self.btn_remove_whitelist.setEnabled(in_whitelist)

    def _add_selected_to_whitelist(self):
        """Add selected devices to the whitelist."""
        paths = self.device_list.get_selected_device_paths()
        for p in paths:
            try:
                self.config_manager.add_to_whitelist(p)
                logger.info(f"Device added to whitelist: {p}")
            except Exception as e:
                logger.error(f"Error adding to whitelist {p}: {e}")

        self._refresh_device_list()

    def _remove_selected_from_whitelist(self):
        """Remove selected devices from the whitelist."""
        paths = self.device_list.get_selected_device_paths()
        for p in paths:
            try:
                self.config_manager.remove_from_whitelist(p)
                logger.info(f"Device removed from whitelist: {p}")
            except Exception as e:
                logger.error(f"Error removing from whitelist {p}: {e}")

        self._refresh_device_list()
    
    def _on_settings_changed(self):
        """Callback when settings change."""
        logger.info("Settings updated, applying changes...")
        
        self._apply_theme()
        self._update_hotkey_label()
        self._update_ui_state()
        
        # Apply always-on-top
        always_on_top = self.config_manager.get('ui', 'always_on_top', False)
        
        if always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        
        self.show()  # Necessary for flags to take effect
    
    def _on_hotkey_changed(self, new_hotkey: str):
        """Callback when hotkey changes."""
        logger.info(f"Updating hotkey to: {new_hotkey}")
        
        if self.hotkey_handler.update_hotkey(new_hotkey):
            self._update_hotkey_label()
            self._show_notification(
                "Hotkey Updated",
                f"New shortcut: {new_hotkey}"
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Could not update the hotkey"
            )
    
    def _show_notification(self, title: str, message: str):
        """Muestra una notificación del sistema."""
        if self.tray_icon and self.config_manager.get('general', 'show_notifications', True):
            self.tray_icon.show_notification(title, message)
    
    def _quit_application(self):
        """Cierra la aplicación completamente."""
        reply = QMessageBox.question(
            self,
            "Confirmar Salida",
            "Are you sure you want to exit?\n"
            "Devices will be automatically unlocked.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Closing application...")
            
            # Desbloquear todo
            self.input_blocker.unlock_all()
            
            # Cerrar aplicación
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()
    
    def closeEvent(self, event: QCloseEvent):
        """Close event: fully exit the application.

        For this project we prefer explicit exit semantics over
        minimizing to tray: when the user closes the main window,
        the process should terminate after optionally confirming.
        """
        self._quit_application()
        event.accept()
