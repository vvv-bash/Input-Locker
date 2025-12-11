"""
Centralized logging system for Input Locker.
"""

import logging
import os
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime


class Logger:
    """Central log manager with automatic rotation."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.logger = logging.getLogger('InputLocker')
        self.logger.setLevel(logging.DEBUG)
        self._json_format = False

        # Try to create system log dir, fallback to user local dir on permission error
        self.log_dir = Path('/var/log/input-locker')
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            # Verify writable
            test_file = self.log_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError):
            # Fallback to user's local directory
            self.log_dir = Path.home() / '.local' / 'share' / 'input-locker' / 'logs'
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / 'app.log'
        
        # Configure default formatter (text)
        self._text_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # JSON formatter function
        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                payload = {
                    'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
                    'logger': record.name,
                    'level': record.levelname,
                    'message': record.getMessage(),
                }
                # include extra if present
                if hasattr(record, 'extra'):
                    payload['extra'] = record.extra
                return json.dumps(payload, ensure_ascii=False)

        self._json_formatter = JSONFormatter()
        
        # File handler with rotation
        # Default rotation settings (can be reconfigured at runtime)
        self._max_bytes = 10 * 1024 * 1024
        self._backup_count = 5

        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self._max_bytes,
            backupCount=self._backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self._text_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self._text_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self._file_handler = file_handler
        self._console_handler = console_handler

    def configure(self, level=logging.INFO, json_format: bool = False):
        """Reconfigure logger at runtime.

        level: logging level to set for both handlers
        json_format: whether to write logs as JSON lines to file
        """
        try:
            self.logger.setLevel(level)
            self._console_handler.setLevel(level)
            self._file_handler.setLevel(min(level, logging.DEBUG))
            self._json_format = bool(json_format)
            if self._json_format:
                self._file_handler.setFormatter(self._json_formatter)
            else:
                self._file_handler.setFormatter(self._text_formatter)
            self.info(f"Logger reconfigured: level={logging.getLevelName(level)}, json={self._json_format}")
        except Exception:
            pass

    def reconfigure_rotation(self, max_bytes: int = None, backup_count: int = None):
        """Recreate the RotatingFileHandler with new rotation parameters.

        If a parameter is None, the existing value is preserved.
        """
        try:
            if max_bytes is not None:
                self._max_bytes = int(max_bytes)
            if backup_count is not None:
                self._backup_count = int(backup_count)

            # Remove existing file handler
            try:
                self.logger.removeHandler(self._file_handler)
            except Exception:
                pass

            # Create new handler with updated rotation
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self._max_bytes,
                backupCount=self._backup_count
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(self._json_formatter if self._json_format else self._text_formatter)
            self._file_handler = file_handler
            self.logger.addHandler(self._file_handler)
            self.info(f"Log rotation updated: max_bytes={self._max_bytes}, backup_count={self._backup_count}")
        except Exception:
            pass

    def is_json(self) -> bool:
        return bool(self._json_format)

    def get_log_entries(self, max_lines=1000):
        """Return parsed log entries if in JSON mode, otherwise raw lines.

        Returns list of dicts (JSON lines) or list of strings.
        """
        try:
            if not self.log_file.exists():
                return []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            lines = lines[-max_lines:]
            if self.is_json():
                entries = []
                for ln in lines:
                    try:
                        entries.append(json.loads(ln))
                    except Exception:
                        entries.append({'raw': ln.strip()})
                return entries
            else:
                return [ln.rstrip('\n') for ln in lines]
        except Exception:
            return []
    
    def get_log_file(self) -> str:
        """
        Return the current log file path.

        Returns:
            str: Full path to the log file
        """
        return str(self.log_file)
    
    def get_logger(self):
        """Return the logger instance."""
        return self.logger
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)
    
    def exception(self, message):
        """Log an exception with traceback."""
        self.logger.exception(message)


# Instancia global
logger_instance = Logger()
logger = logger_instance