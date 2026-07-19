from typing import Optional

from PySide6.QtCore import Slot, QSize, QPoint
from PySide6.QtGui import Qt, QIcon, QColor, QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QVBoxLayout,
    QLayout,
    QScrollArea,
    QWidget,
    QHBoxLayout,
    QToolBar,
    QLineEdit,
    QMenu
)
from betsys import (
    Script,
    WeekdayCode,
    get_weekday_name,
    PriorityCode,
    get_priority_name,
    VarCode
)

from src.dialogs.base import BaseScriptDialog
from src.utils.highlighter import TextKeywords
from src.utils.lang import AppLang
from src.widgets.color import ColorWidget
from src.widgets.expr import ExpressionStackWidget
from src.widgets.switch import Switch
from src.widgets.variable import DraggableVariableWidget, VariableStackWidget


class WeekdayFilterDialog(BaseScriptDialog):
    def __init__(self, script: Script, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(script, parent, *args, **kwargs)
        self.setWindowTitle(self.tr("Фильтр дней недели"))

        self.central_layout.setSpacing(20)
        self.central_layout.setHorizontalSpacing(120)

        self._switches = {}
        for weekday_code in WeekdayCode:
            switch = Switch(size=QSize(50, 25), checked=weekday_code in script.weekday_filter.weekdays, parent=self)

            self._switches[weekday_code] = switch

            self.central_layout.addRow(get_weekday_name(weekday_code, AppLang.code), switch)

    @Slot()
    def accept(self) -> None:
        codes = set()
        for code, switch in self._switches.items():
            if switch.is_checked():
                codes.add(code)

        self._script.weekday_filter.weekdays = codes

        super().accept()


class SignalFilterDialog(BaseScriptDialog):
    def __init__(self, script: Script, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(script, parent, *args, **kwargs)
        self.setWindowTitle(self.tr("Фильтр сигналов"))

        self._min_priority = QCheckBox(self.tr("Приоритет [Min]:"), self)
        self._min_mean_metric_probability = QCheckBox(self.tr("Вероятность метрики [Mean-Min]:"), self)
        self._min_mean_probability = QCheckBox(self.tr("Вероятность исхода [Mean-Min]:"), self)
        self._min_mean_odds = QCheckBox(self.tr("Коэффициент [Mean-Min]:"), self)

        self._min_priority_code = QComboBox(self)
        for priority_code in PriorityCode:
            self._min_priority_code.addItem(get_priority_name(priority_code, AppLang.code), priority_code)

        self._min_mean_metric_probability_value = QDoubleSpinBox(
            decimals=2,
            minimum=0.1,
            maximum=1,
            singleStep=0.01,
            parent=self
        )
        self._min_mean_probability_value = QDoubleSpinBox(
            decimals=2,
            minimum=0.1,
            maximum=1,
            singleStep=0.01,
            parent=self
        )
        self._min_mean_odds_value = QDoubleSpinBox(
            decimals=2,
            minimum=0.1,
            maximum=100,
            singleStep=0.01,
            parent=self
        )

        self._min_priority.checkStateChanged.connect(self.change_min_priority_code)
        self._min_mean_metric_probability.checkStateChanged.connect(self.change_min_mean_metric_probability_value)
        self._min_mean_probability.checkStateChanged.connect(self.change_min_mean_probability_value)
        self._min_mean_odds.checkStateChanged.connect(self.change_min_mean_odds_value)

        if script.signal_filter.min_priority_code is not None:
            self._min_priority_code.setCurrentText(
                get_priority_name(script.signal_filter.min_priority_code, AppLang.code)
            )

            self._min_priority.setCheckState(Qt.CheckState.Checked)
            self.change_min_priority_code(Qt.CheckState.Checked)
        else:
            self._min_priority.setCheckState(Qt.CheckState.Unchecked)
            self.change_min_priority_code(Qt.CheckState.Unchecked)

        if script.signal_filter.min_mean_metric_probability_value:
            self._min_mean_metric_probability_value.setValue(script.signal_filter.min_mean_metric_probability_value)
            self._min_mean_metric_probability.setCheckState(Qt.CheckState.Checked)
            self.change_min_mean_metric_probability_value(Qt.CheckState.Checked)
        else:
            self._min_mean_metric_probability.setCheckState(Qt.CheckState.Unchecked)
            self.change_min_mean_metric_probability_value(Qt.CheckState.Unchecked)

        if script.signal_filter.min_mean_probability_value:
            self._min_mean_probability_value.setValue(script.signal_filter.min_mean_probability_value)
            self._min_mean_probability.setCheckState(Qt.CheckState.Checked)
            self.change_min_mean_probability_value(Qt.CheckState.Checked)
        else:
            self._min_mean_probability.setCheckState(Qt.CheckState.Unchecked)
            self.change_min_mean_probability_value(Qt.CheckState.Unchecked)

        if script.signal_filter.min_mean_odds_value:
            self._min_mean_odds_value.setValue(script.signal_filter.min_mean_odds_value)
            self._min_mean_odds.setCheckState(Qt.CheckState.Checked)
            self.change_min_mean_odds_value(Qt.CheckState.Checked)

        else:
            self._min_mean_odds.setCheckState(Qt.CheckState.Unchecked)
            self.change_min_mean_odds_value(Qt.CheckState.Unchecked)

        self.central_layout.addRow(self._min_priority, self._min_priority_code)
        self.central_layout.addRow(self._min_mean_metric_probability, self._min_mean_metric_probability_value)
        self.central_layout.addRow(self._min_mean_probability, self._min_mean_probability_value)
        self.central_layout.addRow(self._min_mean_odds, self._min_mean_odds_value)

        self.setup_wheel_filter(self)

    @Slot()
    def change_min_priority_code(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._min_priority_code.setEnabled(True)
        else:
            self._min_priority_code.setEnabled(False)

    @Slot()
    def change_min_mean_metric_probability_value(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._min_mean_metric_probability_value.setEnabled(True)
        else:
            self._min_mean_metric_probability_value.setEnabled(False)

    @Slot()
    def change_min_mean_probability_value(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._min_mean_probability_value.setEnabled(True)
        else:
            self._min_mean_probability_value.setEnabled(False)

    @Slot()
    def change_min_mean_odds_value(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._min_mean_odds_value.setEnabled(True)
        else:
            self._min_mean_odds_value.setEnabled(False)

    @Slot()
    def accept(self) -> None:
        signal_filter = self._script.signal_filter

        if self._min_priority.isChecked():
            signal_filter.min_priority_code = self._min_priority_code.currentData()
        else:
            signal_filter.min_priority_code = None

        if self._min_mean_metric_probability.isChecked():
            signal_filter.min_mean_metric_probability_value = self._min_mean_metric_probability_value.value()
        else:
            signal_filter.min_mean_metric_probability_value = None

        if self._min_mean_probability.isChecked():
            signal_filter.min_mean_probability_value = self._min_mean_probability_value.value()
        else:
            signal_filter.min_mean_probability_value = None

        if self._min_mean_odds.isChecked():
            signal_filter.min_mean_odds_value = self._min_mean_odds_value.value()
        else:
            signal_filter.min_mean_odds_value = None

        super().accept()


class MatchFilterDialog(BaseScriptDialog):
    def __init__(self, script: Script, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(script, parent, *args, **kwargs)
        self.setWindowTitle(self.tr("Фильтр матчей"))

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)

        self._var_widget = VariableStackWidget(script.match_filter.variables, self)
        self._expr_widget = ExpressionStackWidget(script.match_filter.expressions, self)
        self._lineups_widget = Switch(size=QSize(45, 20), checked=script.match_filter.has_lineups, parent=self)

        var_type = ColorWidget(
            title=self.tr("Тип переменной"),
            icon=QIcon(":/resources/icons/var_type.png"),
            icon_size=QSize(32, 32),
            color=QColor(60, 65, 75),
            parent=self
        )
        var_type.setFixedHeight(55)
        var_type.setMaximumWidth(400)

        lineups = ColorWidget(
            title=self.tr("Ожидать обновления состава команд"),
            icon=QIcon(":/resources/icons/lineups.png"),
            icon_size=QSize(32, 32),
            color=QColor(60, 65, 75),
            parent=self
        )
        lineups.setFixedHeight(55)

        lineups_toolbar = QToolBar(parent=self, iconSize=QSize(30, 30))
        lineups_toolbar.addWidget(self._lineups_widget)
        lineups.central_layout.addWidget(lineups_toolbar)

        var = ColorWidget(
            title=self.tr("Переменные"),
            icon=QIcon(":/resources/icons/var.png"),
            icon_size=QSize(32, 32),
            color=QColor(60, 65, 75),
            parent=self
        )
        var.setFixedHeight(55)

        var_toolbar = QToolBar(parent=self, iconSize=QSize(30, 30))

        var.central_layout.addWidget(var_toolbar)

        self._remove_var = QAction(
            QIcon(":/resources/icons/remove.png"),
            self.tr("Очистить"),
            self
        )

        self._find_edit = QLineEdit(self, placeholderText=self.tr("Имя для поиска ..."))
        self._find_edit.textChanged.connect(self._var_widget.find_variable)

        var_toolbar.addWidget(self._find_edit)
        var_toolbar.addAction(self._remove_var)

        expr = ColorWidget(
            title=self.tr("Выражения"),
            icon=QIcon(":/resources/icons/expr.png"),
            icon_size=QSize(32, 32),
            color=QColor(60, 65, 75),
            parent=self
        )
        expr.setFixedHeight(55)

        expr_toolbar = QToolBar(parent=self, iconSize=QSize(30, 30))

        self._add_expr = QAction(
            QIcon(":/resources/icons/plus.png"),
            self.tr("Добавить"),
            self
        )
        self._remove_expr = QAction(
            QIcon(":/resources/icons/remove.png"),
            self.tr("Очистить"),
            self
        )
        self._info_expr = QAction(
            QIcon(":/resources/icons/info.png"),
            self.tr("Информация"),
            self
        )
        expr_toolbar.addActions([self._add_expr,  self._info_expr, self._remove_expr])

        expr.central_layout.addWidget(expr_toolbar)

        var_type_widget = QWidget(self)
        var_type_scroll_layout = QVBoxLayout(var_type_widget)
        var_type_scroll_layout.setContentsMargins(10, 10, 10, 10)
        var_type_scroll_layout.setSpacing(10)

        for var_code in VarCode:
            widget = DraggableVariableWidget(var_code, self)
            widget.add_variable_signal.connect(self._var_widget.create_variable)
            var_type_scroll_layout.addWidget(widget)

        var_type_scroll_layout.addStretch()

        variable_type_scroll = QScrollArea()
        variable_type_scroll.setMaximumWidth(400)
        variable_type_scroll.setWidget(var_type_widget)
        variable_type_scroll.setWidgetResizable(True)

        var_type_layout = QVBoxLayout()
        var_type_layout.addWidget(var_type, alignment=Qt.AlignmentFlag.AlignTop)
        var_type_layout.addWidget(variable_type_scroll)

        var_scroll = QScrollArea()
        var_scroll.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        var_scroll.customContextMenuRequested.connect(self.show_var_context_menu)
        var_scroll.setWidget(self._var_widget)
        var_scroll.setWidgetResizable(True)

        expr_scroll = QScrollArea()
        expr_scroll.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        expr_scroll.customContextMenuRequested.connect(self.show_expr_context_menu)
        expr_scroll.setWidget(self._expr_widget)
        expr_scroll.setWidgetResizable(True)

        var_layout = QVBoxLayout()
        var_layout.addWidget(var, alignment=Qt.AlignmentFlag.AlignTop)
        var_layout.addWidget(var_scroll, stretch=5)
        var_layout.addWidget(expr, alignment=Qt.AlignmentFlag.AlignTop)
        var_layout.addWidget(expr_scroll, stretch=5)
        var_layout.addWidget(lineups, alignment=Qt.AlignmentFlag.AlignBottom)

        filter_layout = QHBoxLayout()
        filter_layout.addLayout(var_type_layout)
        filter_layout.addLayout(var_layout)

        self.central_layout.addRow(filter_layout)

        self._remove_var.triggered.connect(self._var_widget.clear_variables)
        self._remove_expr.triggered.connect(self._expr_widget.clear_expressions)
        self._add_expr.triggered.connect(self._expr_widget.add_expression)
        self._info_expr.triggered.connect(self._expr_widget.show_info)

    @Slot()
    def accept(self) -> None:
        keywords = TextKeywords()
        keywords.clear()

        self._script.match_filter.variables = self._var_widget.variables
        self._script.match_filter.expressions = self._expr_widget.expressions
        self._script.match_filter.has_lineups = self._lineups_widget.is_checked()

        super().accept()

    @Slot()
    def reject(self) -> None:
        keywords = TextKeywords()
        keywords.clear()

        super().reject()

    @Slot()
    def show_expr_context_menu(self, position: QPoint) -> None:
        menu = QMenu(self)
        menu.addAction(self._add_expr)
        menu.addAction(self._info_expr)
        menu.addSeparator()
        menu.addAction(self._remove_expr)
        menu.exec(self._expr_widget.mapToGlobal(position))

    @Slot()
    def show_var_context_menu(self, position: QPoint) -> None:
        menu = QMenu(self)
        menu.addAction(self._remove_var)
        menu.exec(self._var_widget.mapToGlobal(position))
