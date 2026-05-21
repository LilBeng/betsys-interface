from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QWidget, QComboBox, QLabel, QCheckBox, QFormLayout
from betsys import (
    DBContext,
    ScriptDBModel,
    get_priority_name,
    PriorityCode,
    BetCode,
    get_total_bet_name,
    MatchCode,
    SignalTypeCode,
    get_signal_type_name
)
from qasync import asyncSlot

from src.dialogs.dao import BaseDAODialog
from src.utils.blocker import WheelBlocker
from src.utils.lang import AppLang


class CalculatorWidget(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._count = QLabel(self.tr("Общее количество: -"), self)

        self._id = QCheckBox(self.tr("Идентификатор:"), self)
        self._priority = QCheckBox(self.tr("Приоритет:"), self)
        self._type = QCheckBox(self.tr("Сигнал:"), self)
        self._bet = QCheckBox(self.tr("Ставка:"), self)

        self._scripts = QComboBox(self)

        self._priority_code = QComboBox(self)
        for priority_code in PriorityCode:
            self._priority_code.addItem(get_priority_name(priority_code, AppLang.code), priority_code)

        self._type_code = QComboBox(self)
        for type_code in SignalTypeCode:
            self._type_code.addItem(get_signal_type_name(type_code, AppLang.code), type_code)

        self._bet_code = QComboBox(self)
        for bet_code in BetCode:
            self._bet_code.addItem(get_total_bet_name(bet_code, AppLang.code), bet_code)

        self._id.checkStateChanged.connect(self.change_id)
        self._priority.checkStateChanged.connect(self.change_priority)
        self._type.checkStateChanged.connect(self.change_type)
        self._bet.checkStateChanged.connect(self.change_bet)

        self._id.setCheckState(Qt.CheckState.Checked)
        self._priority.setCheckState(Qt.CheckState.Unchecked)
        self._type.setCheckState(Qt.CheckState.Unchecked)
        self._bet.setCheckState(Qt.CheckState.Unchecked)

        self.change_id(Qt.CheckState.Checked)
        self.change_priority(Qt.CheckState.Unchecked)
        self.change_type(Qt.CheckState.Unchecked)
        self.change_bet(Qt.CheckState.Unchecked)

        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.addRow(self._count)
        layout.addRow(self._id, self._scripts)
        layout.addRow(self._type, self._type_code)
        layout.addRow(self._bet, self._bet_code)
        layout.addRow(self._priority, self._priority_code)

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

    @property
    def dict(self) -> dict:
        values = {}

        if self._id.isChecked():
            values["script_id"] = self._scripts.currentData()

        if self._bet.isChecked():
            values["bet_code"] = self._bet_code.currentData()

        if self._type.isChecked():
            values["signal_type_code"] = self._type_code.currentData()

        if self._priority.isChecked():
            values["priority_code"] = self._priority_code.currentData()

        return values

    @Slot()
    def change_id(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._scripts.setEnabled(True)
        else:
            self._scripts.setEnabled(False)

    @Slot()
    def change_priority(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._priority_code.setEnabled(True)
        else:
            self._priority_code.setEnabled(False)

    @Slot()
    def change_type(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._type_code.setEnabled(True)
        else:
            self._type_code.setEnabled(False)

    @Slot()
    def change_bet(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._bet_code.setEnabled(True)
        else:
            self._bet_code.setEnabled(False)

    def set_data(self, scripts: list[ScriptDBModel], count_signals: int) -> None:
        self._scripts.clear()

        if scripts:
            self._id.setCheckState(Qt.CheckState.Checked)
            self._id.setEnabled(True)
            self.change_id(Qt.CheckState.Checked)

            icons = {
                MatchCode.FOOTBALL: QIcon(":/resources/icons/football.png"),
                MatchCode.HOCKEY: QIcon(":/resources/icons/hockey.png"),
                MatchCode.VOLLEYBALL: QIcon(":/resources/icons/volleyball.png"),
            }

            for index, script in enumerate(scripts):
                self._scripts.addItem(icons.get(script.match_code), script.id, script.id)
                self._scripts.setItemData(index, script.description, Qt.ItemDataRole.ToolTipRole)
        else:
            self._id.setCheckState(Qt.CheckState.Unchecked)
            self._id.setEnabled(False)
            self.change_id(Qt.CheckState.Unchecked)

        self._count.setText(self.tr("Общее количество: {}").format(count_signals))


class SignalDAODialog(BaseDAODialog):

    def __init__(self, db_context: DBContext, *args, **kwargs) -> None:
        super().__init__(
            db_context,
            CalculatorWidget,
            self.tr("БД Сигналы"),
            QIcon(":/resources/icons/dao.png"),
            *args,
            **kwargs
        )

        self.setMaximumSize(600, 350)

        self._calc = QAction(
            QIcon(":/resources/icons/console.png"),
            self.tr("Вычислить проходимость"),
            self
        )

        self._update = QAction(
            QIcon(":/resources/icons/update.png"),
            self.tr("Обновить"),
            self
        )

        self._calc.triggered.connect(self.calculate)
        self._update.triggered.connect(self.start_update.emit)

        self.toolbar.addAction(self._calc)
        self.toolbar.addAction(self._update)

        self.start_update.connect(self.update_data)

        self.start_update.emit()

    @asyncSlot()
    async def calculate(self) -> None:
        self.started()
        count = await self.db_context.signals.get_count(**self.central_widget.dict)
        win_rate = await self.db_context.signals.get_win_rate(**self.central_widget.dict)

        if count:
            self.show_message(self.tr("Найдено: {} | Проходимость: {:.0f}%").format(count, win_rate * 100), 5000)
        else:
            self.show_message(self.tr("Сигналы не найдены"))

        self.finished()

    @asyncSlot()
    async def update_data(self, batch_size: int = 50) -> None:
        self.started()

        scripts = await self.get_scripts(batch_size)
        count_signals = await self.db_context.signals.get_count()

        self.central_widget.set_data(scripts, count_signals)

        self.finished()

        self.show_message(self.tr("Данные обновлены"))
