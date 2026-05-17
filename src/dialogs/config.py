import logging
import os
import zoneinfo
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
    QListWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidgetItem,
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
    PredictorCode,
    ForeBetConfig,
    AIAssistantConfig,
    get_predictor_name,
    APIClientConfig,
    DialogConfig
)

from src import CONFIG
from src.utils.blocker import WheelBlocker
from src.utils.button import create_icon_push_button
from src.utils.lang import AppLang
from src.utils.widget import get_time_edit

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
        if self._path.text():
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
        widget = self._stacked_layout.currentWidget()
        if isinstance(widget, LiteDBConfigBox):
            if not widget.config.path:
                QMessageBox.critical(
                    self,
                    self.windowTitle(),
                    f"Не указан путь к локальной БД"
                )

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
        self._table.setMaximumHeight(90)
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

        self._lang_box = QComboBox(self)
        self._lang_box.addItem(get_lang_name(LangCode.RU), LangCode.RU)
        self._lang_box.addItem(get_lang_name(LangCode.EN), LangCode.EN)

        self._project_id = QSpinBox(self, minimum=1)
        self._pages = QSpinBox(self, minimum=1)
        self._time_zone = QSpinBox(self, minimum=1, maximum=11)

        if config:
            self._lang_box.setCurrentText(get_lang_name(config.lang_code))
            self._project_id.setValue(config.project_id)
            self._pages.setValue(config.pages)
            self._time_zone.setValue(config.time_zone)
            self._set_headers(config.headers)

        param_layout = QFormLayout()
        param_layout.addRow(self.tr("Язык:"), self._lang_box)
        param_layout.addRow(self.tr("ID проекта:"), self._project_id)
        param_layout.addRow(self.tr("Страница:"), self._pages)
        param_layout.addRow(self.tr("Часовой пояс:"), self._time_zone)

        table_layout = QHBoxLayout()
        table_layout.addWidget(self._table)
        table_layout.addWidget(self._toolbar)

        layout = QVBoxLayout(self)
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
            project_id=self._project_id.value(),
            lang_code=self._lang_box.currentData(),
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


class ConfigItem(QListWidgetItem):
    """
    Данные для списка.
    """
    def __init__(
            self,
            text: str,
            predictor_code: PredictorCode,
            config: Union[ForeBetConfig, AIAssistantConfig]
    ) -> None:
        super().__init__(text)
        self.predictor_code = predictor_code
        self.config = config


