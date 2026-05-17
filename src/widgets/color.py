from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPalette, QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class ColorWidget(QWidget):
    def __init__(self, title: str, icon: QIcon, icon_size: QSize, color: QColor, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        self.setPalette(palette)

        icon_label = QLabel(self)
        icon_label.setPixmap(icon.pixmap(icon_size))

        text_label = QLabel(title, self)
        font = text_label.font()
        font.setBold(True)
        text_label.setFont(font)

        self.central_layout = QHBoxLayout(self)
        self.central_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignLeft)
        self.central_layout.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignLeft)
        self.central_layout.addStretch()
