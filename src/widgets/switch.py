from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QBrush, QMouseEvent, Qt
from PySide6.QtWidgets import QWidget


class Switch(QWidget):
    toggled = Signal(bool)

    def __init__(self, size: QSize, padding: int = 4, checked: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._size = size
        self._padding = padding

        self.setFixedSize(size)

        if checked:
            self._handle_pos = size.width() / 2
        else:
            self._handle_pos = 0

        self._checked = checked
        self._animation = QPropertyAnimation(self, b"handle_pos")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.set_checked(checked)

    @Property(float)
    def handle_pos(self) -> float:
        return self._handle_pos

    @handle_pos.setter
    def handle_pos(self, pos: float) -> None:
        self._handle_pos = pos
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        self._checked = not self._checked
        self._animate()
        self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def _animate(self):
        self._animation.stop()
        if self._checked:
            self._animation.setEndValue(self.width() - self.height())
        else:
            self._animation.setEndValue(0)
        self._animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.isEnabled():
            if self._checked:
                bg_color = QColor(75, 215, 100)
            else:
                bg_color = QColor(230, 230, 230)
        else:
            if self._checked:
                bg_color = QColor(180, 210, 180)
            else:
                bg_color = QColor(200, 200, 200)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

        # Рисуем ручку
        handle_size = self.height() - self._padding
        handle_x = self._handle_pos

        if self.isEnabled():
            painter.setBrush(QBrush(QColor(64, 64, 64)))
        else:
            painter.setBrush(QBrush(QColor(160, 160, 160)))

        painter.drawEllipse(handle_x + int(self._padding / 2), int(self._padding / 2), handle_size, handle_size)

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool) -> None:
        if self._checked != checked:
            self._checked = checked
            self._animate()
            self.toggled.emit(self._checked)
