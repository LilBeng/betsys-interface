from PySide6.QtCore import Qt, Slot, Signal as pysideSignal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QScrollArea, QFormLayout, QLabel, QToolBar
from betsys import DriverCode, CheckPoint
from betsys.driver.base import Information, SportEventDriver

from src.utils.service import SportEventService
from src.utils.tree import tree_str


class InformationWidget(QFrame):
    print_text = pysideSignal(str)
    show_message = pysideSignal(str)

    def __init__(
            self,
            service: SportEventService,
            driver_code: DriverCode,
            information: Information,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._service = service
        self._driver_code = driver_code

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self._run_datetime = QLabel(information.run_datetime.strftime("%d.%m.%Y %H:%M"))
        self._update_date = QLabel(information.update_date.strftime("%d.%m.%Y"))
        self._matches_count = QLabel(str(information.matches_count))
        self._scripts_count = QLabel(str(information.scripts_count))
        self._signals_count = QLabel(str(information.signals_count))
        self._jobs_count = QLabel(str(information.jobs_count))
        self._next_run_job_datetime = QLabel(information.next_run_job_datetime.strftime("%H:%M:%S"))

        self._update_info = QAction(
            icon=QIcon(":/resources/icons/update.png"),
            text=self.tr("Обновить информацию"),
            parent=self
        )

        self._print_info = QAction(
            icon=QIcon(":/resources/icons/console.png"),
            text=self.tr("Вывести информацию в консоль"),
            parent=self
        )

        bar = QToolBar(self)

        container = QWidget()
        info_layout = QFormLayout(container)
        info_layout.setSpacing(15)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_layout.addRow(bar)
        info_layout.addRow(self.tr("Дата запуска:"), self._run_datetime)
        info_layout.addRow(self.tr("Дата текущего обновления:"), self._update_date)
        info_layout.addRow(self.tr("Количество матчей:"), self._matches_count)
        info_layout.addRow(self.tr("Количество активных сценариев:"), self._scripts_count)
        info_layout.addRow(self.tr("Количество активных сигналов:"), self._signals_count)
        info_layout.addRow(self.tr("Запланировано задач:"), self._jobs_count)
        info_layout.addRow(self.tr("Запуск следующей:"), self._next_run_job_datetime)

        scroll_area.setWidget(container)

        bar.addAction(self._update_info)
        bar.addAction(self._print_info)

        self._print_info.triggered.connect(self.print_info)
        self._update_info.triggered.connect(self.update_info)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    @property
    def driver_code(self) -> DriverCode:
        return self._driver_code

    @Slot()
    def update_info(self) -> None:

        def _update_info(information: Information) -> None:
            if information:
                self._run_datetime.setText(information.run_datetime.strftime("%d.%m.%Y %H:%M"))
                self._update_date.setText(information.update_date.strftime("%d.%m.%Y"))
                self._matches_count.setText(str(information.matches_count))
                self._scripts_count.setText(str(information.scripts_count))
                self._signals_count.setText(str(information.signals_count))
                self._jobs_count.setText(str(information.jobs_count))
                self._next_run_job_datetime.setText(information.next_run_job_datetime.strftime("%H:%M:%S"))

            self.show_message.emit(self.tr("Операция выполнена"))

        self._service.get_object(
            self.driver_code,
            SportEventDriver.__name__,
            SportEventService.get_name(SportEventDriver, SportEventDriver.information),
            _update_info
        )

    @Slot()
    def print_info(self) -> None:
        def _print_info(consumed_match_ids: dict[str, list[str]]) -> None:
            if consumed_match_ids:
                self.print_text.emit(
                    self.tr("Дерево зависимостей [ID сценария -> ID матча]:\n{}").format(tree_str(consumed_match_ids))
                )
            else:
                self.print_text.emit(self.tr("Дерево зависимостей [ID сценария -> ID матча]: не найдено"))

            self.show_message.emit(self.tr("Операция выполнена"))

        self._service.get_object(
            self.driver_code,
            CheckPoint.__name__,
            "consumed_match_ids",
            _print_info
        )
