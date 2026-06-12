import logging
from typing import Optional

from PySide6.QtCore import Signal as pysideSignal, QPoint, QStandardPaths, QSize, Slot
from PySide6.QtGui import QIcon, Qt, QPalette, QColor
from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QMenu,
    QFileDialog,
    QFrame,
    QDialog, QScrollArea
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
    get_risk_name,
    get_signal_type_name,
    get_driver_name,
    CheckPoint
)

from src.dialogs.chat import ChatDialog
from src.dialogs.match import MatchDetailsDialog
from src.layouts.flow import FlowLayout
from src.utils.blocker import WheelBlocker
from src.utils.button import create_icon_push_button
from src.utils.lang import AppLang
from src.utils.service import SportEventService
from src.widgets.color import ColorWidget

_logger = logging.getLogger(__name__)


class SignalBorder(QFrame):
    update_progress = pysideSignal(int, int)
    show_message = pysideSignal(str)
    print_text = pysideSignal(str)

    update_tab_widget = pysideSignal(bool)

    _show_match_dialog = pysideSignal(DriverCode, MatchDetails)

    def __init__(self, service: SportEventService, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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
        widget.print_text.connect(self.print_text.emit)
        widget.show_update_match.connect(self._get_match)
        self._signal_layout.addWidget(widget)

        self.update_tab_widget.emit(bool(self._signal_layout.count()))

    @Slot()
    def evaluated_signal(self, signal: Signal, match_details: MatchDetails, driver_code: DriverCode) -> None:
        """
        Предсказать сигнал.

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
            self.evaluated_signal(signal, match_details, driver_code)

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


class SignalWidget(QFrame):
    """
    Виджет сигнала
    """
    delete_signal = pysideSignal(str, DriverCode)
    print_text = pysideSignal(str)
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
            color=QColor(60, 65, 75),
            parent=self
        )

        self._score_label = QLabel()

        self._top_widget.central_layout.addWidget(self._score_label, alignment=Qt.AlignmentFlag.AlignRight)

        center_layout = QFormLayout()
        center_layout.setHorizontalSpacing(25)
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
        if signal.signal_property.bet.odds:
            center_layout.addRow(self.tr("Коэффициенты:"), QLabel(f"{signal.signal_property.bet.get_odds_reports()}"))
        else:
            center_layout.addRow(self.tr("Коэффициенты:"), QLabel(self.tr("Нет данных")))

        if signal.metric:
            center_layout.addRow(self.tr("Метрика:"), QLabel(f"{signal.metric}"))
        else:
            center_layout.addRow(self.tr("Метрика:"), QLabel(self.tr("Нет данных")))

        if signal.signal_property.bet.probabilities:
            center_layout.addRow(
                self.tr("Вероятности:"),
                QLabel(f"{signal.signal_property.bet.get_probability_reports(AppLang.code)}")
            )
        else:
            center_layout.addRow(self.tr("Вероятности:"), QLabel(self.tr("Нет данных")))

        if signal.recommendation:
            self._info = create_icon_push_button(
                icon=QIcon(":/resources/icons/info.png"),
                tooltip=self.tr("Информация"),
                parent=self
            )
            self._info.clicked.connect(self._show_recommendation_info)

            self._top_widget.central_layout.addWidget(self._info, alignment=Qt.AlignmentFlag.AlignRight)
            value = QLabel(f"{get_risk_name(signal.recommendation.risk_code, AppLang.code)}")
            center_layout.addRow(QLabel(self.tr("Риск:")), value)

        layout.addWidget(self._top_widget)
        layout.addLayout(center_layout)

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
    def text(self) -> str:
        return format_signal(self._signal, self._match_details, AppLang.code)

    @Slot()
    def show_context_menu(self, position: QPoint) -> None:
        menu = QMenu(self)

        screen = menu.addAction(QIcon(":/resources/icons/screen.png"), self.tr("Сохранить карточку"))
        delete = menu.addAction(QIcon(":/resources/icons/delete.png"), self.tr("Удалить"))
        print_data = menu.addAction(QIcon(":/resources/icons/console.png"), self.tr("Вывести в консоль"))
        show_match = menu.addAction(QIcon(":/resources/icons/info.png"), self.tr("Показать матч"))

        if self._signal.recommendation and self._signal.recommendation.messages:
            menu.addSeparator()
            show_dialog = menu.addAction(QIcon(":/resources/icons/dialog.png"), self.tr("Показать чат"))
            show_dialog.triggered.connect(self._show_dialog)

        screen.triggered.connect(self._save_screen)
        delete.triggered.connect(self._delete)
        print_data.triggered.connect(self._print_data)
        show_match.triggered.connect(self._show_match)

        menu.exec(self.mapToGlobal(position))

    @Slot()
    def _delete(self) -> None:
        self.delete_signal.emit(self.signal_id, self._driver_code)

    @Slot()
    def _print_data(self) -> None:
        self.print_text.emit(f"{self.text}")

    @Slot()
    def _show_match(self) -> None:
        if self._match_details.match.match_summary.match_status_code == MatchStatusCode.COMPLETED:
            dialog = MatchDetailsDialog(self._driver_code, [self._match_details])
            dialog.exec()
        else:
            self.show_update_match.emit(self._match_details.match.match_id, self._driver_code)

    @Slot()
    def _save_screen(self) -> None:
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("Сохранить изображение"),
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;BMP Image (*.bmp);;All Files (*)"
        )

        if file_path:
            pixmap = self.grab()

            try:
                pixmap.save(file_path)
            except Exception as exception:
                _logger.exception(exception)

    @Slot()
    def _show_dialog(self) -> None:
        dialog = ChatDialog(self._signal.recommendation.messages, parent=self)
        dialog.exec()

    @Slot()
    def _show_recommendation_info(self) -> None:
        popup = QDialog(self, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        layout = QVBoxLayout(popup)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(QLabel(self._signal.recommendation.conclusion, wordWrap=True))
        layout.addWidget(QLabel(self._signal.recommendation.alternative, wordWrap=True))

        global_pos = self._info.mapToGlobal(QPoint(0, -popup.sizeHint().height()))
        popup.move(global_pos)
        popup.exec()

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
            palette.setColor(QPalette.ColorRole.Window, QColor(70, 130, 45))
        elif forecast_code == ForecastCode.UNSUCCESSFUL:
            palette.setColor(QPalette.ColorRole.Window, QColor(140, 65, 60))
        elif forecast_code == ForecastCode.REFUND:
            palette.setColor(QPalette.ColorRole.Window, QColor(60, 95, 135))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor(60, 65, 75))

        self._top_widget.setPalette(palette)

        if forecast_code == ForecastCode.UNDEFINED:
            self._score_label.setText(self.tr("Отмена сигнала"))
        else:
            home_score = match_details.match.match_summary.home_team_score
            away_score = match_details.match.match_summary.away_team_score
            if home_score is not None and away_score is not None:
                self._score_label.setText(self.tr("Счет {}:{}").format(home_score, away_score))
