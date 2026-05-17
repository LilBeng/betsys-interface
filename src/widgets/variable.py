from typing import Any, Type

from PySide6.QtCore import QSize, Signal, Slot, Qt, QMimeData
from PySide6.QtGui import QIcon, QMouseEvent, QDrag, QPixmap, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QLabel, QHBoxLayout, QFrame, QWidget
from betsys import VarCode, get_variable_name, VARIABLE_TYPE

from src.layouts.flow import FlowLayout
from src.utils.button import create_icon_push_button
from src.utils.highlighter import TextKeywords
from src.utils.lang import AppLang
from src.widgets.var.h2h import H2HAverageWidget, H2HLengthSeriesWidget
from src.widgets.var.metric import MetricProbabilityWidget
from src.widgets.var.other import (
    OddsWidget,
    ProbabilityWidget,
    KellyCriterionWidget,
    ShapeWidget,
    StrengthRatingWidget,
    ProbabilityScoreWidget,
    ExpectedScoreWidget,
    TotalGoalsBeforeWidget,
    NumericalWidget
)
from src.widgets.var.statistic import StatisticWidget, TimeLineStatisticWidget
from src.widgets.var.table import (
    TableFormLengthSeriesWidget,
    TableTrueRowCountElementWidget,
    TableTruePositionWidget,
    TableElementWidget,
    TableFormAverageWidget,
    TableAverageGoalsWidget
)


class DraggableVariableWidget(QFrame):
    add_variable_signal = Signal(VarCode)

    def __init__(self, var_code: VarCode, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._var_code = var_code

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)

        label = QLabel(get_variable_name(var_code, AppLang.code), self)

        add_button = create_icon_push_button(
            QIcon(":/resources/icons/plus.png"),
            self.tr("Добавить"),
            QSize(35, 35),
            self
        )
        add_button.clicked.connect(self.add_variable)

        layout = QHBoxLayout(self)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(add_button)

    @Slot()
    def add_variable(self) -> None:
        self.add_variable_signal.emit(self._var_code)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self._var_code.name)
        drag.setMimeData(mime_data)

        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)

        drag.exec(Qt.DropAction.CopyAction)


class VariableStackWidget(QWidget):
    def __init__(self, variables: list[VARIABLE_TYPE], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

        self._layout = FlowLayout(self)
        self._layout.setContentsMargins(18, 18, 18, 18)
        self._layout.setSpacing(25)

        for variable in variables:
            self.add_variable(variable)

    @property
    def variables(self) -> list[VARIABLE_TYPE]:
        return [item.widget().variable for item in self._layout.items]

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        code = VarCode[event.mimeData().text()]
        self._layout.addWidget(self._get_cls(code)(parent=self))
        event.acceptProposedAction()

    @Slot()
    def find_variable(self, name: str) -> None:
        for item in self._layout.items:
            item.widget().setEnabled(name in item.widget().name)

    @Slot()
    def clear_variables(self) -> None:
        self._layout.clear()

    def add_variable(self, variable: VARIABLE_TYPE) -> None:
        cls = self._get_cls(variable.var_code)
        widget = cls(variable, parent=self)

        keywords = TextKeywords()
        if variable.name:
            keywords.add_word(widget.id, variable.name)

        self._layout.addWidget(widget)

    @Slot()
    def create_variable(self, var_code: VarCode) -> None:
        cls = self._get_cls(var_code)

        self._layout.addWidget(cls(parent=self))

    @staticmethod
    def _get_cls(var_code: VarCode) -> Type[Any]:
        match var_code:
            case VarCode.H2H_AVERAGE:
                return H2HAverageWidget
            case VarCode.H2H_LENGTH_SERIES:
                return H2HLengthSeriesWidget
            case VarCode.ODDS:
                return OddsWidget
            case VarCode.PROBABILITY:
                return ProbabilityWidget
            case VarCode.KELLY_CRITERION:
                return KellyCriterionWidget
            case VarCode.STATISTIC:
                return StatisticWidget
            case VarCode.TIMELINE_STATISTIC:
                return TimeLineStatisticWidget
            case VarCode.TABLE_ALL_AVERAGE_GOALS:
                return TableAverageGoalsWidget
            case VarCode.TABLE_ROW_COUNT_ELEMENT:
                return TableTrueRowCountElementWidget
            case VarCode.TABLE_POSITION:
                return TableTruePositionWidget
            case VarCode.TABLE_ELEMENT:
                return TableElementWidget
            case VarCode.TABLE_FORM_AVERAGE:
                return TableFormAverageWidget
            case VarCode.TABLE_FORM_LENGTH_SERIES:
                return TableFormLengthSeriesWidget
            case VarCode.PROBABILITY_SCORE:
                return ProbabilityScoreWidget
            case VarCode.EXPECTED_SCORE:
                return ExpectedScoreWidget
            case VarCode.TOTAL_GOALS_BEFORE:
                return TotalGoalsBeforeWidget
            case VarCode.NUMERIC:
                return NumericalWidget
            case VarCode.SHAPE:
                return ShapeWidget
            case VarCode.STRENGTH_RATING:
                return StrengthRatingWidget
            case VarCode.METRIC_PROBABILITY:
                return MetricProbabilityWidget
