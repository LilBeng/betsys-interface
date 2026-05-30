import ctypes
import logging
from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QByteArray, Slot, QPoint, QThread, QSize
from PySide6.QtGui import QIcon, QCloseEvent, QScreen
from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QProgressBar,
    QMenu,
    QApplication,
    QMessageBox,
    QTabWidget
)
from betsys import (
    __version__,
    DBContext,
    MultiDriverConfig,
    DriverCode,
    SportEventDriver
)

from src import ERRORS, DISPLAY
from src.utils.button import create_icon_push_button
from src.utils.cache import DataCache
from src.utils.service import SportEventService
from src.utils.worker import Worker
from src.widgets.console import ConsoleWidget
from src.widgets.driver import DriverToolBar
from src.widgets.logger import LogWidget
from src.widgets.signal import SignalBorder

_logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Главное окно.
    """

    def __init__(
            self,
            db_context: DBContext,
            multi_driver_config: MultiDriverConfig,
            only_database: bool,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        if only_database:
            self.setWindowTitle(f"Betting System [BetSys v.{__version__}] - Database")
        else:
            self.setWindowTitle(f"Betting System [BetSys v.{__version__}] - Client")
        self.setWindowIcon(QIcon(":/resources/icons/bet_sys.png"))

        self.setGeometry(0, 0, 800, 600)

        geo = self.frameGeometry()
        geo.moveCenter(QScreen.availableGeometry(QApplication.primaryScreen()).center())
        self.move(geo.topLeft())

        self.status_bar = self.statusBar()

        self.progress = QProgressBar(self)
        self.progress.setVisible(False)

        self._show_dialog = create_icon_push_button(
            icon=QIcon(":/resources/icons/config.png"),
            tooltip=self.tr("Кэш памяти"),
            parent=self
        )
        self._show_dialog.setFlat(True)
        self._show_dialog.clicked.connect(self.show_cache_dialog)

        self.status_bar.addPermanentWidget(self.progress)
        self.status_bar.addPermanentWidget(self._show_dialog)

        self.menu_bar = self.menuBar()

        self.driver_tool_bar = DriverToolBar(only_database, parent=self)
        self.addToolBar(self.driver_tool_bar)

        # self.container = BorderWidget(self)
        # if not only_database:
        #     self.container.customContextMenuRequested.connect(self.show_context_menu)
        #     self.container.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # self._scroll = QScrollArea()
        # self._scroll.setWidget(self.container)
        # self._scroll.setWidgetResizable(True)

        log_widget = LogWidget(500, ERRORS, parent=self)
        self.log_dock = QDockWidget(self.tr("Журнал"), self)
        self.log_dock.setObjectName("logging")
        self.log_dock.setWindowIcon(QIcon(":/resources/icons/log.png"))
        self.log_dock.setWidget(log_widget)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.log_dock)

        if not only_database:
            self.console_widget = ConsoleWidget(self)
            self.console_dock = QDockWidget(self.tr("Консоль"), self)
            self.console_dock.setObjectName("console")
            self.console_dock.setWindowIcon(QIcon(":/resources/icons/console.png"))
            self.console_dock.setWidget(self.console_widget)

            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.console_dock)

            self.tabifyDockWidget(self.log_dock, self.console_dock)
            self.log_dock.raise_()
        else:
            self.tabifiedDockWidgets(self.log_dock)

        view = self.menu_bar.addMenu(self.tr("Вид"))
        if only_database:
            view.addActions(
                [
                    self.log_dock.toggleViewAction(),
                    view.addSeparator(),
                    self.driver_tool_bar.toggleViewAction(),
                ]
            )
        else:
            view.addActions(
                [
                    self.console_dock.toggleViewAction(),
                    self.log_dock.toggleViewAction(),
                    view.addSeparator(),
                    self.driver_tool_bar.toggleViewAction()
                ]
            )

        football = self.menu_bar.addMenu(self.tr("Футбол"))
        if only_database:
            football.addActions(
                [
                    self.driver_tool_bar.football_download
                ]
            )
        else:
            football.addActions(
                [
                    self.driver_tool_bar.football_config,
                    football.addSeparator(),
                    self.driver_tool_bar.football_info,
                    football.addSeparator(),
                    self.driver_tool_bar.football_download,
                    football.addSeparator(),
                    self.driver_tool_bar.football_run,
                    self.driver_tool_bar.football_run_with_checkpoint,
                    football.addSeparator(),
                    self.driver_tool_bar.football_stop,
                    self.driver_tool_bar.football_stop_with_checkpoint,
                    football.addSeparator(),
                    self.driver_tool_bar.football_update_scripts,
                    self.driver_tool_bar.football_update_leagues
                ]
            )
        hockey = self.menu_bar.addMenu(self.tr("Хоккей"))
        if only_database:
            hockey.addActions(
                [
                    self.driver_tool_bar.hockey_download,
                ]
            )
        else:
            hockey.addActions(
                [
                    self.driver_tool_bar.hockey_config,
                    hockey.addSeparator(),
                    self.driver_tool_bar.hockey_info,
                    hockey.addSeparator(),
                    self.driver_tool_bar.hockey_download,
                    hockey.addSeparator(),
                    self.driver_tool_bar.hockey_run,
                    self.driver_tool_bar.hockey_run_with_checkpoint,
                    hockey.addSeparator(),
                    self.driver_tool_bar.hockey_stop,
                    self.driver_tool_bar.hockey_stop_with_checkpoint,
                    hockey.addSeparator(),
                    self.driver_tool_bar.hockey_update_scripts,
                    self.driver_tool_bar.hockey_update_leagues
                ]
            )

        volleyball = self.menu_bar.addMenu(self.tr("Волейбол"))
        if only_database:
            volleyball.addActions(
                [
                    self.driver_tool_bar.volleyball_download,
                ]
            )
        else:
            volleyball.addActions(
                [
                    self.driver_tool_bar.volleyball_config,
                    volleyball.addSeparator(),
                    self.driver_tool_bar.volleyball_info,
                    volleyball.addSeparator(),
                    self.driver_tool_bar.volleyball_download,
                    volleyball.addSeparator(),
                    self.driver_tool_bar.volleyball_run,
                    self.driver_tool_bar.volleyball_run_with_checkpoint,
                    volleyball.addSeparator(),
                    self.driver_tool_bar.volleyball_stop,
                    self.driver_tool_bar.volleyball_stop_with_checkpoint,
                    volleyball.addSeparator(),
                    self.driver_tool_bar.volleyball_update_scripts,
                    self.driver_tool_bar.volleyball_update_leagues
                ]
            )

        bd_dao = self.menu_bar.addMenu(self.tr("Базы данных"))
        bd_dao.addActions(
            [
                self.driver_tool_bar.config_dao,
                bd_dao.addSeparator(),
                self.driver_tool_bar.transfer_dao,
                bd_dao.addSeparator(),
                self.driver_tool_bar.script_dao,
                self.driver_tool_bar.league_dao,
                self.driver_tool_bar.match_details_dao,
                self.driver_tool_bar.signal_dao,
                self.driver_tool_bar.ai_prompt_dao
            ]
        )

        if not only_database:
            signals = self.menu_bar.addMenu(self.tr("Сигналы"))
            signals.addActions(
                [
                    self.driver_tool_bar.remove_finished_signals,
                    self.driver_tool_bar.print_signals
                ]
            )

        self._service = SportEventService(db_context, multi_driver_config, parent=self)
        self._service.status_message.connect(self.show_message)

        if not only_database:
            self.driver_tool_bar.football_run.triggered.connect(
                partial(self._service.run, DriverCode.FOOTBALL, False)
            )
            self.driver_tool_bar.hockey_run.triggered.connect(
                partial(self._service.run, DriverCode.HOCKEY, False)
            )
            self.driver_tool_bar.volleyball_run.triggered.connect(
                partial(self._service.run, DriverCode.VOLLEYBALL, False)
            )
            self.driver_tool_bar.football_run_with_checkpoint.triggered.connect(
                partial(self._service.run, DriverCode.FOOTBALL, True)
            )
            self.driver_tool_bar.hockey_run_with_checkpoint.triggered.connect(
                partial(self._service.run, DriverCode.HOCKEY, True)
            )
            self.driver_tool_bar.volleyball_run_with_checkpoint.triggered.connect(
                partial(self._service.run, DriverCode.VOLLEYBALL, True)
            )
            self.driver_tool_bar.football_stop.triggered.connect(
                partial(self._service.stop, DriverCode.FOOTBALL, False)
            )
            self.driver_tool_bar.hockey_stop.triggered.connect(
                partial(self._service.stop, DriverCode.HOCKEY, False)
            )
            self.driver_tool_bar.volleyball_stop.triggered.connect(
                partial(self._service.stop, DriverCode.VOLLEYBALL, False)
            )
            self.driver_tool_bar.football_stop_with_checkpoint.triggered.connect(
                partial(self._service.stop, DriverCode.FOOTBALL, True)
            )
            self.driver_tool_bar.hockey_stop_with_checkpoint.triggered.connect(
                partial(self._service.stop, DriverCode.HOCKEY, True)
            )
            self.driver_tool_bar.volleyball_stop_with_checkpoint.triggered.connect(
                partial(self._service.stop, DriverCode.VOLLEYBALL, True)
            )
            self.driver_tool_bar.football_info.triggered.connect(
                partial(self._service.show_info, DriverCode.FOOTBALL)
            )
            self.driver_tool_bar.hockey_info.triggered.connect(
                partial(self._service.show_info, DriverCode.HOCKEY)
            )
            self.driver_tool_bar.volleyball_info.triggered.connect(
                partial(self._service.show_info, DriverCode.VOLLEYBALL)
            )
            self.driver_tool_bar.football_update_scripts.triggered.connect(
                partial(self._service.update_data, DriverCode.FOOTBALL, True)
            )
            self.driver_tool_bar.hockey_update_scripts.triggered.connect(
                partial(self._service.update_data, DriverCode.HOCKEY, True)
            )
            self.driver_tool_bar.volleyball_update_scripts.triggered.connect(
                partial(self._service.update_data, DriverCode.VOLLEYBALL, True)
            )
            self.driver_tool_bar.football_update_leagues.triggered.connect(
                partial(self._service.update_data, DriverCode.FOOTBALL, False)
            )
            self.driver_tool_bar.hockey_update_leagues.triggered.connect(
                partial(self._service.update_data, DriverCode.HOCKEY, False)
            )
            self.driver_tool_bar.volleyball_update_leagues.triggered.connect(
                partial(self._service.update_data, DriverCode.VOLLEYBALL, False)
            )
            self.driver_tool_bar.football_config.triggered.connect(
                partial(self._service.edit_driver_config, DriverCode.FOOTBALL)
            )
            self.driver_tool_bar.hockey_config.triggered.connect(
                partial(self._service.edit_driver_config, DriverCode.HOCKEY)
            )
            self.driver_tool_bar.volleyball_config.triggered.connect(
                partial(self._service.edit_driver_config, DriverCode.VOLLEYBALL)
            )

        self.driver_tool_bar.football_download.triggered.connect(
            partial(self._service.download_leagues, DriverCode.FOOTBALL)
        )
        self.driver_tool_bar.hockey_download.triggered.connect(
            partial(self._service.download_leagues, DriverCode.HOCKEY)
        )
        self.driver_tool_bar.volleyball_download.triggered.connect(
            partial(self._service.download_leagues, DriverCode.VOLLEYBALL)
        )

        self.driver_tool_bar.config_dao.triggered.connect(self._service.edit_dao_config)
        self.driver_tool_bar.transfer_dao.triggered.connect(self._service.show_transfer_dao)
        self.driver_tool_bar.script_dao.triggered.connect(self._service.show_scripts_dialog)
        self.driver_tool_bar.league_dao.triggered.connect(self._service.show_leagues_dialog)
        self.driver_tool_bar.match_details_dao.triggered.connect(self._service.show_matches_dialog)
        self.driver_tool_bar.signal_dao.triggered.connect(self._service.show_signals_dialog)
        self.driver_tool_bar.ai_prompt_dao.triggered.connect(self._service.show_prompts_dialog)

        if not only_database:
            self._tab_bar = QTabWidget(self)
            self._tab_bar.setDocumentMode(True)
            self._tab_bar.tabBar().setIconSize(QSize(35, 35))
            self._tab_bar.tabBar().setElideMode(Qt.TextElideMode.ElideRight)
            self._tab_bar.tabBar().setFixedWidth(220)

            self._signal_border = SignalBorder(self._service, self)
            self._signal_border.update_progress.connect(self.sync_update_progress)
            self._signal_border.show_message.connect(self.show_message)
            self._signal_border.print_text.connect(self.print_text)
            self._signal_border.customContextMenuRequested.connect(self.show_context_menu)
            self._signal_border.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

            self._service.signal_created.connect(self._signal_border.add_signal)
            self._service.signal_deleted.connect(self._signal_border.delete_signal)
            self._service.signal_restored.connect(self._signal_border.add_signal)
            self._service.signal_evaluated.connect(self._signal_border.evaluated_signal)

            self.driver_tool_bar.remove_finished_signals.triggered.connect(self._signal_border.remove_finished_signals)
            self.driver_tool_bar.print_signals.triggered.connect(self._signal_border.print_signals)

            self._tab_bar.addTab(self._signal_border, QIcon(":/resources/icons/signal.png"), self.tr("Сигналы"))

            self.setCentralWidget(self._tab_bar)

        SportEventDriver.update_progress.connect(self.async_update_progress)

        self._load_config()

        self._thread = QThread()
        self._worker = Worker(self._thread)

    @classmethod
    def get_settings_path(cls) -> str:
        """
        Получить путь к файлу настроек
        """
        return str(Path(DISPLAY))

    def _load_config(self) -> None:
        """
        Загрузка из INI файла.
        """
        settings_file = self.get_settings_path()
        settings = QSettings(str(settings_file), QSettings.Format.IniFormat)

        geometry = settings.value("MainWindow/geometry")
        if geometry and isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)

        state = settings.value("MainWindow/state")
        if state and isinstance(state, QByteArray):
            self.restoreState(state)

    def _save_config(self) -> None:
        """
        Сохранение в INI файл.
        """
        settings_file = self.get_settings_path()

        settings = QSettings(settings_file, QSettings.Format.IniFormat)

        settings.setValue("MainWindow/geometry", self.saveGeometry())
        settings.setValue("MainWindow/state", self.saveState())

        settings.sync()

    def show_message(self, message: str, timeout: int = 2000) -> None:
        """
        Показать сообщение.

        :param message: Сообщение.
        :param timeout: Таймаут.
        """
        self.status_bar.showMessage(message, timeout)

    def print_text(self, text: str) -> None:
        """
        Показать сообщение.

        :param text: Текст.
        """
        self.console_widget.add_text(text)

    def closeEvent(self, event: QCloseEvent) -> None:

        """Перехват события закрытия окна"""
        reply = QMessageBox.question(
            self,
            self.tr("Выход"),
            self.tr("Вы уверены, что хотите выйти?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._save_config()
            self._service.shutdown_workers()

            event.accept()

            ctypes.windll.kernel32.ExitProcess(0)
        else:
            event.ignore()

    async def async_update_progress(self, sender: str, value: int, max_value: int) -> None:
        self.sync_update_progress(value, max_value)

    @Slot()
    def sync_update_progress(self, value: int, max_value: int) -> None:
        if value != max_value:
            self.menu_bar.setEnabled(False)
            self.driver_tool_bar.setEnabled(False)
            self.progress.setVisible(True)
        else:
            self.menu_bar.setEnabled(True)
            self.driver_tool_bar.setEnabled(True)
            self.progress.setVisible(False)

        self.progress.setMaximum(max_value)

        self.progress.setValue(value)

    @Slot()
    def show_context_menu(self, position: QPoint) -> None:
        """
        Показать контекстное меню.

        :param position: Позиция.
        """
        context_menu = QMenu(self)
        context_menu.addAction(self.driver_tool_bar.remove_finished_signals)
        context_menu.addAction(self.driver_tool_bar.print_signals)
        context_menu.exec(self._signal_border.mapToGlobal(position))

    @Slot()
    def show_cache_dialog(self) -> None:
        cache_menu = QMenu(self)
        cache_menu.addAction(
            QIcon(":/resources/icons/download.png"),
            self.tr("Загружено лиг: {}").format(len(DataCache.leagues))
        ).setEnabled(False)
        cache_menu.addAction(
            QIcon(":/resources/icons/download.png"),
            self.tr("Загружено матчей: {}").format(len(DataCache.matches))
        ).setEnabled(False)
        cache_menu.addSeparator()
        clear = cache_menu.addAction(QIcon(":/resources/icons/delete.png"), self.tr("Очистить память"))
        clear.triggered.connect(self._clear_cache)

        global_pos = self._show_dialog.mapToGlobal(QPoint(0, -cache_menu.sizeHint().height()))
        cache_menu.popup(global_pos)

    def _clear_cache(self) -> None:
        def finished():
            self.show_message(self.tr("Память очищена"))

        cache = DataCache()
        self._worker.start(finished, cache.clear)
