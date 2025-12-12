"""Log viewer with filtering and export capabilities."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QComboBox, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt
from pathlib import Path

from ..utils.logger import logger_instance, logger


class LogViewer(QDialog):
    """Dialog to view application logs."""
    
    def __init__(self, parent=None):
        """Initialize the log viewer."""
        super().__init__(parent)
        self.setWindowTitle("Log Viewer - Input Locker")
        self.resize(800, 600)
        
        # Ensure we always work with a Path object
        self.log_file = Path(logger_instance.get_log_file())
        self.current_filter = "ALL"
        self.json_mode = logger_instance.is_json()
        
        self._init_ui()
        self._load_logs()
        
        # Timer for auto-refresh
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._load_logs)
        self.update_timer.start(2000)  # Actualizar cada 2 segundos
    
    def _init_ui(self):
        """Initialize the interface."""
        layout = QVBoxLayout(self)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        # Filter by level
        toolbar_layout.addWidget(QLabel("Filter by level:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self.filter_combo)

        # JSON toggle
        self.json_toggle = QComboBox()
        self.json_toggle.addItems(["Auto", "Plain", "JSON"])
        self.json_toggle.setCurrentText("JSON" if self.json_mode else "Plain")
        self.json_toggle.currentTextChanged.connect(self._on_json_toggle)
        toolbar_layout.addWidget(self.json_toggle)
        
        toolbar_layout.addStretch()
        
        # Buttons
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setObjectName("btnSecondary")
        btn_refresh.clicked.connect(self._load_logs)
        toolbar_layout.addWidget(btn_refresh)
        
        btn_clear = QPushButton("🗑️ Clear Logs")
        btn_clear.setObjectName("btnSecondary")
        btn_clear.clicked.connect(self._clear_logs)
        toolbar_layout.addWidget(btn_clear)
        
        btn_export = QPushButton("💾 Export")
        btn_export.setObjectName("btnSecondary")
        btn_export.clicked.connect(self._export_logs)
        toolbar_layout.addWidget(btn_export)
        
        layout.addLayout(toolbar_layout)
        
        # Text area for logs
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_text.setFont(self._get_monospace_font())
        layout.addWidget(self.log_text)
        
        # Info footer
        self.info_label = QLabel()
        self.info_label.setObjectName("lblSubtitle")
        layout.addWidget(self.info_label)
        
        # Bottom actions
        bottom_row = QHBoxLayout()

        # Copy summary button (used by Diagnostics too)
        btn_copy = QPushButton("📋 Copy Summary")
        btn_copy.setObjectName("btnSecondary")
        btn_copy.clicked.connect(self._copy_summary)
        bottom_row.addWidget(btn_copy)

        bottom_row.addStretch()

        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        bottom_row.addWidget(btn_close)

        layout.addLayout(bottom_row)
    
    def _get_monospace_font(self):
        """Return a monospace font."""
        from PyQt6.QtGui import QFont, QFontDatabase

        # Prefer modern developer fonts if they are available on the system.
        candidates = [
            "JetBrains Mono",
            "Fira Code",
            "Source Code Pro",
            "Cascadia Code",
            "Courier New",
            "monospace",
        ]

        families = QFontDatabase.families()
        family = None
        for name in candidates:
            if name in families:
                family = name
                break

        if family is None:
            family = "Courier New"

        font = QFont(family, 9)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        return font
    
    def _load_logs(self):
        """Load logs from the file."""
        try:
            if not self.log_file.exists():
                self.log_text.setPlainText("Log file not found.")
                return

            # Use logger_instance to read entries (it can parse JSON lines)
            entries = logger_instance.get_log_entries(max_lines=2000)

            display_lines = []
            lines = []  # type: ignore[assignment]
            if isinstance(entries, list) and entries and isinstance(entries[0], dict):
                # JSON entries -> pretty format and filter by level
                for e in entries:
                    level = e.get('level', '')
                    if self.current_filter != 'ALL' and level != self.current_filter:
                        continue
                    timestamp = e.get('timestamp', '')
                    msg = e.get('message', e.get('raw', ''))
                    display_lines.append(f"{timestamp} {level} - {msg}\n")
                lines = entries
            else:
                # Plain text
                lines = entries
                if self.current_filter != "ALL":
                    lines = [line for line in lines if self.current_filter in line]

                # Ensure each entry ends with a newline so they appear
                # as one line per log entry, like a terminal.
                for raw in lines[-1000:]:
                    line = str(raw)
                    if not line.endswith("\n"):
                        line += "\n"
                    display_lines.append(line)

            self.log_text.setPlainText(''.join(display_lines))
            
            # Scroll to the end
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
            
            # Update info
            total_lines = len(lines) if isinstance(lines, list) else 0
            displayed_lines = len(display_lines)
            self.info_label.setText(
                f"Showing {displayed_lines} of {total_lines} lines | "
                f"File: {self.log_file}"
            )
            
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
            self.log_text.setPlainText(f"Error loading logs: {e}")
    
    def _on_filter_changed(self, level: str):
        """Callback when the filter changes."""
        self.current_filter = level
        self._load_logs()
    
    def _on_json_toggle(self, mode: str):
        """Callback when JSON mode toggle changes."""
        try:
            # Update logger format based on selection
            if mode == "JSON":
                logger_instance.configure(json_format=True)
            elif mode == "Plain":
                logger_instance.configure(json_format=False)
            # "Auto" leaves current format untouched
            self.json_mode = logger_instance.is_json()
            self._load_logs()
        except Exception as e:
            logger.error(f"Error changing log view mode: {e}")
    
    def _clear_logs(self):
        """Clear the log file."""
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure you want to clear all logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write("")
                
                logger.info("Logs cleared by user")
                self._load_logs()

                QMessageBox.information(self, "Success", "Logs cleared successfully.")
                
            except Exception as e:
                logger.error(f"Error clearing logs: {e}")
                QMessageBox.critical(self, "Error", f"Error clearing logs: {e}")
    
    def _export_logs(self):
        """Export logs to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            str(Path.home() / "input-locker-logs.txt"),
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy(self.log_file, file_path)
                
                logger.info(f"Logs exported to: {file_path}")
                QMessageBox.information(
                    self,
                    "Success",
                    f"Logs exported successfully to:\n{file_path}"
                )
                
            except Exception as e:
                logger.error(f"Error exporting logs: {e}")
                QMessageBox.critical(self, "Error", f"Error exporting logs: {e}")

    def _copy_summary(self):
        """Copy a short diagnostics summary to the clipboard.

        This is intended to be pasted in bug reports. It includes the
        current log file path, JSON/plain mode and the last visible
        lines currently loaded in the viewer.
        """
        try:
            from PyQt6.QtWidgets import QApplication

            clipboard = QApplication.instance().clipboard()

            header = [
                "Input Locker – Diagnostics Summary",
                f"Log file: {self.log_file}",
                f"JSON mode: {'yes' if self.json_mode else 'no'}",
                f"Filter: {self.current_filter}",
                "",
                "Last visible log lines:",
                "----------------------------------------",
            ]
            body = self.log_text.toPlainText().splitlines()[-50:]
            text = "\n".join(header + body)

            clipboard.setText(text)

            QMessageBox.information(
                self,
                "Diagnostics copied",
                "A short diagnostics summary has been copied to the clipboard.\n"
                "You can paste it directly into a bug report.",
            )
        except Exception as e:
            logger.error(f"Error copying diagnostics summary: {e}")
    
    def closeEvent(self, event):
        """Override close event to stop the timer."""
        self.update_timer.stop()
        event.accept()