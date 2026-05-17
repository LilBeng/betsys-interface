from typing import Optional

from PySide6.QtWidgets import QWidget, QTimeEdit


def get_time_edit(parent: Optional[QWidget] = None) -> QTimeEdit:
    """
    Получить виджет.

    :param parent: Родитель.

    :return: Виджет.
    """
    time_edit = QTimeEdit(parent)
    time_edit.setDisplayFormat("HH:mm:ss")
    time_edit.setWrapping(True)
    return time_edit
