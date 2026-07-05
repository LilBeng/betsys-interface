from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QComboBox, QFormLayout, QLabel, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox, \
    QStackedLayout, QLayout
from betsys import (
    MatchDetails,
    BetCode,
    get_total_bet_name,
    OddsValueCode,
    get_odds_value_name,
    ValueCode,
    get_value_name
)

from src.dialogs.base import BaseDialog
from src.layouts.stacked import BetStackedLayout
from src.utils.lang import AppLang


class MarketWidget(QWidget):
    def __init__(self, match_details: MatchDetails, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)

        self._match_details = match_details

        self._bet_stacked = BetStackedLayout(None, True, match_details.match.match_code, self)

        self._bet = QComboBox(self)
        for code in BetCode:
            self._bet.addItem(get_total_bet_name(code, AppLang.code), code)

        self._bet.currentIndexChanged.connect(self._changed_bet)

        self._odds_value = QComboBox(self)
        for code in OddsValueCode:
            self._odds_value.addItem(get_odds_value_name(code, AppLang.code))

        self._odds_value.currentIndexChanged.connect(self.on_any_change)

        self._value = QComboBox(self)
        for code in ValueCode:
            self._value.addItem(get_value_name(code, AppLang.code))

        self._value.currentIndexChanged.connect(self.on_any_change)

        self._label = QLabel()

        layout = QFormLayout(self)
        layout.addRow(self.tr("Ставка:"), self._bet)
        layout.addRow(self.tr("Тип коэффициента:"), self._odds_value)
        layout.addRow(self.tr("Тип значения:"), self._value)
        layout.addRow(self._bet_stacked)
        layout.addRow(self._label)

        for index in range(self._bet_stacked.count()):
            page = self._bet_stacked.widget(index)
            self.connect_widgets_recursive(page)

        self.on_any_change()

    def connect_widgets_recursive(self, widget):
        """Рекурсивно подключает все виджеты"""
        if isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(self.on_any_change)
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(self.on_any_change)
        elif isinstance(widget, QDoubleSpinBox):
            widget.valueChanged.connect(self.on_any_change)
        elif isinstance(widget, QLineEdit):
            widget.textChanged.connect(self.on_any_change)
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(self.on_any_change)

        # Рекурсивно обходим дочерние виджеты
        if hasattr(widget, 'children'):
            for child in widget.children():
                if isinstance(child, QWidget):
                    self.connect_widgets_recursive(child)

    @Slot()
    def on_any_change(self) -> None:
        value = self._match_details.find_odds_value(
            self._bet_stacked.bet,
            self._odds_value.currentData(),
            self._value.currentData()
        )
        if value:
            self._label.setText(self.tr("Коэффициент: {}").format(value))
        else:
            self._label.setText(self.tr("Коэффициент: не найден"))

    @Slot()
    def _changed_bet(self, index: int) -> None:
        code = self._bet.itemData(index)
        self._bet_stacked.set_current_widget(code)

        self.on_any_change()


class StackedMarketDialog(BaseDialog):
    def __init__(self, matches: list[MatchDetails], parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)

        self.setWindowIcon(QIcon(":/resources/icons/info.png"))
        self.setWindowTitle(self.tr("Коэффициенты"))

        self._box = QComboBox(self)
        self._box.addItems([match.match.match_id for match in matches])
        self._box.currentIndexChanged.connect(self._changed)

        self._stacked_layout = QStackedLayout()

        layout = QFormLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addRow(self.tr("Идентификатор матча:"), self._box)
        layout.addRow(self._stacked_layout)

        for match in matches:
            widget = MarketWidget(match, self)
            self._stacked_layout.addWidget(widget)

        self.setup_wheel_filter(self)

    @Slot()
    def _changed(self, index: int) -> None:
        self._stacked_layout.setCurrentIndex(index)
