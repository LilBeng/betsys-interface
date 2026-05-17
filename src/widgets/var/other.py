from typing import Union, Optional

from PySide6.QtCore import Slot
from betsys import (
    OddsVar,
    ProbabilityVar,
    KellyCriterionVar,
    BothToScoreBet,
    FEventStatusCode,
    ProbabilityScoreVar,
    get_variable_name,
    TeamCode,
    ValueCode,
    OddsValueCode,
    ExpectedScoreVar,
    ShapeVar,
    StrengthRatingVar,
    TotalGoalsBeforeVar,
    StrengthRatingCode,
    NumericalVar,
    Interval
)

from src.dialogs.variable import (
    BaseOtherDialog,
    ProbabilityDialog,
    ExpectedScoreDialog,
    ShapeDialog,
    StrengthRatingDialog,
    TotalGoalsBeforeDialog,
    NumericalDialog
)
from src.utils.lang import AppLang
from src.widgets.var.base import BaseVariableWidget


class BaseOtherWidget(BaseVariableWidget):
    def __init__(
            self,
            title: str,
            variable: Union[OddsVar, ProbabilityVar, KellyCriterionVar],
            all_events: bool,
            *args,
            **kwargs
    ) -> None:
        super().__init__(title, variable, *args, **kwargs)
        self._all_events = all_events

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = BaseOtherDialog(self._variable, self._all_events, parent=self)
        dialog.exec()


class OddsWidget(BaseOtherWidget):
    def __init__(self, variable: Optional[OddsVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = OddsVar(
                odds_bet=BothToScoreBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_both_to_score=True
                ),
                odds_value_code=OddsValueCode.CURRENT,
                value_code=ValueCode.MAX
            )

        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, True, *args, **kwargs)


class ProbabilityWidget(BaseOtherWidget):
    def __init__(self, variable: Optional[ProbabilityVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = ProbabilityVar(
                probability_bet=BothToScoreBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_both_to_score=True
                ),
                value_code=ValueCode.MAX
            )

        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, True, *args, **kwargs)


class KellyCriterionWidget(BaseOtherWidget):
    def __init__(self, variable: Optional[KellyCriterionVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = KellyCriterionVar(
                criterion_bet=BothToScoreBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_both_to_score=True
                ),
                odds_value_code=OddsValueCode.CURRENT,
                value_code=ValueCode.MAX
            )

        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, True, *args, **kwargs)


class ProbabilityScoreWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[ProbabilityScoreVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = ProbabilityScoreVar()
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = ProbabilityDialog(self._variable, parent=self)
        dialog.exec()


class ExpectedScoreWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[ExpectedScoreVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = ExpectedScoreVar()
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = ExpectedScoreDialog(self._variable, parent=self)
        dialog.exec()


class ShapeWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[ShapeVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = ShapeVar(
                shape_team_code=TeamCode.HOME
            )
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = ShapeDialog(self._variable, parent=self)
        dialog.exec()


class StrengthRatingWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[StrengthRatingVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = StrengthRatingVar(
                strength_rating_team_code=TeamCode.HOME,
                strength_rating_code=StrengthRatingCode.TOTAL
            )
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = StrengthRatingDialog(self._variable, parent=self)
        dialog.exec()


class TotalGoalsBeforeWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[TotalGoalsBeforeVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = TotalGoalsBeforeVar(
                interval=Interval(min=1, max=90),
                is_dynamic=False
            )
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = TotalGoalsBeforeDialog(self._variable, parent=self)
        dialog.exec()


class NumericalWidget(BaseVariableWidget):
    def __init__(self, variable: Optional[NumericalVar] = None, *args, **kwargs) -> None:
        if not variable:
            variable = NumericalVar(numeric=0)
        super().__init__(get_variable_name(variable.var_code, AppLang.code), variable, *args, **kwargs)

    @Slot()
    def show_setting_dialog(self) -> None:
        dialog = NumericalDialog(self._variable, parent=self)
        dialog.exec()
