"""
Animation utility functions for smooth UI transitions.
"""
from PyQt6.QtWidgets import QStackedWidget
from ..utils.logger import logger


def fade_transition(stacked_widget: QStackedWidget, target_index: int, duration: int = 300):
    """Safely switch pages; placeholder for future animations.

    Currently we prioritize reliability: if you click a nav item,
    the corresponding page is always made visible immediately.
    """
    try:
        if target_index == stacked_widget.currentIndex():
            return
        stacked_widget.setCurrentIndex(target_index)
    except Exception as e:
        logger.warning(f"Fade transition failed, falling back to instant switch: {e}")
        stacked_widget.setCurrentIndex(target_index)


def slide_transition(stacked_widget: QStackedWidget, target_index: int, duration: int = 300, direction: str = "left"):
    """
    Perform a slide transition between pages in a stacked widget.
    
    Args:
        stacked_widget: The QStackedWidget to transition
        target_index: The index of the target page
        duration: Animation duration in milliseconds
        direction: Direction of slide ("left", "right", "up", "down")
    """
    try:
        stacked_widget.setCurrentIndex(target_index)
    except Exception as e:
        logger.warning(f"Slide transition failed: {e}")


def scale_transition(stacked_widget: QStackedWidget, target_index: int, duration: int = 300):
    """
    Perform a scale transition between pages in a stacked widget.
    
    Args:
        stacked_widget: The QStackedWidget to transition
        target_index: The index of the target page
        duration: Animation duration in milliseconds
    """
    try:
        stacked_widget.setCurrentIndex(target_index)
    except Exception as e:
        logger.warning(f"Scale transition failed: {e}")