class ForeBetConfigBox(QGroupBox):
    """
    Конфигурация ForeBet.
    """
    def __init__(self, config: Optional[ForeBetConfig] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setTitle(get_predictor_name(PredictorCode.FORE_BET, AppLang.code))

        self._lang_box = QComboBox(self)
        self._lang_box.addItem(get_lang_name(LangCode.RU), LangCode.RU)
        self._lang_box.addItem(get_lang_name(LangCode.EN), LangCode.EN)

        self._offset = get_time_edit(self)

        if config:
            self._lang_box.setCurrentText(get_lang_name(config.lang_code))
            self._offset.setTime(
                QTime(config.offset.hours, config.offset.minutes, config.offset.seconds)
            )

        layout = QFormLayout(self)
        layout.addRow(self.tr("Язык:"), self._lang_box)
        layout.addRow(self.tr("Синхронизация времени:"), self._offset)

    @property
    def config(self) -> ForeBetConfig:
        return ForeBetConfig(
            lang_code=self._lang_box.currentData(),
            offset=Time(
                hours=self._offset.time().hour(),
                minutes=self._offset.time().minute(),
                seconds=self._offset.time().second()
            )
        )


class AIConfigBox(QGroupBox):
    """
    Конфигурация ИИ.
    """
    def __init__(self, config: Optional[AIAssistantConfig] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setTitle(get_predictor_name(PredictorCode.AI, AppLang.code))

        self._model = QLineEdit(self)
        self._temperature = QDoubleSpinBox(self, decimals=1, minimum=0.1, maximum=1, singleStep=0.1)
        self._api_key = QLineEdit(self)
        self._base_url = QLineEdit(self)
        self._timeout = QSpinBox(self, minimum=100, maximum=1000)
        self._max_retries = QSpinBox(self, minimum=1, maximum=10)

        dialog_box = QGroupBox(title=self.tr("Параметры диалога"))
        dialog_layout = QFormLayout(dialog_box)
        dialog_layout.addRow(self.tr("Модель:"), self._model)
        dialog_layout.addRow(self.tr("Температура:"), self._temperature)

        api_box = QGroupBox(title=self.tr("Параметры API"))
        api_layout = QFormLayout(api_box)
        api_layout.addRow(self.tr("Ключ:"), self._api_key)
        api_layout.addRow(self.tr("Адрес:"), self._base_url)
        api_layout.addRow(self.tr("Задержка:"), self._timeout)
        api_layout.addRow(self.tr("Количество повторов:"), self._max_retries)

        self._lang_box = QComboBox(self)
        self._lang_box.addItem(get_lang_name(LangCode.RU), LangCode.RU)
        self._lang_box.addItem(get_lang_name(LangCode.EN), LangCode.EN)

        if config:
            self._model.setText(config.dialog_config.model)
            self._temperature.setValue(config.dialog_config.temperature)
            self._api_key.setText(config.client_config.api_key)
            self._base_url.setText(config.client_config.base_url)
            self._timeout.setValue(config.client_config.timeout)
            self._max_retries.setValue(config.client_config.max_retries)
            self._lang_box.setCurrentText(get_lang_name(config.lang_code))

        layout = QFormLayout(self)
        layout.addRow(dialog_box)
        layout.addRow(api_box)
        layout.addRow(self.tr("Язык:"), self._lang_box)

    @property
    def config(self) -> AIAssistantConfig:
        return AIAssistantConfig(
            dialog_config=DialogConfig(
                model=self._model.text(),
                temperature=self._temperature.value()

            ),
            client_config=APIClientConfig(
                api_key=self._api_key.text(),
                base_url=self._base_url.text(),
                timeout=self._timeout.value(),
                max_retries=self._max_retries.value()
            ),
            lang_code=self._lang_box.currentData()
        )


class PredictorDialog(QDialog):
    def __init__(self, config: Optional[Union[ForeBetConfig, AIAssistantConfig]] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle(self.tr("Прогнозирующая модель"))
        self.setWindowIcon(QIcon(":/resources/icons/config.png"))

        self._models = QComboBox(self)
        for code in PredictorCode:
            self._models.addItem(get_predictor_name(code, AppLang.code), code)

        self._stacked_layout = QStackedLayout()

        if isinstance(config, ForeBetConfig):
            self._fore_bet_config = ForeBetConfigBox(config, self)
        else:
            self._fore_bet_config = ForeBetConfigBox(parent=self)

        if isinstance(config, AIAssistantConfig):
            self._ai_config = AIConfigBox(config, self)
        else:
            self._ai_config = AIConfigBox(parent=self)

        for widget in [self._fore_bet_config, self._ai_config]:
            self._stacked_layout.addWidget(widget)

        if config:
            if isinstance(config, ForeBetConfig):
                self._stacked_layout.setCurrentWidget(self._fore_bet_config)
            else:
                self._stacked_layout.setCurrentWidget(self._ai_config)

            self._models.setCurrentIndex(self._stacked_layout.currentIndex())
            self._models.setEnabled(False)

        add_button = QPushButton(self.tr("Применить"))
        add_button.clicked.connect(self.accept)

        exit_button = QPushButton(self.tr("Отмена"))
        exit_button.clicked.connect(self.reject)

        layout_button = QHBoxLayout()
        layout_button.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_button.addWidget(add_button)
        layout_button.addWidget(exit_button)

        self._dialog_layout = QFormLayout(self)
        self._dialog_layout.setSizeConstraint(QFormLayout.SizeConstraint.SetFixedSize)
        self._dialog_layout.setSpacing(15)
        self._dialog_layout.addRow("Модель:", self._models)
        self._dialog_layout.addRow(self._stacked_layout)
        self._dialog_layout.addRow(layout_button)

        self._models.currentIndexChanged.connect(self.change_index)

        self.wheel_blocker = WheelBlocker()
        self.installEventFilter(self.wheel_blocker)

        self.setup_wheel_filter(self)

    def setup_wheel_filter(self, widget: QWidget) -> None:
        """
        Рекурсивно устанавливаем фильтр на все дочерние виджеты
        """
        widget.installEventFilter(self.wheel_blocker)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self.wheel_blocker)

    @Slot()
    def change_index(self, index: int) -> None:
        self._stacked_layout.setCurrentIndex(index)

    @property
    def item(self) -> ConfigItem:
        widget = self._stacked_layout.currentWidget()
        if isinstance(widget, (ForeBetConfigBox, AIConfigBox)):
            return ConfigItem(
                    get_predictor_name(self._models.currentData(), AppLang.code),
                    self._models.currentData(),
                    widget.config
                )


class PredictorGroupBox(QGroupBox):
    """
    Конфигурация прогнозирующих моделей.
    """
    def __init__(
            self,
            predictors: Optional[dict[PredictorCode, Union[ForeBetConfig, AIAssistantConfig]]] = None,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.setTitle(self.tr("Прогнозирующие модели"))

        self._list_widget = QListWidget(self)
        self._list_widget.setFixedHeight(120)
        self._list_widget.itemDoubleClicked.connect(self._edit_item)

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

        self._add.triggered.connect(self._add_item)
        self._edit.triggered.connect(self._edit_item)
        self._del.triggered.connect(self._del_item)

        self._toolbar.addAction(self._add)
        self._toolbar.addAction(self._edit)
        self._toolbar.addAction(self._del)

        layout = QHBoxLayout(self)
        layout.addWidget(self._list_widget)
        layout.addWidget(self._toolbar)

        if predictors:
            self._set_predictors(predictors)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    @property
    def predictors(self) -> dict[PredictorCode, Union[ForeBetConfig, AIAssistantConfig]]:
        predictors = {}
        for row in range(self._list_widget.count()):
            item = self._list_widget.item(row)
            if isinstance(item, ConfigItem):
                predictors[item.predictor_code] = item.config
        return predictors

    @property
    def _codes(self) -> list[PredictorCode]:
        codes = []
        for row in range(self._list_widget.count()):
            item = self._list_widget.item(row)
            if isinstance(item, ConfigItem):
                codes.append(item.predictor_code)
        return codes

    @Slot()
    def show_context_menu(self, position: QPoint) -> None:
        """
        Показать контекстное меню.

        :param position: Позиция.
        """
        context_menu = QMenu(self)
        context_menu.addAction(self._add)

        if self._list_widget.selectedItems():
            context_menu.addSeparator()

            context_menu.addActions(
                [
                    self._edit,
                    self._del
                ]
            )

        context_menu.exec(self.mapToGlobal(position))

    @Slot()
    def _add_item(self) -> None:
        """
        Добавить данные.
        """
        dialog = PredictorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item = dialog.item

            if item.predictor_code in self._codes:
                reply = QMessageBox.question(
                    self.parent(),
                    self.tr("Добавление модели"),
                    self.tr("Модель «{}» уже есть в списке, заменить на текущую?").format(
                        get_predictor_name(item.predictor_code, AppLang.code),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                        QMessageBox.StandardButton.Cancel
                    )
                )

                if reply == QMessageBox.StandardButton.Yes:
                    for row in range(self._list_widget.count()):
                        list_item = self._list_widget.item(row)
                        if isinstance(list_item, ConfigItem):
                            if item.predictor_code == list_item.predictor_code:
                                self._list_widget.takeItem(row)
                                self._list_widget.addItem(item)

    @Slot()
    def _edit_item(self) -> None:
        """
        Редактировать данные.
        """
        item = self._list_widget.currentItem()
        if item:
            if isinstance(item, ConfigItem):
                dialog = PredictorDialog(item.config, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    edit_item = dialog.item
                    item.setText(edit_item.text())
                    item.predictor_code = edit_item.predictor_code
                    item.config = edit_item.config

    @Slot()
    def _del_item(self) -> None:
        """
        Удалить данные.
        """
        item = self._list_widget.currentItem()
        if item:
            row = self._list_widget.row(item)
            self._list_widget.takeItem(row)

    def _set_predictors(self, predictors: dict[PredictorCode, Union[ForeBetConfig, AIAssistantConfig]]) -> None:
        for predictor_code, config in predictors.items():
            item = ConfigItem(
                get_predictor_name(predictor_code, AppLang.code),
                predictor_code,
                config
            )
            self._list_widget.addItem(item)


class DriverConfigDialog(QDialog):
    """
    Конфигурация драйвера.
    """
    def __init__(self, config: Optional[DriverConfig] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setWindowTitle(self.tr("Настройка конфигурации"))
        self.setWindowIcon(QIcon(":/resources/icons/config.png"))

        if config:
            self._scraper_box = ScraperGroupBox(config.scraper_config, parent=self)
            self._predictor_box = PredictorGroupBox(config.predictors, parent=self)
        else:
            self._scraper_box = ScraperGroupBox(parent=self)
            self._predictor_box = PredictorGroupBox(parent=self)

        self._max_workers = QSpinBox(self, minimum=1, maximum=os.cpu_count())

        self._timezone = QComboBox(self)
        for zone in sorted(zoneinfo.available_timezones()):
            self._timezone.addItem(zone)

        self._misfire_time = get_time_edit(self)
        self._update_match = get_time_edit(self)
        self._update_teams = get_time_edit(self)
        self._update_matches = get_time_edit(self)

        if config:
            if config.max_workers:
                self._max_workers.setValue(config.max_workers)
            self._timezone.setCurrentText(config.timezone)
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

        scheduler_box = QGroupBox(self, title=self.tr("Планировщик задач"))
        scheduler_layout = QFormLayout(scheduler_box)
        scheduler_layout.addRow(self.tr("Количество потоков:"), self._max_workers)
        scheduler_layout.addRow(self.tr("Часовой пояс:"), self._timezone)
        scheduler_layout.addRow(self.tr("Время задержки задачи:"), self._misfire_time)
        scheduler_layout.addRow(self.tr("Таймер обновления матча:"), self._update_match)
        scheduler_layout.addRow(self.tr("Таймер обновления состава:"), self._update_teams)
        scheduler_layout.addRow(self.tr("Время загрузки матчей:"), self._update_matches)

        apply_button = QPushButton(self.tr("Применить"))
        apply_button.clicked.connect(self.accept)

        cancel_button = QPushButton(self.tr("Отмена"))
        cancel_button.clicked.connect(self.reject)

        layout_button = QHBoxLayout()
        layout_button.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_button.addWidget(apply_button)
        layout_button.addWidget(cancel_button)

        layout = QFormLayout(self)
        layout.setSizeConstraint(QFormLayout.SizeConstraint.SetFixedSize)
        layout.setSpacing(5)
        layout.addRow(self._scraper_box)
        layout.addRow(self._predictor_box)
        layout.addRow(scheduler_box)
        layout.addRow(layout_button)

        # Создаем и устанавливаем фильтр
        self.wheel_blocker = WheelBlocker()
        self.installEventFilter(self.wheel_blocker)

        self.setup_wheel_filter(self)

    @property
    def config(self) -> DriverConfig:
        return DriverConfig(
            scraper_config=self._scraper_box.config,
            predictors=self._predictor_box.predictors,
            max_workers=self._max_workers.value(),
            timezone=self._timezone.currentText(),
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

    def setup_wheel_filter(self, widget: QWidget) -> None:
        """
        Рекурсивно устанавливаем фильтр на все дочерние виджеты
        """
        widget.installEventFilter(self.wheel_blocker)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self.wheel_blocker)
