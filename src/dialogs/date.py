from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton

from src.widgets.calendar import DateRangeCalendar


class DatePickerDialog(QDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle(self.tr("Выбор даты"))
        self.setModal(True)

        layout = QVBoxLayout(self)

        self.calendar = DateRangeCalendar(parent=self)
        layout.addWidget(self.calendar)

        buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton(self.tr("Запустить"), parent=self)
        self.cancel_button = QPushButton(self.tr("Отмена"), parent=self)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    @property
    def selected_date(self) -> QDate:
        return self.calendar.selectedDate()

    @staticmethod
    def get_date(*args, **kwargs) -> Optional[QDate]:
        """
        Получить дату.

        :return: Дата или None.
        """
        dialog = DatePickerDialog(*args, **kwargs)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.selected_date
        return None
