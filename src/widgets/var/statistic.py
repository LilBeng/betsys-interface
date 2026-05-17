from typing import Optional

from PySide6.QtCore import Slot
from betsys import StatisticVar, get_variable_name, FStatisticCode, FEventStatusCode, TeamCode, TimeLineStatisticVar

from src.dialogs.variable import StatisticDialog
from src.utils.lang import AppLang
from src.widgets.var.base import BaseVariableWidget


class StatisticWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[StatisticVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = StatisticVar(
                event_status_code=FEventStatusCode.FULL_TIME,
                statistic_code=FStatisticCode.EXPECTED_GOALS,
                team_code=TeamCode.HOME
            )
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = StatisticDialog(self._variable, parent=self)
        dialog.exec()


class TimeLineStatisticWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[TimeLineStatisticVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = TimeLineStatisticVar(
                current_time=1,
                statistic_code=FStatisticCode.EXPECTED_GOALS,
                team_code=TeamCode.HOME
            )
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = StatisticDialog(self._variable, parent=self)
        dialog.exec()
