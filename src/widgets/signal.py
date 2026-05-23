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
    QDialog
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
    get_signal_type_name
)

from src.dialogs.chat import ChatDialog
from src.utils.blocker import WheelBlocker
from src.utils.button import create_icon_push_button
from src.utils.lang import AppLang
from src.widgets.color import ColorWidget

_logger = logging.getLogger(__name__)


class SignalWidget(QFrame):
    """
    Виджет сигнала
    """
    delete_signal = pysideSignal(str, DriverCode)
    print_text = pysideSignal(str)

    def __init__(
            self,
            signal: Signal,
            match_details: MatchDetails,
            driver_code: DriverCode,
            parent: Optional[QWidget] = None,
            *args, **kwargs
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
        if match_details.match.match_summary.match_status_code == MatchStatusCode.IN_PROGRESS:
            self._score_label.setText(
                self.tr("Счет {}:{}").format(
                    match_details.match.match_summary.home_team_score,
                    match_details.match.match_summary.away_team_score
                )
            )

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

        if self._signal.recommendation and self._signal.recommendation.messages:
            menu.addSeparator()
            show_dialog = menu.addAction(QIcon(":/resources/icons/dialog.png"), self.tr("Показать чат"))
            show_dialog.triggered.connect(self._show_dialog)

        screen.triggered.connect(self._save_screen)
        delete.triggered.connect(self._delete)
        print_data.triggered.connect(self._print_data)

        menu.exec(self.mapToGlobal(position))

    @Slot()
    def _delete(self) -> None:
        self.delete_signal.emit(self.signal_id, self._driver_code)
        self.deleteLater()

    @Slot()
    def _print_data(self) -> None:
        self.print_text.emit(f"{self.text}\n")

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
            self._score_label.setText(
                self.tr("Счет {}:{}").format(
                    match_details.match.match_summary.home_team_score,
                    match_details.match.match_summary.away_team_score
                )
            )
