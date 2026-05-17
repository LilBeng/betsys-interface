from PySide6.QtCore import QDate
from PySide6.QtWidgets import QCalendarWidget


class DateRangeCalendar(QCalendarWidget):
    """
    Календарь.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.current_date = QDate.currentDate()
        self.max_date = self.current_date.addDays(6)

        self.setDateRange(self.current_date, self.max_date)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
