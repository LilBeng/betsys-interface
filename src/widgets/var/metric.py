from typing import Optional

from PySide6.QtCore import Slot
from betsys import (
    MetricProbabilityVar,
    MatchCategoryCode,
    BothToScoreBet,
    FEventStatusCode,
    PriorCode,
    get_variable_name
)

from src.dialogs.variable import MetricProbabilityDialog
from src.utils.lang import AppLang
from src.widgets.var.base import BaseVariableWidget


class MetricProbabilityWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[MetricProbabilityVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = MetricProbabilityVar(
                category_code=MatchCategoryCode.OVERALL,
                bet=BothToScoreBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_both_to_score=True
                ),
                use_championship=True,
                use_cup=True,
                use_friendly=False,
                min_length_mask=25,
                prior_code=PriorCode.JEFFREYS,
                number_samples=1500
            )

        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = MetricProbabilityDialog(self._variable, parent=self)
        dialog.exec()
