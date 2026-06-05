from typing import Optional, Callable

from PySide6.QtCore import QThread, QSize
from PySide6.QtGui import QIcon, QAction, Qt, QScreen
from PySide6.QtWidgets import QPlainTextEdit, QLabel, QWidget, QSizePolicy, QComboBox, QFormLayout, QHBoxLayout, \
    QStackedLayout, QApplication
from betsys import DBContext, MatchCode, MatchDetails, DriverCode, get_driver_name
from qasync import asyncSlot

from src.dialogs.base import BaseDialog
from src.dialogs.dao import BaseDAODialog
from src.utils.cache import DataCache
from src.utils.forecast import Forecast
from src.utils.lang import AppLang
from src.utils.worker import Worker
from src.widgets.match import MatchDetailsWidget
from src.widgets.switch import Switch


class MatchDetailsDAODialog(BaseDAODialog):

    def __init__(self, db_context: DBContext, *args, **kwargs) -> None:
        super().__init__(
            db_context,
            QPlainTextEdit,
            self.tr("БД Матчи"),
            QIcon(":/resources/icons/dao.png"),
            *args,
            **kwargs
        )
        self.central_widget.setReadOnly(True)

        self._clear_action = QAction(
            QIcon(":/resources/icons/delete.png"),
            self.tr("Очистить"),
            self
        )

        self._run_analyze = QAction(
            QIcon(":/resources/icons/run.png"),
            self.tr("Запустить анализ"),
            self
        )

        self._update_action = QAction(
            QIcon(":/resources/icons/update.png"),
            self.tr("Обновить"),
            self
        )

        self._scripts = QComboBox(self)

        self.toolbar.addAction(self._run_analyze)
        self.toolbar.addAction(self._clear_action)
        self.toolbar.addAction(self._update_action)

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

        self._in_memory = Switch(size=QSize(40, 20), checked=True, parent=self)

        self._memory_widget = QWidget()
        memory_layout = QHBoxLayout(self._memory_widget)
        memory_layout.addWidget(QLabel(self.tr("Хранить данные в памяти:")))
        memory_layout.addWidget(self._in_memory)

        self.toolbar.addWidget(self._memory_widget)

        self._forecast = Forecast(self)
        self._forecast.update_progress.connect(self._update_progress)
        self._forecast.send_message.connect(self.central_widget.appendPlainText)

        self._thread = QThread()
        self._worker = Worker(self._thread)

        self._run_analyze.triggered.connect(self.run)
        self._clear_action.triggered.connect(self.central_widget.clear)
        self._update_action.triggered.connect(self.start_update.emit)

        self._weekdays_info = Switch(size=QSize(50, 25), checked=False, parent=self)
        self._leagues_info = Switch(size=QSize(50, 25), checked=False, parent=self)

        self._layout = QFormLayout()
        self._layout.setSpacing(15)
        self._layout.addRow(self.tr("Сценарий:"), self._scripts)
        self._layout.addRow(self.tr("Информация по дням недели:"), self._weekdays_info)
        self._layout.addRow(self.tr("Информация по лигам:"), self._leagues_info)

        self.central_layout.addLayout(self._layout)

        self.start_update.connect(self.update_widget)

        self.start_update.emit()

    def started(self) -> None:
        super().started()

        self._scripts.setEnabled(False)
        self._weekdays_info.setEnabled(False)
        self._leagues_info.setEnabled(False)
        self._memory_widget.setEnabled(False)

    def finished(self) -> None:
        super().finished()

        self._scripts.setEnabled(True)
        self._weekdays_info.setEnabled(True)
        self._leagues_info.setEnabled(True)
        self._memory_widget.setEnabled(True)

    def _start_thread(self, callback: Optional[Callable], func: Callable, *args) -> None:
        if not self._worker.is_running:
            self._worker.start(callback, func, *args)
        else:
            self.show_message(self.tr("Дождитесь завершения предыдущего действия"))

    @asyncSlot()
    async def update_widget(self, batch_size: int = 10) -> None:
        self.started()

        self._scripts.clear()
        self.central_widget.clear()

        self.central_widget.appendPlainText(self.tr("Подготовка данных к анализу ..."))

        icons = {
            MatchCode.FOOTBALL: QIcon(":/resources/icons/football.png"),
            MatchCode.HOCKEY: QIcon(":/resources/icons/hockey.png"),
            MatchCode.VOLLEYBALL: QIcon(":/resources/icons/volleyball.png"),
        }

        scripts = await self.get_scripts(batch_size)
        for index, script in enumerate(scripts):
            self._scripts.addItem(icons.get(script.match_code), script.id, script)
            self._scripts.setItemData(index, script.description, Qt.ItemDataRole.ToolTipRole)
            self.central_widget.appendPlainText(
                self.tr("Загружен сценарий: {} - {}").format(script.id, script.description)
            )

        self._scripts.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._run_analyze.setEnabled(bool(scripts))
        self._scripts.setEnabled(bool(scripts))

        self.finished()

        self.show_message(self.tr("Данные обновлены"))

    @asyncSlot()
    async def run(self, batch_size: int = 250) -> None:
        if self._scripts.currentData():
            self.started()

            if not DataCache.matches:
                DataCache.matches = await self.get_matches(batch_size)

            if not DataCache.leagues:
                DataCache.leagues = await self.get_leagues(batch_size)

            self._start_thread(
                self._finished,
                self._forecast.run,
                self._scripts.currentData(),
                self._weekdays_info.is_checked(),
                self._leagues_info.is_checked(),
                self._in_memory.is_checked()
            )
        else:
            self.show_message(self.tr("Сценарий не выбран"))

    def _finished(self) -> None:
        self.finished()
        self.show_message(self.tr("Анализ сценария завершен"))


class MatchDetailsDialog(BaseDialog):
    def __init__(self, driver_code: DriverCode, matches: list[MatchDetails], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setGeometry(0, 0, 800, 600)

        geo = self.frameGeometry()
        geo.moveCenter(QScreen.availableGeometry(QApplication.primaryScreen()).center())
        self.move(geo.topLeft())

        if driver_code == DriverCode.FOOTBALL:
            self.setWindowIcon(QIcon(":/resources/icons/football.png"))
        elif driver_code == DriverCode.HOCKEY:
            self.setWindowIcon(QIcon(":/resources/icons/hockey.png"))
        else:
            self.setWindowIcon(QIcon(":/resources/icons/volleyball.png"))

        self.setWindowTitle(get_driver_name(driver_code, AppLang.code))

        self._box = QComboBox(self)
        self._box.addItems([match.match.match_id for match in matches])
        self._box.currentIndexChanged.connect(self._changed)

        self._stacked_layout = QStackedLayout()
        for match in matches:
            widget = MatchDetailsWidget(match, parent=self)
            self._stacked_layout.addWidget(widget)

        layout = QFormLayout(self)
        layout.addRow(self.tr("Идентификатор матча:"), self._box)
        layout.addRow(self._stacked_layout)

    def _changed(self, index: int) -> None:
        self._stacked_layout.setCurrentIndex(index)
