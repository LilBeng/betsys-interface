from typing import Optional, Any

from PySide6.QtCore import QRect, QSize, Qt, QPoint
from PySide6.QtWidgets import QLayout, QWidget, QLayoutItem


class FlowLayout(QLayout):
    def __init__(self, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.items = []

    def addItem(self, item: QWidget) -> None:
        self.items.append(item)
        self.sort_items()

    def count(self) -> int:
        return len(self.items)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation.Horizontal

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        left, top, right, bottom = self.getContentsMargins()
        return self.do_layout(QRect(0, 0, width, 0), True) + top + bottom

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self.do_layout(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        return size

    def sort_items(self, attr: str = "datetime", reverse: bool = False) -> None:
        def get_sort_key(item: QLayoutItem) -> Any:
            widget = item.widget()
            if widget and hasattr(widget, attr):
                value = getattr(widget, attr)
                return value

            return 0

        self.items.sort(key=get_sort_key, reverse=reverse)
        self.invalidate()
        self.update()

    def do_layout(self, rect: QRect, is_test: bool) -> int:
        if not self.items:
            return 0

        left, top, right, bottom = self.getContentsMargins()
        available_rect = rect.adjusted(left, top, -right, -bottom)

        if available_rect.width() <= 0:
            return top + bottom

        # Максимум 3 в строке, но с учётом доступной ширины
        max_per_row = 0
        for count in range(1, min(3, len(self.items)) + 1):
            total_width = sum(item.sizeHint().width() for item in self.items[:count])
            total_width += self.spacing() * (count - 1)
            if total_width <= available_rect.width():
                max_per_row = count
            else:
                break

        if max_per_row == 0:
            max_per_row = 1

        # Разбиваем на строки по max_per_row
        lines = []
        for i in range(0, len(self.items), max_per_row):
            lines.append(self.items[i:i + max_per_row])

        # Вычисляем ширину одного виджета
        total_spacing = self.spacing() * (max_per_row - 1)
        item_width = (available_rect.width() - total_spacing) // max_per_row

        y = available_rect.y()

        for line in lines:
            x = available_rect.x()
            line_height = 0

            for item in line:
                if not is_test:
                    item.setGeometry(QRect(QPoint(x, y), QSize(item_width, item.sizeHint().height())))

                x += item_width + self.spacing()
                line_height = max(line_height, item.sizeHint().height())

            y += line_height + self.spacing()

        return y - self.spacing() + bottom + top

    def clear(self) -> None:
        for item in self.items[:]:
            widget = item.widget()
            widget.deleteLater()
            self.removeItem(item)

        self.items.clear()

        self.update()
        self.invalidate()
        self.activate()
