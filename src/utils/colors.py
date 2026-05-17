import logging

from PySide6.QtGui import QColor

LEVEL_COLORS = {
    logging.DEBUG: QColor(0, 255, 128),
    logging.INFO: QColor(0, 128, 255),
    logging.WARNING: QColor(255, 128, 0),
    logging.ERROR: QColor(255, 64, 64),
    logging.CRITICAL: QColor(255, 0, 255)
}
