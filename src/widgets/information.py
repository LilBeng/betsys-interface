import logging

from PySide6.QtCore import Qt, Slot, Signal as pysideSignal, QPoint, QStandardPaths
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QToolBar,
    QMenu,
    QLineEdit,
    QFileDialog
)
from betsys import DriverCode, CheckPoint, MatchDetails, format_match_details
from betsys.driver.base import Information, SportEventDriver

from src.dialogs.information import InformationDialog
from src.dialogs.market import StackedMarketDialog
from src.dialogs.match import MatchDetailsDialog
from src.utils.lang import AppLang
from src.utils.service import SportEventService
from src.utils.tree import tree_str
from src.widgets.table import MatchTableWidget

_logger = logging.getLogger(__name__)


class InformationWidget(QFrame):
    print_text = pysideSignal(str)
    show_message = pysideSignal(str)
    update_progress = pysideSignal(int, int)

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

        self._update_table = QAction(
            icon=QIcon(":/resources/icons/update.png"),
            text=self.tr("Обновить матчи"),
            parent=self
        )

        self._print_info = QAction(
            icon=QIcon(":/resources/icons/console.png"),
            text=self.tr("Вывести зависимости в консоль"),
            parent=self
        )

        self._show_info = QAction(
            icon=QIcon(":/resources/icons/info.png"),
            text=self.tr("Показать информацию"),
            parent=self
        )

        self._save_checkpoint = QAction(
            icon=QIcon(":/resources/icons/save.png"),
            text=self.tr("Сохранить контрольную точку"),
            parent=self
        )

        self._show_match = QAction(
            icon=QIcon(":/resources/icons/edit.png"),
            text=self.tr("Открыть матч"),
            parent=self
        )

        bar = QToolBar(self)

        self._table = MatchTableWidget(parent=self)
        self._table.cellDoubleClicked.connect(self.show_match)
        self._table.horizontalHeader().setMinimumSectionSize(150)
        self._table.update_progress.connect(self.update_progress)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self.show_context_menu)

        self._search_input = QLineEdit(self)
        self._search_input.setPlaceholderText(self.tr("Введите текст для поиска ..."))
        self._search_input.textChanged.connect(self.on_search)

        bar.addAction(self._update_table)
        bar.addAction(self._save_checkpoint)
        bar.addAction(self._show_info)
        bar.addAction(self._print_info)
        bar.addAction(self._show_match)

        self._show_info.triggered.connect(self.show_info)
        self._print_info.triggered.connect(self.print_info)
        self._update_table.triggered.connect(self.update_table)
        self._save_checkpoint.triggered.connect(self.save_checkpoint)
        self._show_match.triggered.connect(self.show_match)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.addWidget(bar)
        main_layout.addWidget(self._table)
        main_layout.addWidget(self._search_input)

        self._update_table.triggered.emit()

    @property
    def driver_code(self) -> DriverCode:
        return self._driver_code

    @Slot()
    def show_info(self) -> None:
        def _show_info(information: Information) -> None:
            if information:
                dialog = InformationDialog(information, parent=self)
                dialog.exec()
            else:
                self.show_message.emit(self.tr("Информация не получена"))

        self._service.get_object(
            _show_info,
            self.driver_code,
            SportEventDriver.__name__,
            SportEventService.get_name(SportEventDriver, SportEventDriver.information),
        )

    @Slot()
    def update_table(self) -> None:
        def _update_table(match_details: dict[str, MatchDetails]) -> None:
            if match_details:
                self._table.set_items(match_details.values()) # noqa

        self._service.get_object(
            _update_table,
            self.driver_code,
            CheckPoint.__name__,
            "match_details",
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
            _print_info,
            self.driver_code,
            CheckPoint.__name__,
            "consumed_match_ids",
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

            show_market = context_menu.addAction(
                QIcon(":/resources/icons/info.png"),
                self.tr("Показать коэффициенты")
            )
            show_market.triggered.connect(self._show_market)

            context_menu.addAction(self._show_match)

        context_menu.exec(self._table.mapToGlobal(position))

    @Slot()
    def _print_match_info(self) -> None:
        for model in self._table.get_selected_models():
            self.print_text.emit(f"{format_match_details(model, AppLang.code)}")

        self.show_message.emit(self.tr("Операция выполнена"))

    @Slot()
    def _show_market(self) -> None:
        dialog = StackedMarketDialog(self._table.get_selected_models(), self)
        dialog.exec()

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

    @Slot()
    def show_match(self) -> None:
        if matches := self._table.get_selected_models():
            dialog = MatchDetailsDialog(self._driver_code, matches, parent=self)
            dialog.exec()
        else:
            self.show_message.emit(self.tr("Матчи не выбраны"))
