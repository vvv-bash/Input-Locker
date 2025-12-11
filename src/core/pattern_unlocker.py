"""
Pattern unlocker (Konami-style sequence) to unlock via a specific key sequence.
"""

import time
from evdev import ecodes
from ..utils.logger import logger


class PatternUnlocker:
    """Detects a specific key pattern to trigger an unlock callback."""

    def __init__(self, callback, pattern=None, timeout=3.0):
        """
        Initialize the pattern detector.

        Args:
            callback: Callable to invoke when the pattern is detected
            pattern: List of key codes that form the pattern
            timeout: Maximum time between keys (seconds)
        """
        self.callback = callback
        self.timeout = timeout

        # Default pattern: UP UP DOWN DOWN ENTER
        if pattern is None:
            self.pattern = [
                ecodes.KEY_UP,
                ecodes.KEY_UP,
                ecodes.KEY_DOWN,
                ecodes.KEY_DOWN,
                ecodes.KEY_ENTER
            ]
        else:
            self.pattern = pattern

        self.current_sequence = []
        self.last_key_time = 0

        # Human readable pattern name
        self.pattern_name = self._get_pattern_name()

        logger.info(f"PatternUnlocker initialized: {self.pattern_name}")

    def _get_pattern_name(self):
        """Return a human-readable name for the pattern."""
        key_names = []
        for key_code in self.pattern:
            name = self._get_key_name(key_code)
            key_names.append(name)
        return " → ".join(key_names)

    def _get_key_name(self, key_code):
        """Return a short name for a key code."""
        key_map = {
            ecodes.KEY_UP: "↑",
            ecodes.KEY_DOWN: "↓",
            ecodes.KEY_LEFT: "←",
            ecodes.KEY_RIGHT: "→",
            ecodes.KEY_ENTER: "ENTER",
            ecodes.KEY_SPACE: "SPACE",
            ecodes.KEY_ESC: "ESC",
            ecodes.KEY_A: "A",
            ecodes.KEY_B: "B",
            ecodes.KEY_L: "L",
            ecodes.KEY_O: "O",
            ecodes.KEY_C: "C",
            ecodes.KEY_K: "K",
        }

        if key_code in key_map:
            return key_map[key_code]

        # Fallback to ecodes names
        for name in dir(ecodes):
            if name.startswith('KEY_') and getattr(ecodes, name) == key_code:
                return name.replace('KEY_', '')

        return f"KEY_{hex(key_code)}"

    def handle_key(self, key_code, key_state):
        """
        Process a key event.

        Args:
            key_code: Key code
            key_state: State (0=release, 1=press, 2=hold)

        Returns:
            bool: True if the full pattern was detected
        """
        # Only process key presses
        if key_state != 1:
            return False

        current_time = time.time()

        # Reset if timeout elapsed
        if current_time - self.last_key_time > self.timeout:
            if self.current_sequence:
                logger.debug(f"⏱️  Pattern timeout - resetting ({current_time - self.last_key_time:.1f}s)")
            self.current_sequence = []

        self.last_key_time = current_time

        expected_position = len(self.current_sequence)

        if expected_position >= len(self.pattern):
            # Completed pattern previously, reset
            self.current_sequence = []
            expected_position = 0

        expected_key = self.pattern[expected_position]

        if key_code == expected_key:
            self.current_sequence.append(key_code)
            key_name = self._get_key_name(key_code)

            logger.info(f"✓ Pattern: {len(self.current_sequence)}/{len(self.pattern)} - Correct key: {key_name}")

            # Show progress
            progress = []
            for i, k in enumerate(self.pattern):
                if i < len(self.current_sequence):
                    progress.append(f"[{self._get_key_name(k)}]")
                else:
                    progress.append(self._get_key_name(k))
            logger.info(f"   Progress: {' '.join(progress)}")

            # Check if pattern completed
            if len(self.current_sequence) == len(self.pattern):
                logger.info("=" * 60)
                logger.info("🎉 PATTERN COMPLETED!")
                logger.info(f"   Pattern: {self.pattern_name}")
                logger.info("   🔓 Unlocking...")
                logger.info("=" * 60)

                self.current_sequence = []

                if self.callback:
                    try:
                        self.callback()
                        logger.info("✓ Callback executed successfully")
                    except Exception as e:
                        logger.error(f"❌ Error executing callback: {e}")
                        import traceback
                        logger.error(traceback.format_exc())

                return True
        else:
            # Wrong key - reset sequence
            if self.current_sequence:
                wrong_key = self._get_key_name(key_code)
                expected_name = self._get_key_name(expected_key)
                logger.warning(f"✗ Wrong key: {wrong_key} (expected {expected_name})")
                logger.info(f"   Pattern interrupted - resetting...")
                self.current_sequence = []

        return False

    def reset(self):
        """Reset the detector state."""
        logger.debug("Resetting pattern detector")
        self.current_sequence = []
        self.last_key_time = 0

    def get_progress(self):
        """Return current progress as (completed_keys, total_keys)."""
        return (len(self.current_sequence), len(self.pattern))
