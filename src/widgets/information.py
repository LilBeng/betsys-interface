import logging

from PySide6.QtCore import Qt, Slot, Signal as pysideSignal, QPoint, QStandardPaths
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QToolBar,
    QMenu,
    QLineEdit,
    QFileDialog,
    QComboBox,
    QWidget,
    QFormLayout,
    QSizePolicy
)
from betsys import (
    DriverCode,
    CheckPoint,
    MatchDetails,
    format_match_details,
    MatchFilterDBModel,
    BetCode,
    MatchStatusCode,
    SignalTypeCode,
    EventCode, Signal, get_driver_name
)
from betsys.driver.base import Information, SportEventDriver
from qasync import asyncSlot

from src.dialogs.chat import MatchMessageViewer
from src.dialogs.information import InformationDialog
from src.dialogs.market import StackedMarketDialog
from src.dialogs.match import MatchDetailsDialog
from src.dialogs.property import CreateSignalDialog
from src.utils.lang import AppLang
from src.utils.service import BetSysService, SportEventService
from src.utils.tree import tree_str
from src.widgets.table import MatchTableWidget

_logger = logging.getLogger(__name__)


class InformationWidget(QFrame):
    print_text = pysideSignal(str)
    show_message = pysideSignal(str)
    update_progress = pysideSignal(int, int)

    def __init__(self, driver_code: DriverCode, update_time: int = 120000, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._driver_code = driver_code
        self._update_time = update_time

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

        self._filters = QComboBox(self)
        self._filters.setMinimumWidth(250)
        self._filters.currentIndexChanged.connect(self.filter_table)

        filter_widget = QWidget()
        filter_layout = QFormLayout(filter_widget)
        filter_layout.addRow(self.tr("Фильтр:"), self._filters)

        self._update_db_filters = QAction(
            icon=QIcon(":/resources/icons/update.png"),
            text=self.tr("Обновить фильтры"),
            parent=self
        )

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        bar.addWidget(spacer)
        bar.addWidget(filter_widget)
        bar.addAction(self._update_db_filters)

        self._show_info.triggered.connect(self.show_info)
        self._print_info.triggered.connect(self.print_info)
        self._update_table.triggered.connect(self.update_table)
        self._save_checkpoint.triggered.connect(self.save_checkpoint)
        self._show_match.triggered.connect(self.show_match)
        self._update_db_filters.triggered.connect(self.update_filters)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.addWidget(bar)
        main_layout.addWidget(self._table)
        main_layout.addWidget(self._search_input)

        BetSysService.service.match_event.connect(self.update_table_item)

        self._update_db_filters.triggered.emit()

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

        if BetSysService.service.workers.get(self.driver_code):
            BetSysService.service.get_object(
                _show_info,
                self.driver_code,
                SportEventDriver.__name__,
                SportEventService.get_name(SportEventDriver, SportEventDriver.information)
            )
        else:
            self.show_message.emit(
                self.tr("Для выполнения действия инициализируйте драйвер «{}»").format(
                    get_driver_name(self.driver_code, AppLang.code)
                )
            )

    @Slot()
    def update_table_item(self, code: EventCode, details: MatchDetails, driver_code: DriverCode) -> None:
        if driver_code == self.driver_code:
            match code:
                case EventCode.CREATED:
                    self._table.add_item(details)
                case EventCode.UPDATED:
                    self._table.update_item(details)
                case EventCode.COMPLETED:
                    self._table.delete_item(details)
                case EventCode.DELETED:
                    self._table.delete_item(details)
                case EventCode.RESUMED:
                    self._table.add_item(details)

            data = self._filters.currentData()
            if data:
                self._table.filter_matches(data)
            else:
                self._table.show_all_matches()

    @Slot()
    def update_table(self) -> None:
        def _update_table(match_details: dict[str, MatchDetails]) -> None:
            if match_details:
                self._table.set_items(match_details.values()) # noqa

                data = self._filters.currentData()
                if data:
                    self._table.filter_matches(data)
                else:
                    self._table.show_all_matches()

        if BetSysService.service.workers.get(self.driver_code):
            BetSysService.service.get_object(
                _update_table,
                self.driver_code,
                CheckPoint.__name__,
                "match_details",
            )
        else:
            self.show_message.emit(
                self.tr("Для выполнения действия инициализируйте драйвер «{}»").format(
                    get_driver_name(self.driver_code, AppLang.code)
                )
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

        if BetSysService.service.workers.get(self.driver_code):
            BetSysService.service.get_object(
                _print_info,
                self.driver_code,
                CheckPoint.__name__,
                "consumed_match_ids",
            )
        else:
            self.show_message.emit(
                self.tr("Для выполнения действия инициализируйте драйвер «{}»").format(
                    get_driver_name(self.driver_code, AppLang.code)
                )
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
                self.tr("Вывести матч в консоль")
            )
            action.triggered.connect(self._print_match_info)

            create_action = context_menu.addAction(
                QIcon(":/resources/icons/create.png"),
                self.tr("Создать сигнал")
            )
            create_action.triggered.connect(self._create_signal)

            context_menu.addSeparator()

            run_assistant = context_menu.addAction(
                QIcon(":/resources/icons/run.png"),
                self.tr("Запустить анализ ИИ")
            )
            run_assistant.triggered.connect(self._run_analyse)

            prompts = context_menu.addAction(
                QIcon(":/resources/icons/console.png"),
                self.tr("Вывести запросы в консоль")
            )
            prompts.triggered.connect(self._print_prompts)

            show_message = context_menu.addAction(
                QIcon(":/resources/icons/dialog.png"),
                self.tr("Показать сообщения")
            )
            show_message.triggered.connect(self._show_dialog)

            context_menu.addSeparator()

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
    def _create_signal(self) -> None:
        for model in self._table.get_selected_models():
            dialog = CreateSignalDialog(self.driver_code, model, self)
            dialog.add_signal.connect(self._add_signal)
            dialog.exec()

    @Slot()
    def _add_signal(self, signal: Signal) -> None:
        def _completed(flag: bool) -> None:
            if flag:
                self.show_message.emit(self.tr("Сигнал (id={}) - зарегистрирован").format(signal.signal_id))
            else:
                self.show_message.emit(self.tr("Не удалось зарегистрировать сигнал (id={})").format(signal.signal_id))

        BetSysService.service.get_object(
            _completed,
            self._driver_code,
            SportEventDriver.__name__,
            SportEventDriver.add_signal.__name__,
            signal
        )

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
        if BetSysService.service.workers.get(self.driver_code):
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent(),
                self.tr("Сохранить файл"),
                QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
                self.tr("Файлы контрольной точки (*.cp)")
            )
            if file_path:
                BetSysService.service.save_checkpoint(file_path, self._driver_code)
        else:
            self.show_message.emit(
                self.tr("Для выполнения действия инициализируйте драйвер «{}»").format(
                    get_driver_name(self.driver_code, AppLang.code)
                )
            )

    @Slot()
    def show_match(self) -> None:
        if matches := self._table.get_selected_models():
            dialog = MatchDetailsDialog(self._driver_code, matches, parent=self)
            dialog.exec()
        else:
            self.show_message.emit(self.tr("Матчи не выбраны"))

    @Slot()
    def filter_table(self, index: int) -> None:
        data = self._filters.itemData(index)
        if data:
            self._table.filter_matches(data)
        else:
            self._table.show_all_matches()

    @Slot()
    def _show_dialog(self) -> None:
        if matches := self._table.get_selected_models():
            for match in matches:
                dialog = MatchMessageViewer(match, self._driver_code, parent=self)
                dialog.exec()
        else:
            self.show_message.emit(self.tr("Матчи не выбраны"))

    @Slot()
    def _run_analyse(self) -> None:
        if matches := self._table.get_selected_models():
            for match in matches:
                match_id = match.match.match_id

                def _check(flag: bool) -> None:
                    if flag:
                        self.show_message.emit(self.tr("Матч (id={}) - анализ завершен").format(match_id))
                    else:
                        self.show_message.emit(self.tr("Не удалось проанализировать матч (id={})").format(match_id))

                BetSysService.service.get_object(
                    _check,
                    self.driver_code,
                    SportEventDriver.__name__,
                    SportEventDriver.generate_assistant_match_messages.__name__,
                    match_id
                )

    @asyncSlot()
    async def update_filters(self) -> None:
        filters = await BetSysService.service.db_context.filters.get_filters(
            SportEventService.get_match_code(self._driver_code)
        )

        self._update_filters(filters)

    @asyncSlot()
    async def _print_prompts(self) -> None:
        for model in self._table.get_selected_models():
            if model.match.match_summary.match_status_code == MatchStatusCode.IN_PROGRESS:
                code = SignalTypeCode.LIVE
            else:
                code = SignalTypeCode.PRE_MATCH

            prompts = await BetSysService.service.db_context.prompts.get_prompts(
                BetCode.UNKNOWN,
                SportEventService.get_match_code(self._driver_code),
                code
            )
            if prompts:
                for index, prompt in enumerate(prompts, start=1):
                    text = prompt.generate_prompt(model, None, AppLang.code)
                    self.print_text.emit(f"#{index}\n{text}")
            else:
                self.show_message.emit(self.tr("Запросы не найдены"))

    def _update_filters(self, models: list[MatchFilterDBModel]) -> None:
        self._filters.clear()

        for index, obj in enumerate(models):
            self._filters.addItem(obj.id, obj)
            self._filters.setItemData(index, obj.description, Qt.ItemDataRole.ToolTipRole)

        self._filters.addItem(self.tr("Отсутствует"), None)
