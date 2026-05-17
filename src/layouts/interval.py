from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QWidget, QLabel, QSpinBox
from betsys import Interval


class IntervalLayout(QHBoxLayout):
    def __init__(self, min_val: int, max_val: int, parent: Optional[QWidget] = None) -> None:
        super().__init__()

        self._label = QLabel("-", parent)
        self._min = QSpinBox(minimum=min_val, maximum=max_val, singleStep=1, value=min_val, parent=parent)
        self._max = QSpinBox(minimum=min_val, maximum=max_val, singleStep=1, value=max_val, parent=parent)

        self._min.setMinimumWidth(100)
        self._max.setMinimumWidth(100)

        self.addWidget(self._min, alignment=Qt.AlignmentFlag.AlignLeft)
        self.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.addWidget(self._max, alignment=Qt.AlignmentFlag.AlignRight)

    @property
    def min(self) -> QSpinBox:
        return self._min

    @property
    def max(self) -> QSpinBox:
        return self._max

    @property
    def interval(self) -> Interval:
        return Interval(min=self.min.value(), max=self.max.value())

    def setEnabled(self, flag: bool) -> None:
        self._min.setEnabled(flag)
        self._label.setEnabled(flag)
        self._max.setEnabled(flag)
