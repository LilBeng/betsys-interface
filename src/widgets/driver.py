from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolBar, QMenu, QToolButton

from src.utils.button import create_tool_button


class DriverToolBar(QToolBar):
    """
    Панель управления драйверами.
    """

    def __init__(self, only_database: bool, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setWindowTitle(self.tr("Панель инструментов"))

        self.setObjectName("toolbar")

        self.setIconSize(QSize(45, 45))

        if not only_database:

            # Запуск
            self._run_button = create_tool_button(
                icon=QIcon(":/resources/icons/run.png"),
                tooltip=self.tr("Запустить"),
                parent=self
            )

            self._run_menu = QMenu(self._run_button)

            run_football_menu = self._run_menu.addMenu(
                QIcon(":/resources/icons/football.png"),
                self.tr("Футбол")
            )
            self.football_run = run_football_menu.addAction(
                QIcon(":/resources/icons/run.png"),
                self.tr("Запустить")
            )
            self.football_run_with_checkpoint = run_football_menu.addAction(
                QIcon(":/resources/icons/run.png"),
                self.tr("Запустить [Контрольная точка]")
            )

            run_hockey_menu = self._run_menu.addMenu(
                QIcon(":/resources/icons/hockey.png"),
                self.tr("Хоккей")
            )
            self.hockey_run = run_hockey_menu.addAction(
                QIcon(":/resources/icons/run.png"),
                self.tr("Запустить")
            )
            self.hockey_run_with_checkpoint = run_hockey_menu.addAction(
                QIcon(":/resources/icons/run.png"),
                self.tr("Запустить [Контрольная точка]")
            )

            run_volleyball_menu = self._run_menu.addMenu(
                QIcon(":/resources/icons/volleyball.png"),
                self.tr("Волейбол")
            )
            self.volleyball_run = run_volleyball_menu.addAction(
                QIcon(":/resources/icons/run.png"),
                self.tr("Запустить")
            )
            self.volleyball_run_with_checkpoint = run_volleyball_menu.addAction(
                QIcon(":/resources/icons/run.png"),
                self.tr("Запустить [Контрольная точка]")
            )

            self._run_button.setMenu(self._run_menu)
            self._run_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

            # Остановка
            self._stop_button = create_tool_button(
                icon=QIcon(":/resources/icons/stop.png"),
                tooltip=self.tr("Остановить"),
                parent=self
            )

            self._stop_menu = QMenu(self._stop_button)

            stop_football_menu = self._stop_menu.addMenu(
                QIcon(":/resources/icons/football.png"),
                self.tr("Футбол")
            )
            self.football_stop = stop_football_menu.addAction(
                QIcon(":/resources/icons/stop.png"),
                self.tr("Остановить")
            )
            self.football_stop_with_checkpoint = stop_football_menu.addAction(
                QIcon(":/resources/icons/stop.png"),
                self.tr("Остановить [Контрольная точка]")
            )

            stop_hockey_menu = self._stop_menu.addMenu(
                QIcon(":/resources/icons/hockey.png"),
                self.tr("Хоккей")
            )
            self.hockey_stop = stop_hockey_menu.addAction(
                QIcon(":/resources/icons/stop.png"),
                self.tr("Остановить")
            )
            self.hockey_stop_with_checkpoint = stop_hockey_menu.addAction(
                QIcon(":/resources/icons/stop.png"),
                self.tr("Остановить [Контрольная точка]")
            )

            stop_volleyball_menu = self._stop_menu.addMenu(
                QIcon(":/resources/icons/volleyball.png"),
                self.tr("Волейбол")
            )
            self.volleyball_stop = stop_volleyball_menu.addAction(
                QIcon(":/resources/icons/stop.png"),
                self.tr("Остановить")
            )
            self.volleyball_stop_with_checkpoint = stop_volleyball_menu.addAction(
                QIcon(":/resources/icons/stop.png"),
                self.tr("Остановить [Контрольная точка]")
            )

            self._stop_button.setMenu(self._stop_menu)
            self._stop_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

            # Обновление
            self._update_button = create_tool_button(
                icon=QIcon(":/resources/icons/update.png"),
                tooltip=self.tr("Обновить"),
                parent=self
            )

            self._update_menu = QMenu(self._update_button)

            update_football_menu = self._update_menu.addMenu(
                QIcon(":/resources/icons/football.png"),
                self.tr("Футбол")
            )
            self.football_update_scripts = update_football_menu.addAction(
                QIcon(":/resources/icons/update.png"),
                self.tr("Обновить сценарии")
            )
            self.football_update_leagues = update_football_menu.addAction(
                QIcon(":/resources/icons/update.png"),
                self.tr("Обновить лиги")
            )

            update_hockey_menu = self._update_menu.addMenu(
                QIcon(":/resources/icons/hockey.png"),
                self.tr("Хоккей")
            )
            self.hockey_update_scripts = update_hockey_menu.addAction(
                QIcon(":/resources/icons/update.png"),
                self.tr("Обновить сценарии")
            )
            self.hockey_update_leagues = update_hockey_menu.addAction(
                QIcon(":/resources/icons/update.png"),
                self.tr("Обновить лиги")
            )

            update_volleyball_menu = self._update_menu.addMenu(
                QIcon(":/resources/icons/volleyball.png"),
                self.tr("Волейбол")
            )
            self.volleyball_update_scripts = update_volleyball_menu.addAction(
                QIcon(":/resources/icons/update.png"),
                self.tr("Обновить сценарии")
            )
            self.volleyball_update_leagues = update_volleyball_menu.addAction(
                QIcon(":/resources/icons/update.png"),
                self.tr("Обновить лиги")
            )
            self.volleyball_update_leagues = update_volleyball_menu.addAction(
                QIcon(":/resources/icons/update.png"),
                self.tr("Обновить лиги")
            )

            self._update_button.setMenu(self._update_menu)
            self._update_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

            # Информация
            self._info_button = create_tool_button(
                icon=QIcon(":/resources/icons/info.png"),
                tooltip=self.tr("Информация"),
                parent=self
            )

            self._info_menu = QMenu(self._info_button)

            self.football_info = self._info_menu.addAction(
                QIcon(":/resources/icons/info.png"),
                self.tr("Информация [Футбол]")
            )
            self.hockey_info = self._info_menu.addAction(
                QIcon(":/resources/icons/info.png"),
                self.tr("Информация [Хоккей]")
            )
            self.volleyball_info = self._info_menu.addAction(
                QIcon(":/resources/icons/info.png"),
                self.tr("Информация [Волейбол]")
            )

            self._info_button.setMenu(self._info_menu)
            self._info_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # Информация
        self._download_button = create_tool_button(
            icon=QIcon(":/resources/icons/download.png"),
            tooltip=self.tr("Загрузка"),
            parent=self
        )

        self._download_menu = QMenu(self._download_button)

        self.football_download = self._download_menu.addAction(
            QIcon(":/resources/icons/download.png"),
            self.tr("Загрузить лиги [Футбол]")
        )
        self.hockey_download = self._download_menu.addAction(
            QIcon(":/resources/icons/download.png"),
            self.tr("Загрузить лиги [Хоккей]")
        )
        self.volleyball_download = self._download_menu.addAction(
            QIcon(":/resources/icons/download.png"),
            self.tr("Загрузить лиги [Волейбол]")
        )

        self._download_button.setMenu(self._download_menu)
        self._download_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        if not only_database:
            # Конфигурация
            self._config_button = create_tool_button(
                icon=QIcon(":/resources/icons/config.png"),
                tooltip=self.tr("Конфигурация"),
                parent=self
            )

            self._config_menu = QMenu(self._config_button)

            self.football_config = self._config_menu.addAction(
                QIcon(":/resources/icons/config.png"),
                self.tr("Конфигурация [Футбол]")
            )
            self.hockey_config = self._config_menu.addAction(
                QIcon(":/resources/icons/config.png"),
                self.tr("Конфигурация [Хоккей]")
            )
            self.volleyball_config = self._config_menu.addAction(
                QIcon(":/resources/icons/config.png"),
                self.tr("Конфигурация [Волейбол]")
            )

            self._config_button.setMenu(self._config_menu)
            self._config_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # Базы данных
        self._dao_button = create_tool_button(
            icon=QIcon(":/resources/icons/dao.png"),
            tooltip=self.tr("Базы данных"),
            parent=self
        )

        self._dao_menu = QMenu(self._dao_button)

        self.config_dao = self._dao_menu.addAction(
            QIcon(":/resources/icons/config.png"),
            self.tr("Конфигурация")
        )
        self._dao_menu.addSeparator()

        self.transfer_dao = self._dao_menu.addAction(
            QIcon(":/resources/icons/update.png"),
            self.tr("Обмен данными")
        )
        self._dao_menu.addSeparator()

        self.script_dao = self._dao_menu.addAction(
            QIcon(":/resources/icons/dao.png"),
            self.tr("БД Сценарии")
        )
        self.league_dao = self._dao_menu.addAction(
            QIcon(":/resources/icons/dao.png"),
            self.tr("БД Лиги")
        )
        self.match_details_dao = self._dao_menu.addAction(
            QIcon(":/resources/icons/dao.png"),
            self.tr("БД Матчи")
        )
        self.signal_dao = self._dao_menu.addAction(
            QIcon(":/resources/icons/dao.png"),
            self.tr("БД Сигналы")
        )
        self.ai_prompt_dao = self._dao_menu.addAction(
            QIcon(":/resources/icons/dao.png"),
            self.tr("БД Промты")
        )

        self._dao_button.setMenu(self._dao_menu)
        self._dao_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        if not only_database:
            self._signal_button = create_tool_button(
                icon=QIcon(":/resources/icons/signal.png"),
                tooltip=self.tr("Сигналы"),
                parent=self
            )
            self._signal_menu = QMenu(self._signal_button)

            self.remove_finished_signals = self._signal_menu.addAction(
                QIcon(":/resources/icons/remove.png"),
                self.tr("Очистить завершенные"),
            )

            self.print_signals = self._signal_menu.addAction(
                QIcon(":/resources/icons/console.png"),
                self.tr("Вывести в консоль")
            )
            self._signal_button.setMenu(self._signal_menu)
            self._signal_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        if not only_database:
            self.addWidget(self._run_button)
            self.addWidget(self._stop_button)
            self.addWidget(self._info_button)
            self.addWidget(self._update_button)

        self.addWidget(self._download_button)
        if not only_database:
            self.addWidget(self._config_button)

        self.addSeparator()
        self.addWidget(self._dao_button)
        if not only_database:
            self.addSeparator()
            self.addWidget(self._signal_button)
