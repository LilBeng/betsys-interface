from PySide6.QtCore import QObject, QEvent


class WheelBlocker(QObject):
    """
    Фильтр для блокировки событий колесика мыши
    """
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            return True
        return super().eventFilter(obj, event)
