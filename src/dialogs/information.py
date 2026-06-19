from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFormLayout, QLabel, QLayout, QWidget
from betsys import Information

from src.dialogs.base import BaseDialog


class InformationDialog(BaseDialog):
    def __init__(self, information: Information, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self.setWindowTitle(self.tr("Информация"))
        self.setWindowIcon(QIcon(":/resources/icons/info.png"))

        self._run_datetime = QLabel(information.run_datetime.strftime("%d.%m.%Y %H:%M"))
        self._update_date = QLabel(information.update_date.strftime("%d.%m.%Y"))
        self._matches_count = QLabel(str(information.matches_count))
        self._scripts_count = QLabel(str(information.scripts_count))
        self._signals_count = QLabel(str(information.signals_count))
        self._jobs_count = QLabel(str(information.jobs_count))
        self._next_run_job_datetime = QLabel(information.next_run_job_datetime.strftime("%H:%M:%S"))

        info_layout = QFormLayout(self)
        info_layout.setSpacing(15)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        info_layout.addRow(self.tr("Дата запуска:"), self._run_datetime)
        info_layout.addRow(self.tr("Дата загрузки матчей:"), self._update_date)
        info_layout.addRow(self.tr("Количество матчей:"), self._matches_count)
        info_layout.addRow(self.tr("Количество активных сценариев:"), self._scripts_count)
        info_layout.addRow(self.tr("Количество активных сигналов:"), self._signals_count)
        info_layout.addRow(self.tr("Запланировано задач:"), self._jobs_count)
        info_layout.addRow(self.tr("Запуск следующей:"), self._next_run_job_datetime)
