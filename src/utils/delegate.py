from PySide6.QtCore import QModelIndex, Qt, QRect
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from betsys import ResultCode


class ResultDelegate(QStyledItemDelegate):
    a = 20
    b = 5

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().paint(painter, option, index)

        blocks = index.data(Qt.ItemDataRole.UserRole)
        if not blocks:
            return None

        x = option.rect.left() + self.b

        for result_code in blocks:
            if result_code == ResultCode.WIN:
                color = QColor(76, 175, 80)
                text = self.tr("В")
            elif result_code == ResultCode.DRAW:
                color = QColor(255, 193, 7)
                text = self.tr("Н")
            elif result_code == ResultCode.LOSS:
                color = QColor(244, 67, 54)
                text = self.tr("П")
            else:
                color = QColor(158, 158, 158)
                text = self.tr("?")

            rect = QRect(x, option.rect.top() + self.b, self.a, self.a)

            painter.fillRect(rect, color)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

            x += self.a + self.b
