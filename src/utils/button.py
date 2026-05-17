from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QToolButton, QWidget


def create_icon_push_button(
        icon: QIcon,
        tooltip: str,
        size: QSize = QSize(32, 32),
        parent: Optional[QWidget] = None
) -> QPushButton:
    """
    Создать кнопку.

    :param icon: Иконка.
    :param tooltip: Описание.
    :param size: Размер.
    :param parent: Родитель.

    :return: Кнопка.
    """
    push_button = QPushButton(parent)
    push_button.setIcon(icon)
    push_button.setIconSize(size - QSize(5, 5))
    push_button.setToolTip(tooltip)
    push_button.setFixedSize(size)
    return push_button


def create_tool_button(
        icon: QIcon,
        tooltip: str,
        size: QSize = QSize(32, 32),
        parent: Optional[QWidget] = None
) -> QToolButton:
    """
    Создать кнопку.

    :param icon: Иконка.
    :param tooltip: Описание.
    :param size: Размер.
    :param parent: Родитель.

    :return: Кнопка.
    """
    tool_button = QToolButton(parent)
    tool_button.setIcon(icon)
    tool_button.setIconSize(size)
    tool_button.setToolTip(tooltip)
    return tool_button
