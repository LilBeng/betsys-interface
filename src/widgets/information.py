import logging

from PySide6.QtCore import Qt, Slot, Signal as pysideSignal, QPoint, QStandardPaths
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QScrollArea,
    QFormLayout,
    QLabel,
    QToolBar,
    QMenu,
    QLineEdit,
    QFileDialog
)
from betsys import DriverCode, CheckPoint, MatchDetails, format_match_details
from betsys.driver.base import Information, SportEventDriver

from src.utils.lang import AppLang
from src.utils.service import SportEventService
from src.utils.tree import tree_str
from src.widgets.table import MatchTableWidget

_logger = logging.getLogger(__name__)


class InformationWidget(QFrame):
    print_text = pysideSignal(str)
    show_message = pysideSignal(str)
    update_progress = pysideSignal(int, int)

    _update = pysideSignal()

    def __init__(
            self,
            service: SportEventService,
            driver_code: DriverCode,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._service = service
        self._driver_code = driver_code

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self._run_datetime = QLabel("...")
        self._update_date = QLabel("...")
        self._matches_count = QLabel("...")
        self._scripts_count = QLabel("...")
        self._signals_count = QLabel("...")
        self._jobs_count = QLabel("...")
        self._next_run_job_datetime = QLabel("...")

        self._update_info = QAction(
            icon=QIcon(":/resources/icons/update.png"),
            text=self.tr("Обновить информацию"),
            parent=self
        )

        self._print_info = QAction(
            icon=QIcon(":/resources/icons/console.png"),
            text=self.tr("Вывести зависимости в консоль"),
            parent=self
        )

        self._save_checkpoint = QAction(
            icon=QIcon(":/resources/icons/save.png"),
            text=self.tr("Сохранить контрольную точку"),
            parent=self
        )

        bar = QToolBar(self)

        self._table = MatchTableWidget(self)
        self._table.horizontalHeader().setMinimumSectionSize(150)
        self._table.update_progress.connect(self.update_progress)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self.show_context_menu)

        self._search_input = QLineEdit(self)
        self._search_input.setPlaceholderText(self.tr("Введите текст для поиска ..."))
        self._search_input.textChanged.connect(self.on_search)

        container = QWidget()
        info_layout = QFormLayout(container)
        info_layout.setSpacing(15)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_layout.addRow(bar)
        info_layout.addRow(self.tr("Дата запуска:"), self._run_datetime)
        info_layout.addRow(self.tr("Дата загрузки матчей:"), self._update_date)
        info_layout.addRow(self.tr("Количество матчей:"), self._matches_count)
        info_layout.addRow(self.tr("Количество активных сценариев:"), self._scripts_count)
        info_layout.addRow(self.tr("Количество активных сигналов:"), self._signals_count)
        info_layout.addRow(self.tr("Запланировано задач:"), self._jobs_count)
        info_layout.addRow(self.tr("Запуск следующей:"), self._next_run_job_datetime)
        info_layout.addRow(self._table)
        info_layout.addRow(self._search_input)

        scroll_area.setWidget(container)

        bar.addAction(self._update_info)
        bar.addAction(self._save_checkpoint)
        bar.addAction(self._print_info)

        self._print_info.triggered.connect(self.print_info)
        self._update_info.triggered.connect(self.update_info)
        self._save_checkpoint.triggered.connect(self.save_checkpoint)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        self._update.connect(self.update_table)

        self._update_info.triggered.emit()

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

            self._update.emit()

        self._service.get_object(
            self.driver_code,
            SportEventDriver.__name__,
            SportEventService.get_name(SportEventDriver, SportEventDriver.information),
            _update_info
        )

    @Slot()
    def update_table(self) -> None:
        def _update_table(match_details: dict[str, MatchDetails]) -> None:
            if match_details:
                self._table.set_items(match_details.values()) # noqa

        self._service.get_object(
            self.driver_code,
            CheckPoint.__name__,
            "match_details",
            _update_table
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

    @Slot()
    def show_context_menu(self, position: QPoint) -> None:
        """
        Показать контекстное меню.

        :param position: Позиция.
        """
        context_menu = QMenu(self)

        if self._table.get_selected_models():
            action = context_menu.addAction(
                QIcon(":/resources/icons/console.png"),
                self.tr("Вывести в консоль")
            )
            action.triggered.connect(self._print_match_info)

        context_menu.exec(self._table.mapToGlobal(position))

    @Slot()
    def _print_match_info(self) -> None:
        for model in self._table.get_selected_models():
            self.print_text.emit(f"{format_match_details(model, AppLang.code)}")

        self.show_message.emit(self.tr("Операция выполнена"))

    @Slot()
    def on_search(self, text: str) -> None:
        if text.strip():
            self._table.filter_table_rows(text)
        else:
            self._table.show_all_rows()

    @Slot()
    def save_checkpoint(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent(),
            self.tr("Сохранить файл"),
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            self.tr("Файлы контрольной точки (*.cp)")
        )
        if file_path:
            self._service.save_checkpoint(file_path, self._driver_code)
