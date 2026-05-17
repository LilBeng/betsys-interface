from typing import Optional

from PySide6.QtCore import Slot
from betsys import (
    H2HAverageVar,
    H2HLengthSeriesVar,
    TeamCode,
    GameCode,
    EncounterCode,
    BothToScoreBet,
    FEventStatusCode,
    get_variable_name
)

from src.dialogs.variable import BaseH2HDialog
from src.utils.lang import AppLang
from src.widgets.var.base import BaseVariableWidget


class H2HAverageWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[H2HAverageVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = H2HAverageVar(
                team_code=TeamCode.HOME,
                average_bet=BothToScoreBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_both_to_score=True
                ),
                game_code=GameCode.TOTAL,
                encounter_code=EncounterCode.REGULAR_GAME,
                only_this_league=True
            )

        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = BaseH2HDialog(self._variable, parent=self)
        dialog.exec()


class H2HLengthSeriesWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[H2HLengthSeriesVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = H2HLengthSeriesVar(
                team_code=TeamCode.HOME,
                length_series_bet=BothToScoreBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_both_to_score=True
                ),
                game_code=GameCode.TOTAL,
                encounter_code=EncounterCode.REGULAR_GAME,
                only_this_league=True
            )

        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = BaseH2HDialog(self._variable, parent=self)
        dialog.exec()
