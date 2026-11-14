from PySide6.QtCore import QSize, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGroupBox,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QFormLayout,
    QHBoxLayout,
)
from betsys import Script, MatchCode, get_match_name

from src.dialogs.filters import WeekdayFilterDialog, SignalFilterDialog, MatchFilterDialog
from src.dialogs.property import LeaguePropertyDialog, BetPropertyDialog
from src.utils.button import create_icon_push_button
from src.utils.lang import AppLang
from src.widgets.switch import Switch


class DataGroupBox(QGroupBox):
    def __init__(self, script: Script, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._script = script

        self.setTitle(self.tr("Основные данные"))

        icons = [
            QIcon(":/resources/icons/football.png"),
            QIcon(":/resources/icons/hockey.png"),
            QIcon(":/resources/icons/volleyball.png"),
        ]

        self._id = QLineEdit(text=script.script_id, readOnly=True)

        self._is_active = Switch(size=QSize(50, 25), checked=script.is_active, parent=self)
        self._is_active.toggled.connect(self.change_is_active)

        self._match_code = QComboBox()
        for match_code, icon in zip(MatchCode, icons):
            self._match_code.addItem(icon, get_match_name(match_code, AppLang.code), match_code)
        self._match_code.currentIndexChanged.connect(self.change_math_code)
        self._match_code.setCurrentText(get_match_name(script.match_code, AppLang.code))

        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.addRow(self.tr("ID:"), self._id)
        layout.addRow(self.tr("Активность:"), self._is_active)
        layout.addRow(self.tr("Тип игры:"), self._match_code)

    @Slot()
    def change_is_active(self, flag: bool) -> None:
        self._script.is_active = flag

    @Slot()
    def change_math_code(self, index: int) -> None:
        self._script.match_code = self._match_code.itemData(index)


class PropertyGroupBox(QGroupBox):
    def __init__(self, script: Script, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._script = script

        self.setTitle(self.tr("Параметры"))

        self._signal_property = create_icon_push_button(
            icon=QIcon(":/resources/icons/config.png"),
            tooltip=self.tr("Конфигурация"),
            parent=self
        )

        self._weekday_filter = create_icon_push_button(
            icon=QIcon(":/resources/icons/config.png"),
            tooltip=self.tr("Конфигурация"),
            parent=self
        )

        self._league_property = create_icon_push_button(
            icon=QIcon(":/resources/icons/config.png"),
            tooltip=self.tr("Конфигурация"),
            parent=self
        )

        self._match_filter = create_icon_push_button(
            icon=QIcon(":/resources/icons/config.png"),
            tooltip=self.tr("Конфигурация"),
            parent=self
        )

        self._signal_filter = create_icon_push_button(
            icon=QIcon(":/resources/icons/config.png"),
            tooltip=self.tr("Конфигурация"),
            parent=self
        )

        self._signal_property.clicked.connect(self.show_signal_property)
        self._league_property.clicked.connect(self.show_league_property)
        self._match_filter.clicked.connect(self.show_match_filter)
        self._signal_filter.clicked.connect(self.show_signal_filter)
        self._weekday_filter.clicked.connect(self.show_weekday_filter)

        left_layout = QFormLayout()
        left_layout.setSpacing(10)
        left_layout.addRow(self.tr("Дни недели:"), self._weekday_filter)
        left_layout.addRow(self.tr("Параметры сигнала:"), self._signal_property)
        left_layout.addRow(self.tr("Фильтр сигналов:"), self._signal_filter)

        right_layout = QFormLayout()
        right_layout.setSpacing(10)
        right_layout.addRow(self.tr("Фильтр матчей:"), self._match_filter)
        right_layout.addRow(self.tr("Фильтр лиг:"), self._league_property)

        layout = QHBoxLayout(self)
        layout.setSpacing(25)
        layout.addLayout(left_layout)
        layout.addLayout(right_layout)

    @Slot()
    def show_weekday_filter(self) -> None:
        dialog = WeekdayFilterDialog(self._script.weekday_filter, self)
        dialog.exec()

    @Slot()
    def show_signal_filter(self) -> None:
        dialog = SignalFilterDialog(self._script.signal_filter, self)
        dialog.exec()

    @Slot()
    def show_match_filter(self) -> None:
        dialog = MatchFilterDialog(self._script.match_filter, self)
        dialog.resize(800, 800)
        dialog.exec()

    @Slot()
    def show_league_property(self) -> None:
        dialog = LeaguePropertyDialog(self._script.league_filter, self)
        dialog.exec()

    @Slot()
    def show_signal_property(self) -> None:
        dialog = BetPropertyDialog(self._script.signal_property, parent=self)
        dialog.exec()


class DescriptionGroupBox(QGroupBox):
    def __init__(self, script: Script, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._script = script

        self.setTitle(self.tr("Описание"))

        self._description = QTextEdit(script.description, self)
        self._description.setPlaceholderText("Введите текст ...")
        self._description.setText(script.description)
        self._description.textChanged.connect(self.change_description)

        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.addRow(self._description)

    @Slot()
    def change_description(self) -> None:
        self._script.description = self._description.toPlainText()
