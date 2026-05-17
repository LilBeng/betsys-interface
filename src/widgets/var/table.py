from typing import Optional

from PySide6.QtCore import Slot
from betsys import (
    get_variable_name,
    TableTrueRowCountElementVar,
    GameCode,
    ElementRowCode,
    TableElementVar,
    TeamCode,
    TableTruePositionVar,
    TableFormAverageVar,
    BothToScoreBet,
    FEventStatusCode,
    TableFormLengthSeriesVar,
    TableAverageGoalsVar
)

from src.dialogs.variable import TableTrueDialog, TableFormDialog, TableAverageGoalsDialog
from src.utils.lang import AppLang
from src.widgets.var.base import BaseVariableWidget


class TableTrueRowCountElementWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[TableTrueRowCountElementVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = TableTrueRowCountElementVar(
                game_code=GameCode.TOTAL,
                element_row_code=ElementRowCode.POINTS
            )
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = TableTrueDialog(self._variable, parent=self)
        dialog.exec()


class TableElementWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[TableElementVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = TableElementVar(
                team_code=TeamCode.HOME,
                game_code=GameCode.TOTAL,
                element_row_code=ElementRowCode.POINTS
            )
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = TableTrueDialog(self._variable, parent=self)
        dialog.exec()


class TableTruePositionWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[TableTruePositionVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = TableTruePositionVar(
                team_code=TeamCode.HOME,
                game_code=GameCode.TOTAL,
                element_row_code=ElementRowCode.POINTS,
                reverse=True
            )
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = TableTrueDialog(self._variable, parent=self)
        dialog.exec()


class TableFormAverageWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[TableFormAverageVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = TableFormAverageVar(
                team_code=TeamCode.HOME,
                average_bet=BothToScoreBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_both_to_score=True
                ),
                game_code=GameCode.TOTAL
            )

        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = TableFormDialog(self._variable, parent=self)
        dialog.exec()


class TableFormLengthSeriesWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[TableFormLengthSeriesVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = TableFormLengthSeriesVar(
                team_code=TeamCode.HOME,
                length_series_bet=BothToScoreBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_both_to_score=True
                ),
                game_code=GameCode.TOTAL
            )

        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = TableFormDialog(self._variable, parent=self)
        dialog.exec()


class TableAverageGoalsWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[TableAverageGoalsVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = TableAverageGoalsVar(
                game_code=GameCode.TOTAL,
                is_scored=True
            )

        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = TableAverageGoalsDialog(self._variable, parent=self)
        dialog.exec()
