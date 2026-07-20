import logging
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Signal as pysideSignal, QPoint, QSize, Slot
from PySide6.QtGui import QIcon, Qt, QPalette
from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QMenu,
    QFrame,
    QScrollArea
)
from betsys import (
    Signal,
    MatchDetails,
    MatchCode,
    DriverCode,
    ForecastCode,
    get_priority_name,
    MatchStatusCode,
    format_signal,
    get_signal_type_name,
    get_driver_name,
    CheckPoint,
    EventCode,
    SportEventDriver,
    get_global_event_status_name
)
from qasync import asyncSlot

from src.dialogs.chat import ChatDialog
from src.dialogs.market import StackedMarketDialog
from src.dialogs.match import MatchDetailsDialog
from src.layouts.flow import FlowLayout
from src.utils.blocker import WheelBlocker
from src.utils.color import GREEN, RED, BLUE, YELLOW, GRAPHITE
from src.utils.lang import AppLang
from src.utils.service import SportEventService
from src.widgets.color import ColorWidget

_logger = logging.getLogger(__name__)


class SignalBorder(QFrame):
    update_progress = pysideSignal(int, int)
    show_message = pysideSignal(str)
    print_text = pysideSignal(str)

    event = pysideSignal(EventCode, Signal, MatchDetails, DriverCode)

    update_tab_widget = pysideSignal(bool)

    _show_match_dialog = pysideSignal(DriverCode, MatchDetails)

    def __init__(self, service: SportEventService, parent: QWidget = Optional[None], *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self._service = service

        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()

        self._signal_layout = FlowLayout(container)
        self._signal_layout.setContentsMargins(10, 10, 10, 10)
        self._signal_layout.setSpacing(25)

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

        self._show_match_dialog.connect(self._show_match)
        self.event.connect(self.event_signal)

    @Slot()
    def event_signal(
            self,
            event_code: EventCode,
            signal: Signal,
            details: MatchDetails,
            driver_code: DriverCode
    ) -> None:
        if event_code == EventCode.CREATED:
            self.add_signal(signal, details, driver_code)
        elif event_code == EventCode.COMPLETED:
            self.complete_signal(signal, details, driver_code)
        elif event_code == EventCode.DELETED:
            self.delete_signal(signal, details, driver_code)
        elif event_code == EventCode.UPDATED:
            self.update_signal(signal, details, driver_code)
        elif event_code == EventCode.RESUMED:
            self.resume_signal(signal, details, driver_code)

    @Slot()
    def add_signal(self, signal: Signal, match_details: MatchDetails, driver_code: DriverCode) -> None:
        """
        Добавить сигнал.

        :param signal: Сигнал.
        :param match_details: Детали матча.
        :param driver_code: Код драйвера.
        """
        widget = SignalWidget(signal, match_details, driver_code, self)
        widget.delete_signal.connect(self._delete_signal)
        widget.invert_signal.connect(self.invert_signal)
        widget.print_text.connect(self.print_text.emit)
        widget.print_prompts.connect(self._print_prompts_signal)
        widget.show_update_match.connect(self._get_match)
        widget.run_analyse.connect(self.run_analyse_signal)
        self._signal_layout.addWidget(widget)

        self.update_tab_widget.emit(bool(self._signal_layout.count()))

    @Slot()
    def update_signal(self, signal: Signal, match_details: MatchDetails, driver_code: DriverCode) -> None:
        for index in range(self._signal_layout.count()):
            item = self._signal_layout.itemAt(index)
            widget = item.widget()
            if isinstance(widget, SignalWidget):
                if signal.signal_id == widget.signal_id:
                    widget.update_data(signal, match_details)
                    break

    @Slot()
    def resume_signal(self, signal: Signal, match_details: MatchDetails, driver_code: DriverCode) -> None:
        for index in range(self._signal_layout.count()):
            item = self._signal_layout.itemAt(index)
            widget = item.widget()
            if isinstance(widget, SignalWidget):
                if signal.signal_id == widget.signal_id:
                    widget.resume_data(signal, match_details)
                    break

    @Slot()
    def complete_signal(self, signal: Signal, match_details: MatchDetails, driver_code: DriverCode) -> None:
        """
        Завершить сигнал.

        :param signal: Сигнал.
        :param match_details: Детали матча.
        :param driver_code: Код драйвера.
        """
        is_check = False
        for index in range(self._signal_layout.count()):
            item = self._signal_layout.itemAt(index)
            widget = item.widget()
            if isinstance(widget, SignalWidget):
                if signal.signal_id == widget.signal_id:
                    widget.forecast(signal, match_details)

                    is_check = True
                    break

        if not is_check:
            self.add_signal(signal, match_details, driver_code)
            self.complete_signal(signal, match_details, driver_code)

    @Slot()
    def _delete_signal(self, signal_id: str, driver_code: DriverCode) -> None:
        self._service.remove_signal(signal_id, driver_code)

        for index in range(self._signal_layout.count()):
            item = self._signal_layout.itemAt(index)
            widget = item.widget()
            if isinstance(widget, SignalWidget):
                if signal_id == widget.signal_id:
                    self._signal_layout.takeAt(index)
                    widget.deleteLater()

                    self._signal_layout.invalidate()
                    self._signal_layout.update()
                    self._signal_layout.activate()

                    break

        self.show_message.emit(
            self.tr("Сигнал драйвера «{}» удален").format(get_driver_name(driver_code, AppLang.code))
        )

        self.update_tab_widget.emit(bool(self._signal_layout.count()))

    @Slot()
    def delete_signal(self, signal: Signal, match_details: MatchDetails, driver_code: DriverCode) -> None:
        """
        Удалить сигнал.

        :param signal: Сигнал.
        :param match_details: Детали матча.
        :param driver_code: Код драйвера.
        """
        for index in range(self._signal_layout.count()):
            item = self._signal_layout.itemAt(index)
            widget = item.widget()
            if isinstance(widget, SignalWidget):
                if signal.signal_id == widget.signal_id:
                    self._signal_layout.takeAt(index)
                    widget.deleteLater()

                    self._signal_layout.invalidate()
                    self._signal_layout.update()
                    self._signal_layout.activate()

                    self.show_message.emit(
                        self.tr("Сигнал драйвера «{}» удален").format(get_driver_name(driver_code, AppLang.code))
                    )

                    break

        self.update_tab_widget.emit(bool(self._signal_layout.count()))

    @Slot()
    def remove_finished_signals(self) -> None:
        self._service.fing_signal_ids(self._remove_non_active_signals)

    @Slot()
    def print_signals(self) -> None:
        if self._signal_layout.items:
            for item in self._signal_layout.items[:]:
                widget = item.widget()
                if isinstance(widget, SignalWidget):
                    self.print_text.emit(f"{widget.text}")

            self.show_message.emit(self.tr(f"Информация выведена в консоль"))
        else:
            self.show_message.emit(self.tr(f"Сигналы не найдены"))

    @Slot()
    def invert_signal(self, signal_id: str, driver_code: DriverCode) -> None:
        def _check(flag: bool) -> None:
            if flag:
                self.show_message.emit(self.tr("Сигнал (id={}) инвертирован").format(signal_id))
            else:
                self.show_message.emit(self.tr("Не удалось инвертировать сигнал (id={})").format(signal_id))

        self._service.get_object(
            _check,
            driver_code,
            SportEventDriver.__name__,
            SportEventDriver.invert_signal.__name__,
            signal_id
        )

    @Slot()
    def run_analyse_signal(self, signal_id: Signal, driver_code: DriverCode) -> None:
        def _check(flag: bool) -> None:
            if flag:
                self.show_message.emit(self.tr("Сигнал (id={}) - анализ завершен").format(signal_id))
            else:
                self.show_message.emit(self.tr("Не удалось проанализировать сигнал (id={})").format(signal_id))

        self._service.get_object(
            _check,
            driver_code,
            SportEventDriver.__name__,
            SportEventDriver.generate_assistant_response.__name__,
            signal_id
        )

    def _remove_non_active_signals(self, signal_ids: list[str]) -> None:
        """
        Удалить завершенные сигналы.
        """
        if signal_ids:
            items = self._signal_layout.items[:]
            for index, item in enumerate(items, start=1):
                widget = item.widget()
                if isinstance(widget, SignalWidget):
                    if widget.signal_id not in signal_ids:
                        self._signal_layout.items.remove(item)
                        widget.setVisible(False)
                        widget.deleteLater()

                        self._signal_layout.invalidate()
                        self._signal_layout.update()
                        self._signal_layout.activate()

                self.update_progress.emit(index, len(items))

            self.show_message.emit(self.tr(f"Сигналы завершенных матчей удалены"))
        else:
            if self._signal_layout.items:
                self._signal_layout.clear()

            self.show_message.emit(self.tr(f"Сигналы не найдены"))

        self.update_tab_widget.emit(bool(self._signal_layout.count()))

    @Slot()
    def _get_match(self, match_id: str, driver_code: DriverCode) -> None:
        def _show_dialog(match_details: MatchDetails) -> None:
            self._show_match_dialog.emit(driver_code, match_details)

        self._service.get_object(
            _show_dialog,
            driver_code,
            CheckPoint.__name__,
            CheckPoint.get_match_details.__name__,
            match_id
        )

    @Slot()
    def _show_match(self, driver_code: DriverCode, match_details: MatchDetails) -> None:
        dialog = MatchDetailsDialog(driver_code, [match_details])
        dialog.exec()

    @asyncSlot()
    async def _print_prompts_signal(self, signal: Signal, match_details: MatchDetails) -> None:
        self.update_progress.emit(1, 1)

        prompts = await self._service.db_context.prompts.get_prompts(
            signal.signal_property.bet.bet_code,
            match_details.match.match_code,
            signal.signal_property.signal_type_code
        )

        for index, model in enumerate(prompts, start=1):
            prompt = model.generate_prompt(match_details, signal, AppLang.code)
            self.print_text.emit(f"#{index}\n{prompt}")

            self.update_progress.emit(index, len(prompts))


class SignalWidget(QFrame):
    """
    Виджет сигнала
    """
    delete_signal = pysideSignal(str, DriverCode)
    invert_signal = pysideSignal(str, DriverCode)

    print_text = pysideSignal(str)
    print_prompts = pysideSignal(Signal, MatchDetails)
    run_analyse = pysideSignal(str, DriverCode)
    show_update_match = pysideSignal(str, DriverCode)

    def __init__(
            self,
            signal: Signal,
            match_details: MatchDetails,
            driver_code: DriverCode,
            parent: Optional[QWidget] = None,
            *args,
            **kwargs
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        self._signal = signal
        self._match_details = match_details

        self._driver_code = driver_code

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)

        self.wheel_blocker = WheelBlocker()

        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        if match_details.match.match_code == MatchCode.FOOTBALL:
            icon = QIcon(":/resources/icons/football.png")
        elif match_details.match.match_code == MatchCode.HOCKEY:
            icon = QIcon(":/resources/icons/hockey.png")
        else:
            icon = QIcon(":/resources/icons/volleyball.png")

        self._top_widget = ColorWidget(
            title=match_details.match.match_summary.match_datetime.strftime("%d.%m.%Y - %H:%M"),
            icon=icon,
            icon_size=QSize(45, 45),
            color=GRAPHITE,
            parent=self
        )

        self._status_label = QLabel()

        center_layout = QFormLayout()
        center_layout.setHorizontalSpacing(25)
        center_layout.addRow(self.tr("Статус матча:"), self._status_label)
        center_layout.addRow(
            self.tr("Тип сигнала:"),
            QLabel(get_signal_type_name(signal.signal_property.signal_type_code, AppLang.code))
        )
        center_layout.addRow(
            self.tr("Приоритет:"),
            QLabel(get_priority_name(signal.signal_property.priority_code, AppLang.code))
        )
        center_layout.addRow(self.tr("Страна:"), QLabel(match_details.match.league.country_name.capitalize()))
        center_layout.addRow(self.tr("Лига:"), QLabel(match_details.match.league.league_name))
        center_layout.addRow(self.tr("Хозяева:"), QLabel(match_details.match.home_team.name))
        center_layout.addRow(self.tr("Гости:"), QLabel(match_details.match.away_team.name))
        center_layout.addRow(
            self.tr("Ставка:"),
            QLabel(f"{signal.signal_property.bet.format_reports(True, AppLang.code)}")
        )

        if signal.metric:
            center_layout.addRow(self.tr("Метрика:"), QLabel(f"{signal.metric}"))
        else:
            center_layout.addRow(self.tr("Метрика:"), QLabel(self.tr("Нет данных")))

        if signal.signal_property.bet.odds:
            center_layout.addRow(self.tr("Коэффициенты:"), QLabel(f"{signal.signal_property.bet.get_odds_reports()}"))
        else:
            center_layout.addRow(self.tr("Коэффициенты:"), QLabel(self.tr("Нет данных")))

        if signal.signal_property.bet.probabilities:
            center_layout.addRow(
                self.tr("Вероятности:"),
                QLabel(f"{signal.signal_property.bet.get_probability_reports(AppLang.code)}")
            )
        else:
            center_layout.addRow(self.tr("Вероятности:"), QLabel(self.tr("Нет данных")))

        layout.addWidget(self._top_widget)
        layout.addLayout(center_layout)

        self._set_status(match_details)

    @property
    def signal_id(self) -> str:
        return self._signal.signal_id

    @property
    def driver_code(self) -> DriverCode:
        return self._driver_code

    @property
    def is_active(self) -> bool:
        return self._signal.is_active

    @property
    def datetime(self) -> datetime:
        return self._match_details.match.match_summary.match_datetime

    @property
    def text(self) -> str:
        return format_signal(self._signal, self._match_details, AppLang.code)

    @Slot()
    def show_context_menu(self, position: QPoint) -> None:
        menu = QMenu(self)

        delete = menu.addAction(QIcon(":/resources/icons/delete.png"), self.tr("Удалить"))
        print_data = menu.addAction(QIcon(":/resources/icons/console.png"), self.tr("Вывести сигнал в консоль"))
        menu.addSeparator()
        show_match = menu.addAction(QIcon(":/resources/icons/info.png"), self.tr("Показать матч"))
        show_market = menu.addAction(QIcon(":/resources/icons/info.png"), self.tr("Показать коэффициенты"))
        if self._signal.is_active:
            menu.addSeparator()
            invert_signal = menu.addAction(QIcon(":/resources/icons/invert.png"), self.tr("Инвертировать сигнал"))
            invert_signal.triggered.connect(self._invert_signal)

        menu.addSeparator()

        run_assistant = menu.addAction(QIcon(":/resources/icons/run.png"), self.tr("Запустить анализ ИИ"))
        run_assistant.triggered.connect(self._run_analyse)

        print_prompts = menu.addAction(QIcon(":/resources/icons/console.png"), self.tr("Вывести запросы в консоль"))
        print_prompts.triggered.connect(self._print_prompts)

        menu.addSeparator()
        show_dialog = menu.addAction(QIcon(":/resources/icons/dialog.png"), self.tr("Показать чат"))
        show_dialog.triggered.connect(self._show_dialog)

        delete.triggered.connect(self._delete)
        print_data.triggered.connect(self._print_data)
        show_match.triggered.connect(self._show_match)
        show_market.triggered.connect(self._show_market)

        menu.exec(self.mapToGlobal(position))

    @Slot()
    def _invert_signal(self) -> None:
        self.invert_signal.emit(self.signal_id, self._driver_code)

    @Slot()
    def _delete(self) -> None:
        self.delete_signal.emit(self.signal_id, self._driver_code)

    @Slot()
    def _print_data(self) -> None:
        self.print_text.emit(f"{self.text}")

    @Slot()
    def _print_prompts(self) -> None:
        self.print_prompts.emit(self._signal, self._match_details)

    @Slot()
    def _show_match(self) -> None:
        if self._match_details.match.match_summary.match_status_code == MatchStatusCode.COMPLETED:
            dialog = MatchDetailsDialog(self._driver_code, [self._match_details], self)
            dialog.exec()
        else:
            self.show_update_match.emit(self._match_details.match.match_id, self._driver_code)

    @Slot()
    def _show_market(self) -> None:
        dialog = StackedMarketDialog([self._match_details], self)
        dialog.exec()

    @Slot()
    def _show_dialog(self) -> None:
        dialog = ChatDialog(self._signal.messages, parent=self)
        dialog.exec()

    @Slot()
    def _run_analyse(self) -> None:
        self.run_analyse.emit(self._signal.signal_id, self.driver_code)

    def _set_status(self, match_details: MatchDetails) -> None:
        status = get_global_event_status_name(match_details.match.match_summary.event_status_code, AppLang.code)

        home_score = match_details.match.match_summary.home_team_score
        away_score = match_details.match.match_summary.away_team_score
        if home_score is not None and away_score is not None:
            score = f" {home_score}:{away_score}"
        else:
            score = ""

        if match_details.match.match_summary.current_time != -1:
            current_time = f" ({match_details.match.match_summary.current_time}\')"
        else:
            current_time = ""

        self._status_label.setText(f"{status}{score}{current_time}")

    def update_data(self, signal: Signal, match_details: MatchDetails) -> None:
        self._signal = signal
        self._match_details = match_details

        self._set_status(match_details)

    def resume_data(self, signal: Signal, match_details: MatchDetails) -> None:
        self._signal = signal
        self._match_details = match_details

        self._set_status(match_details)

        palette = self._top_widget.palette()
        palette.setColor(QPalette.ColorRole.Window, GRAPHITE)

        self._top_widget.setPalette(palette)

    def forecast(self, signal: Signal, match_details: MatchDetails) -> None:
        """
        Результат.

        :param signal: Сигнал.
        :param match_details: История игры.
        """
        self._signal = signal
        self._match_details = match_details

        palette = self._top_widget.palette()

        forecast_code = signal.signal_property.forecast(match_details.match)
        if forecast_code == ForecastCode.SUCCESSFUL:
            palette.setColor(QPalette.ColorRole.Window, GREEN)
        elif forecast_code == ForecastCode.UNSUCCESSFUL:
            palette.setColor(QPalette.ColorRole.Window, RED)
        elif forecast_code == ForecastCode.REFUND:
            palette.setColor(QPalette.ColorRole.Window, BLUE)
        else:
            palette.setColor(QPalette.ColorRole.Window, YELLOW)

        self._top_widget.setPalette(palette)

        self._set_status(match_details)
