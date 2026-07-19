import logging
import os
from typing import Optional, Union

from PySide6.QtCore import Slot, Qt, QStandardPaths, QTime, QSize, QPoint
from PySide6.QtGui import QIcon, QRegularExpressionValidator, QAction
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QHBoxLayout,
    QFileDialog,
    QStackedLayout,
    QPushButton,
    QMessageBox,
    QComboBox,
    QSpinBox,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDoubleSpinBox,
    QWidget,
    QToolBar,
    QMenu
)
from betsys import (
    LiteDBConfig,
    PostgresDBConfig,
    DriverConfig,
    FlashScoreConfig,
    LangCode,
    get_lang_name,
    Time,
    AIAssistantConfig,
    APIClientConfig,
    DialogConfig,
    ReasoningEffortCode,
    get_reasoning_effort_name,
    AutosaveConfig, ForeBetConfig
)

from src import CONFIG, AUTOSAVE_DIR
from src.utils.blocker import WheelBlocker
from src.utils.button import create_icon_push_button
from src.utils.lang import AppLang
from src.utils.widget import get_time_edit
from src.widgets.switch import Switch

_logger = logging.getLogger(__name__)


class LiteDBConfigBox(QGroupBox):
    """
    Конфигурация SQLite.
    """
    def __init__(self, config: Optional[LiteDBConfig] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setTitle(f"SQLite")

        self._path = QLineEdit()
        self._path.setMinimumWidth(350)
        if config:
            self._path.setText(config.path)

        self._add_config = create_icon_push_button(
            icon=QIcon(":/resources/icons/export.png"),
            tooltip=self.tr("Выбрать файл"),
            parent=self
        )

        self._add_config.clicked.connect(self.open_file_dialog)

        self._layout = QHBoxLayout()
        self._layout.addWidget(self._path)
        self._layout.addWidget(self._add_config)

        self._box_layout = QFormLayout(self)
        self._box_layout.addRow(self.tr("Путь к файлу:"), self._layout)

    @property
    def config(self) -> LiteDBConfig:
        return LiteDBConfig(
            path=self._path.text()
        )

    def open_file_dialog(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Выбор файла"),
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            self.tr("Файл базы данных (*.db)")
        )

        if file_name:
            self._path.setText(file_name)


class PostgresDBConfigBox(QGroupBox):
    """
    Конфигурация PostgreSQL.
    """
    def __init__(self, config: Optional[PostgresDBConfig] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setTitle(f"PostgreSQL")

        self._login = QLineEdit(self)

        self._password = QLineEdit(self)
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        self._name = QLineEdit(self)

        self._host = QLineEdit(self)
        self._host.setValidator(QRegularExpressionValidator(r"^[0-9.]*$"))

        self._port = QLineEdit(self)
        self._port.setValidator(QRegularExpressionValidator(r"^\d{0,5}$"))

        if config:
            self._login.setText(config.user)
            self._password.setText(config.password)
            self._name.setText(config.name)
            self._host.setText(config.host)
            self._port.setText(str(config.port))

        self._box_layout = QFormLayout(self)
        self._box_layout.addRow(self.tr("Логин:"), self._login)
        self._box_layout.addRow(self.tr("Пароль:"), self._password)
        self._box_layout.addRow(self.tr("Название БД:"), self._name)
        self._box_layout.addRow(self.tr("Хост:"), self._host)
        self._box_layout.addRow(self.tr("Порт:"), self._port)

    @property
    def config(self) -> Optional[PostgresDBConfig]:
        if all([self._login.text(), self._password.text(), self._name.text(), self._host.text(), self._port.text()]):
            return PostgresDBConfig(
                user=self._login.text(),
                password=self._password.text(),
                name=self._name.text(),
                host=self._host.text(),
                port=int(self._port.text())
            )


class DAOConfigDialog(QDialog):
    """
    Конфигурация БД.
    """
    def __init__(self, config: Optional[Union[LiteDBConfig, PostgresDBConfig]] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setWindowTitle(self.tr("Настройка конфигурации"))
        self.setWindowIcon(QIcon(":/resources/icons/config.png"))
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._db = QComboBox(self)
        for text in ["SQLite", "PostgreSQL"]:
            self._db.addItem(QIcon(":/resources/icons/dao.png"), text)

        self._stacked_layout = QStackedLayout()

        if isinstance(config, LiteDBConfig):
            self._lite_config = LiteDBConfigBox(config, self)
        else:
            self._lite_config = LiteDBConfigBox(parent=self)

        if isinstance(config, PostgresDBConfig):
            self._postgres_config = PostgresDBConfigBox(config, self)
        else:
            self._postgres_config = PostgresDBConfigBox(parent=self)

        for widget in [self._lite_config, self._postgres_config]:
            self._stacked_layout.addWidget(widget)

        if config:
            if isinstance(config, LiteDBConfig):
                self._stacked_layout.setCurrentWidget(self._lite_config)
            else:
                self._stacked_layout.setCurrentWidget(self._postgres_config)

            self._db.setCurrentIndex(self._stacked_layout.currentIndex())

        auth_button = QPushButton(self.tr("Подключиться"))
        auth_button.clicked.connect(self.accept)

        exit_button = QPushButton(self.tr("Отмена"))
        exit_button.clicked.connect(self.reject)

        layout_button = QHBoxLayout()
        layout_button.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_button.addWidget(auth_button)
        layout_button.addWidget(exit_button)

        self._dialog_layout = QFormLayout(self)
        self._dialog_layout.setSizeConstraint(QFormLayout.SizeConstraint.SetFixedSize)
        self._dialog_layout.setSpacing(15)
        self._dialog_layout.addRow(self.tr("Сервер:"), self._db)
        self._dialog_layout.addRow(self._stacked_layout)
        self._dialog_layout.addRow(layout_button)

        self._db.currentIndexChanged.connect(self.change_index)

    @Slot()
    def change_index(self, index: int) -> None:
        self._stacked_layout.setCurrentIndex(index)

    @property
    def config(self) -> Optional[Union[LiteDBConfig, PostgresDBConfig]]:
        widget = self._stacked_layout.currentWidget()
        if isinstance(widget, (LiteDBConfigBox, PostgresDBConfigBox)):
            return widget.config

    def accept(self) -> None:
        try:
            self.config.save(CONFIG)
        except Exception as exception:
            _logger.exception(exception)
            QMessageBox.critical(
                self,
                self.windowTitle(),
                f"Не удалось сохранить конфигурацию подключения к БД"
            )

        super().accept()


class ScraperGroupBox(QGroupBox):
    """
    Конфигурация Flashscore.
    """
    def __init__(self, config: Optional[FlashScoreConfig] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setTitle(self.tr("Доступ к Flashscore"))

        self._table = QTableWidget(0, 2)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setHorizontalHeaderLabels([self.tr("Ключ"), self.tr("Значение")])

        self._toolbar = QToolBar(orientation=Qt.Orientation.Vertical, iconSize=QSize(30, 30), parent=self)

        self._add = QAction(
            icon=QIcon(":/resources/icons/plus.png"),
            text=self.tr("Добавить"),
            parent=self
        )
        self._edit = QAction(
            icon=QIcon(":/resources/icons/edit.png"),
            text=self.tr("Редактировать"),
            parent=self
        )
        self._del = QAction(
            icon=QIcon(":/resources/icons/minus.png"),
            text=self.tr("Удалить"),
            parent=self
        )

        self._add.triggered.connect(self._add_row)
        self._del.triggered.connect(self._del_row)

        self._toolbar.addAction(self._add)
        self._toolbar.addAction(self._del)

        self._pages = QSpinBox(self, minimum=1)
        self._time_zone = QSpinBox(self, minimum=1, maximum=11)

        if config:
            self._pages.setValue(config.pages)
            self._time_zone.setValue(config.time_zone)
            self._set_headers(config.headers)

        param_layout = QFormLayout()
        param_layout.addRow(self.tr("Страница:"), self._pages)
        param_layout.addRow(self.tr("UTC+:"), self._time_zone)

        table_layout = QHBoxLayout()
        table_layout.addWidget(self._table)
        table_layout.addWidget(self._toolbar)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addLayout(table_layout)
        layout.addLayout(param_layout)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def _set_headers(self, headers: dict) -> None:
        """
        Заполнить таблицу.

        :param headers: Данные.
        """
        self._table.setRowCount(0)
        for key, value in headers.items():
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(str(key)))
            self._table.setItem(row, 1, QTableWidgetItem(str(value)))

    @property
    def _headers(self) -> dict:
        result = {}
        for row in range(self._table.rowCount()):
            key_item = self._table.item(row, 0)
            val_item = self._table.item(row, 1)
            if key_item and val_item and key_item.text().strip():
                result[key_item.text().strip()] = val_item.text().strip()

        return result

    @property
    def config(self) -> FlashScoreConfig:
        return FlashScoreConfig(
            headers=self._headers,
            pages=self._pages.value(),
            time_zone=self._time_zone.value()
        )

    @Slot()
    def show_context_menu(self, position: QPoint) -> None:
        """
        Показать контекстное меню.

        :param position: Позиция.
        """
        context_menu = QMenu(self)
        context_menu.addAction(self._add)

        if self._table.selectedItems():
            context_menu.addSeparator()

            context_menu.addActions(
                [
                    self._del
                ]
            )

        context_menu.exec(self.mapToGlobal(position))

    @Slot()
    def _add_row(self) -> None:
        """
        Добавить строку.
        """
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(""))
        self._table.setItem(row, 1, QTableWidgetItem(""))

    @Slot()
    def _del_row(self) -> None:
        """
        Удалить строку.
        """
        current_row = self._table.currentRow()
        if current_row >= 0:
            self._table.removeRow(current_row)


class AIConfigBox(QGroupBox):
    """
    Конфигурация ИИ.
    """
    def __init__(self, config: Optional[AIAssistantConfig] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setTitle(self.tr("Ассистент"))

        self._model = QLineEdit(self)
        self._temperature = QDoubleSpinBox(self, decimals=1, minimum=0.1, maximum=1, singleStep=0.1)
        self._api_key = QLineEdit(self)
        self._base_url = QLineEdit(self)
        self._timeout = QSpinBox(self, minimum=100, maximum=1000)
        self._max_retries = QSpinBox(self, minimum=1, maximum=10)

        self._reasoning_effort = QComboBox(self)
        for reasoning_effort_code in ReasoningEffortCode:
            self._reasoning_effort.addItem(
                get_reasoning_effort_name(reasoning_effort_code, AppLang.code),
                reasoning_effort_code
            )

        dialog_box = QGroupBox(title=self.tr("Параметры чата"))
        dialog_layout = QFormLayout(dialog_box)
        dialog_layout.addRow(self.tr("Модель:"), self._model)
        dialog_layout.addRow(self.tr("Температура:"), self._temperature)
        dialog_layout.addRow(self.tr("Уровень рассуждения:"), self._reasoning_effort)

        api_box = QGroupBox(title=self.tr("Параметры API"))
        api_layout = QFormLayout(api_box)
        api_layout.addRow(self.tr("Ключ:"), self._api_key)
        api_layout.addRow(self.tr("Адрес:"), self._base_url)
        api_layout.addRow(self.tr("Задержка:"), self._timeout)
        api_layout.addRow(self.tr("Количество повторов:"), self._max_retries)

        if config:
            self._model.setText(config.dialog_config.model)
            self._temperature.setValue(config.dialog_config.temperature)
            self._api_key.setText(config.client_config.api_key)
            self._base_url.setText(config.client_config.base_url)
            self._timeout.setValue(config.client_config.timeout)
            self._max_retries.setValue(config.client_config.max_retries)
            self._reasoning_effort.setCurrentText(
                get_reasoning_effort_name(config.dialog_config.reasoning_effort_code, AppLang.code)
            )

        layout = QFormLayout(self)
        layout.addRow(dialog_box)
        layout.addRow(api_box)

    @property
    def config(self) -> AIAssistantConfig:
        return AIAssistantConfig(
            dialog_config=DialogConfig(
                model=self._model.text(),
                temperature=self._temperature.value(),
                reasoning_effort_code=self._reasoning_effort.currentData()
            ),
            client_config=APIClientConfig(
                api_key=self._api_key.text(),
                base_url=self._base_url.text(),
                timeout=self._timeout.value(),
                max_retries=self._max_retries.value()
            ),
            is_active=True
        )


class DriverConfigDialog(QDialog):
    """
    Конфигурация драйвера.
    """
    def __init__(
            self,
            config: Optional[DriverConfig] = None,
            parent: Optional[QWidget] = None,
            *args,
            **kwargs
    ) -> None:
        super().__init__(parent=parent, *args, **kwargs)

        self.setWindowTitle(self.tr("Настройка конфигурации"))
        self.setWindowIcon(QIcon(":/resources/icons/config.png"))

        self._scraper_box = ScraperGroupBox(config.scraper_config if config else None, parent=self)
        self._assistant_box = AIConfigBox(config.assistant_config if config else None, parent=self)
        self._assistant_box.setFixedWidth(550)

        self._max_workers = QSpinBox(self, minimum=1, maximum=os.cpu_count())

        self._lang_box = QComboBox(self)
        for code in [LangCode.RU, LangCode.EN]:
            self._lang_box.addItem(get_lang_name(code), code)

        self._timeline_statistic = Switch(
            size=QSize(50, 25),
            checked=config.time_line_statistic if config else False,
            parent=self
        )
        self._assistant = Switch(
            size=QSize(50, 25),
            checked=bool(config.assistant_config.is_active) if config else False,
            parent=self
        )
        self._probability = Switch(
            size=QSize(50, 25),
            checked=bool(config.provider_config.is_active) if config else False,
            parent=self
        )
        self._autosave = Switch(
            size=QSize(50, 25),
            checked=bool(config.autosave_config.is_active) if config else False,
            parent=self
        )

        self._assistant.toggled.connect(self.change_assistant)
        self._autosave.toggled.connect(self.change_autosave)

        self._misfire_time = get_time_edit(self)
        self._update_match = get_time_edit(self)
        self._update_teams = get_time_edit(self)
        self._update_matches = get_time_edit(self)
        self._autosave_time = get_time_edit(self)

        self._path = QLineEdit()

        self._add_folder = create_icon_push_button(
            icon=QIcon(":/resources/icons/export.png"),
            tooltip=self.tr("Выбрать папку"),
            parent=self
        )
        self._add_folder.clicked.connect(self.open_folder_dialog)

        if config:
            if config.max_workers:
                self._max_workers.setValue(config.max_workers)

            if config.autosave_config:
                self._path.setText(config.autosave_config.folder_path)
                
                self._autosave_time.setTime(
                    QTime(
                        config.autosave_config.time.hours,
                        config.autosave_config.time.minutes,
                        config.autosave_config.time.seconds
                    )
                )

            self._lang_box.setCurrentText(get_lang_name(config.lang_code))

            self._misfire_time.setTime(
                QTime(config.misfire_time.hours, config.misfire_time.minutes, config.misfire_time.seconds)
            )
            self._update_match.setTime(
                QTime(config.update_match.hours, config.update_match.minutes, config.update_match.seconds)
            )
            self._update_teams.setTime(
                QTime(config.update_teams.hours, config.update_teams.minutes, config.update_teams.seconds)
            )
            self._update_matches.setTime(
                QTime(config.update_matches.hours, config.update_matches.minutes, config.update_matches.seconds)
            )

        self.change_autosave(self._autosave.is_checked())
        self.change_assistant(self._assistant.is_checked())

        scheduler_box = QGroupBox(self, title=self.tr("Планировщик задач"))
        scheduler_box.setFixedWidth(550)
        scheduler_layout = QFormLayout(scheduler_box)
        scheduler_layout.setSpacing(10)
        scheduler_layout.addRow(self.tr("Количество потоков:"), self._max_workers)
        scheduler_layout.addRow(self.tr("Время задержки задачи:"), self._misfire_time)
        scheduler_layout.addRow(self.tr("Таймер обновления матча:"), self._update_match)
        scheduler_layout.addRow(self.tr("Таймер обновления состава:"), self._update_teams)
        scheduler_layout.addRow(self.tr("Время загрузки матчей:"), self._update_matches)

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self._path)
        folder_layout.addWidget(self._add_folder)

        driver_box = QGroupBox(self, title=self.tr("Драйвер"))
        driver_layout = QFormLayout(driver_box)
        driver_layout.setSpacing(7)
        driver_layout.addRow(self.tr("Язык:"), self._lang_box)
        driver_layout.addRow(self.tr("Статистика по срезам:"), self._timeline_statistic)
        driver_layout.addRow(self.tr("Ассистент:"), self._assistant)
        driver_layout.addRow(self.tr("Импорт вероятностей:"), self._probability)
        driver_layout.addRow(self.tr("Автосохранение:"), self._autosave)
        driver_layout.addRow(self.tr("Таймер:"), self._autosave_time)
        driver_layout.addRow(self.tr("Папка:"), folder_layout)

        apply_button = QPushButton(self.tr("Применить"))
        apply_button.clicked.connect(self.accept)

        cancel_button = QPushButton(self.tr("Отмена"))
        cancel_button.clicked.connect(self.reject)

        layout_button = QHBoxLayout()
        layout_button.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_button.addWidget(apply_button)
        layout_button.addWidget(cancel_button)

        top_layout = QHBoxLayout()
        top_layout.addWidget(driver_box)
        top_layout.addWidget(scheduler_box)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self._scraper_box)

        bottom_layout = QHBoxLayout()
        bottom_layout.addLayout(left_layout)
        bottom_layout.addWidget(self._assistant_box)

        layout = QFormLayout(self)
        layout.setSizeConstraint(QFormLayout.SizeConstraint.SetFixedSize)
        layout.setSpacing(5)
        layout.addRow(top_layout)
        layout.addRow(bottom_layout)
        layout.addRow(layout_button)

        # Создаем и устанавливаем фильтр
        self.wheel_blocker = WheelBlocker()
        self.installEventFilter(self.wheel_blocker)

        self.setup_wheel_filter(self)

    @property
    def config(self) -> DriverConfig:
        autosave_config = AutosaveConfig(
            time=Time(
                hours=self._autosave_time.time().hour(),
                minutes=self._autosave_time.time().minute(),
                seconds=self._autosave_time.time().second()
            ),
            folder_path=self._path.text() if self._path.text() else AUTOSAVE_DIR,
            is_active=self._autosave.is_checked()
        )

        assistant_config = self._assistant_box.config
        assistant_config.is_active = self._assistant.is_checked()

        provider_config = ForeBetConfig(is_active=self._probability.is_checked())

        return DriverConfig(
            scraper_config=self._scraper_box.config,
            assistant_config=assistant_config,
            autosave_config=autosave_config,
            provider_config=provider_config,
            lang_code=self._lang_box.currentData(),
            time_line_statistic=self._timeline_statistic.is_checked(),
            max_workers=self._max_workers.value(),
            misfire_time=Time(
                hours=self._misfire_time.time().hour(),
                minutes=self._misfire_time.time().minute(),
                seconds=self._misfire_time.time().second()
            ),
            update_match=Time(
                hours=self._update_match.time().hour(),
                minutes=self._update_match.time().minute(),
                seconds=self._update_match.time().second()
            ),
            update_teams=Time(
                hours=self._update_teams.time().hour(),
                minutes=self._update_teams.time().minute(),
                seconds=self._update_teams.time().second()
            ),
            update_matches=Time(
                hours=self._update_matches.time().hour(),
                minutes=self._update_matches.time().minute(),
                seconds=self._update_matches.time().second()
            )
        )

    @Slot()
    def change_assistant(self, flag: bool) -> None:
        self._assistant_box.setEnabled(flag)

    @Slot()
    def change_autosave(self, flag: bool) -> None:
        self._autosave_time.setEnabled(flag)
        self._path.setEnabled(flag)
        self._add_folder.setEnabled(flag)

    @Slot()
    def open_folder_dialog(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.tr("Выбор папки"),
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            QFileDialog.Option.ShowDirsOnly
        )

        if folder_path:
            self._path.setText(folder_path)

    @Slot()
    def _state_is_autosave(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._autosave.setEnabled(True)
        else:
            self._autosave.setEnabled(False)

    def setup_wheel_filter(self, widget: QWidget) -> None:
        """
        Рекурсивно устанавливаем фильтр на все дочерние виджеты
        """
        widget.installEventFilter(self.wheel_blocker)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self.wheel_blocker)
