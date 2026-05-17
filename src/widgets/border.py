from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPaintEvent, QPainter
from PySide6.QtWidgets import QWidget


class BorderWidget(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._show_pixmap = True
        self._pixmap = QPixmap(":/resources/images/background.png")

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self._pixmap.isNull() and self._show_pixmap:
            painter = QPainter(self)

            # Масштабируем с сохранением пропорций
            scaled_pixmap = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Центрируем картинку
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)

        super().paintEvent(event)

    def show_background(self) -> None:
        self._show_pixmap = True
        self.update()

    def hide_background(self) -> None:
        self._show_pixmap = False
        self.update()
