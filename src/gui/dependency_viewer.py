"""Dependency viewer showing system dependencies and their status.

This panel gives a quick health check of the external tools that
`input-locker` relies on. It aims to feel like a modern diagnostics
summary: clear status, minimal text, and a compact layout.
"""

import shutil
import subprocess
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt

from ..utils.logger import logger


class DependencyStatus(Enum):
    """Status of a dependency."""
    INSTALLED = "installed"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass
class Dependency:
    """Information about a dependency."""
    name: str
    version: str
    status: DependencyStatus
    description: str
    required: bool


class DependencyChecker:
    """Check system dependencies and their status."""
    
    def __init__(self):
        """Initialize the dependency checker."""
        self.dependencies: List[Dependency] = []
        # Minimal set of tools that are relevant for this app.
        self._definitions = [
            {
                "name": "xinput",
                "cmd": "xinput",
                "required": True,
                "description": "X11 input device utility (needed for some desktop environments)",
            },
            {
                "name": "evtest",
                "cmd": "evtest",
                "required": True,
                "description": "Low-level input event tester (helps debug /dev/input issues)",
            },
            {
                "name": "pkexec",
                "cmd": "pkexec",
                "required": True,
                "description": "Polkit helper for running privileged actions with GUI prompts",
            },
            {
                "name": "lsusb",
                "cmd": "lsusb",
                "required": False,
                "description": "List USB devices (useful for hardware diagnostics)",
            },
        ]
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get summary of dependency status after a check()."""
        installed = sum(1 for d in self.dependencies if d.status == DependencyStatus.INSTALLED)
        missing = sum(1 for d in self.dependencies if d.status == DependencyStatus.MISSING)
        return {"installed": installed, "missing": missing}

    def check(self) -> List[Dependency]:
        """Probe the system and update self.dependencies."""
        self.dependencies = []

        for item in self._definitions:
            name = item["name"]
            cmd = item["cmd"]
            required = item["required"]
            description = item["description"]

            path = shutil.which(cmd)
            if path:
                status = DependencyStatus.INSTALLED
                version = self._get_version(cmd)
            else:
                status = DependencyStatus.MISSING
                version = "-"

            self.dependencies.append(
                Dependency(
                    name=name,
                    version=version,
                    status=status,
                    description=description,
                    required=required,
                )
            )

        logger.debug("Dependency check completed")
        return self.dependencies

    @staticmethod
    def _get_version(cmd: str) -> str:
        """Best-effort attempt to get a version string for a command."""
        try:
            # Many tools support --version or -V; ignore output format details.
            proc = subprocess.run(
                [cmd, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=2,
            )
            line = (proc.stdout or "").splitlines()[0].strip()
            return line or "installed"
        except Exception:
            return "installed"


class DependencyViewer(QFrame):
    """Widget for viewing system dependencies."""
    
    def __init__(self):
        """Initialize the dependency viewer."""
        super().__init__()
        self.checker = DependencyChecker()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("🔧 Dependencies")
        title.setObjectName("lblSubtitle")
        layout.addWidget(title)

        self.summary_label = QLabel("Summary: not checked yet")
        self.summary_label.setObjectName("lblBody")
        layout.addWidget(self.summary_label)

        # Container where we will render per-dependency status rows
        self._deps_container = QVBoxLayout()
        self._deps_container.setContentsMargins(0, 4, 0, 4)
        self._deps_container.setSpacing(4)
        layout.addLayout(self._deps_container)

        hint = QLabel(
            "Tip: if some tools are missing, you can usually install them "
            "with your package manager (for example: apt, dnf, pacman)."
        )
        hint.setWordWrap(True)
        hint.setObjectName("lblCaption")
        layout.addWidget(hint)

        layout.addStretch(1)

        # Run an initial check so the panel is not empty
        self._refresh()

    def _refresh(self):
        """Run dependency checks and update the UI."""
        deps = self.checker.check()
        summary = self.checker.get_status_summary()

        self.summary_label.setText(
            f"Installed: {summary['installed']}  •  Missing: {summary['missing']}"
        )

        # Clear existing rows
        while self._deps_container.count():
            item = self._deps_container.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Rebuild simple status rows
        for dep in deps:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)

            # Status pill
            status_label = QLabel()
            if dep.status == DependencyStatus.INSTALLED:
                status_label.setText("●")
                status_label.setStyleSheet("color: #22C55E; font-weight: bold;")
            elif dep.required:
                status_label.setText("●")
                status_label.setStyleSheet("color: #EF4444; font-weight: bold;")
            else:
                status_label.setText("●")
                status_label.setStyleSheet("color: #FACC15; font-weight: bold;")
            row.addWidget(status_label)

            # Name + description
            name_label = QLabel(f"{dep.name} ({'required' if dep.required else 'optional'})")
            name_label.setObjectName("lblBody")
            row.addWidget(name_label, 1)

            # Version / status text (right-aligned)
            version_text = dep.version if dep.status == DependencyStatus.INSTALLED else dep.status.value
            version_label = QLabel(version_text)
            version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            version_label.setObjectName("lblCaption")
            row.addWidget(version_label)

            # Pack row into a lightweight container widget
            row_widget = QFrame()
            row_widget.setLayout(row)
            self._deps_container.addWidget(row_widget)
