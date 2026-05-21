from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtGui import Qt, QIcon
from PySide6.QtWidgets import QWidget, QFormLayout, QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox
from betsys import (
    BaseBet,
    get_event_name,
    FEventStatusCode,
    HEventStatusCode,
    VEventStatusCode,
    BetCode,
    EVENT_STATUS_TYPE,
    OverUnderBet,
    get_bet_name,
    TeamCode,
    get_team_name,
    BothToScoreBet,
    OneXTwoBet,
    DoubleChanceBet,
    OddOrEvenBet
)

from src.utils.lang import AppLang


class BaseBetLayout(QFormLayout):
    def __init__(self, bet: Optional[BaseBet] = None, all_events: bool = False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._event_status_codes = QComboBox()

        for code in FEventStatusCode:
            self._event_status_codes.addItem(
                QIcon(":/resources/icons/football.png"),
                get_event_name(code, AppLang.code),
                code
            )

            if not all_events:
                break

        for code in HEventStatusCode:
            self._event_status_codes.addItem(
                QIcon(":/resources/icons/hockey.png"),
                get_event_name(code, AppLang.code),
                code
            )

            if not all_events:
                break

        for code in VEventStatusCode:
            self._event_status_codes.addItem(
                QIcon(":/resources/icons/volleyball.png"),
                get_event_name(code, AppLang.code),
                code
            )

            if not all_events:
                break

        if bet:
            self._event_status_codes.setCurrentText(get_event_name(bet.event_status_code, AppLang.code))

        self.addRow(self.tr("Событие:"), self._event_status_codes)

    @property
    def event_status_code(self) -> EVENT_STATUS_TYPE:
        return self._event_status_codes.currentData()


class OverUnderLayout(BaseBetLayout):
    def __init__(self, bet: Optional[OverUnderBet] = None, all_events: bool = False, *args, **kwargs) -> None:
        super().__init__(bet, all_events, *args, **kwargs)

        self._type = QComboBox()
        for flag in [True, False]:
            self._type.addItem(get_bet_name(BetCode.OVER_UNDER, flag, AppLang.code), flag)

        self._team_code = QComboBox()
        self._team_code.addItem(self.tr("Нет"), None)
        for code in TeamCode:
            self._team_code.addItem(get_team_name(code, AppLang.code), code)

        self._is_value = QCheckBox(self.tr("Значение:"))
        self._is_value.stateChanged.connect(self._state_value)

        self._value = QDoubleSpinBox(minimum=0.5, maximum=10, singleStep=0.5, decimals=1)

        self._is_up_to_time = QCheckBox(self.tr("До минуты:"))
        self._is_up_to_time.stateChanged.connect(self._state_up_to_time)

        self._up_to_time = QSpinBox(minimum=1, maximum=120, singleStep=1)

        if bet:
            if bet.bet_code == BetCode.OVER_UNDER:
                self._type.setCurrentText(get_bet_name(bet.bet_code, bet.is_over, AppLang.code))

                if text := get_team_name(bet.team_code, AppLang.code):
                    self._team_code.setCurrentText(text)
                else:
                    self._team_code.setCurrentText(self.tr("Нет"))

                if bet.value:
                    self._value.setValue(bet.value)
                    self._is_value.setCheckState(Qt.CheckState.Checked)
                else:
                    self._value.setEnabled(False)
                    self._is_value.setCheckState(Qt.CheckState.Unchecked)

                if bet.up_to_time:
                    self._up_to_time.setValue(bet.up_to_time)
                    self._is_up_to_time.setCheckState(Qt.CheckState.Checked)
                else:
                    self._up_to_time.setEnabled(False)
                    self._is_up_to_time.setCheckState(Qt.CheckState.Unchecked)
            else:
                self._value.setEnabled(False)
                self._is_value.setCheckState(Qt.CheckState.Unchecked)
                self._up_to_time.setEnabled(False)
                self._is_up_to_time.setCheckState(Qt.CheckState.Unchecked)
        else:
            self._value.setEnabled(False)
            self._is_value.setCheckState(Qt.CheckState.Unchecked)
            self._up_to_time.setEnabled(False)
            self._is_up_to_time.setCheckState(Qt.CheckState.Unchecked)

        self.addRow(self.tr("Тип:"), self._type)
        self.addRow(self.tr("Индивидуальный:"), self._team_code)

        if not all_events:
            self._is_up_to_time.setVisible(False)
            self._up_to_time.setVisible(False)
            self._is_value.setVisible(False)
            self._is_value.setCheckState(Qt.CheckState.Checked)
            self.addRow(self.tr("Значение:"), self._value)
        else:
            self.addRow(self._is_value, self._value)
            self.addRow(self._is_up_to_time, self._up_to_time)

    @Slot()
    def _state_value(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            self._value.setEnabled(True)
        else:
            self._value.setEnabled(False)

    @Slot()
    def _state_up_to_time(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            self._up_to_time.setEnabled(True)
        else:
            self._up_to_time.setEnabled(False)

    @property
    def is_over(self) -> bool:
        return self._type.currentData()

    @property
    def team_code(self) -> Optional[TeamCode]:
        return self._team_code.currentData()

    @property
    def value(self) -> Optional[float]:
        if self._is_value.checkState() == Qt.CheckState.Checked:
            return self._value.value()

    @property
    def up_to_time(self) -> Optional[int]:
        if self._is_up_to_time.checkState() == Qt.CheckState.Checked:
            return self._up_to_time.value()

    @property
    def bet(self) -> OverUnderBet:
        return OverUnderBet(
            event_status_code=self.event_status_code,
            is_over=self.is_over,
            value=self.value,
            team_code=self.team_code,
            up_to_time=self.up_to_time
        )


class BothToScoreLayout(BaseBetLayout):
    def __init__(self, bet: Optional[BothToScoreBet] = None, all_events: bool = False, *args, **kwargs) -> None:
        super().__init__(bet, all_events, *args, **kwargs)

        self._type = QComboBox()
        for flag in [True, False]:
            self._type.addItem(get_bet_name(BetCode.BOTH_TO_SCORE, flag, AppLang.code), flag)

        if bet:
            if bet.bet_code == BetCode.BOTH_TO_SCORE:
                self._type.setCurrentText(get_bet_name(bet.bet_code, bet.is_both_to_score, AppLang.code))

        self.addRow(self.tr("Тип:"), self._type)

    @property
    def is_both_to_score(self) -> bool:
        return self._type.currentData()

    @property
    def bet(self) -> BothToScoreBet:
        return BothToScoreBet(
            event_status_code=self.event_status_code,
            is_both_to_score=self.is_both_to_score
        )


class OneXTwoLayout(BaseBetLayout):
    def __init__(self, bet: Optional[OneXTwoBet] = None, all_events: bool = False, parent: QWidget = None) -> None:
        super().__init__(bet, all_events, parent)
        self._type = QComboBox(parent=parent)
        for code in [*TeamCode, None]:
            self._type.addItem(get_bet_name(BetCode.ONE_X_TWO, code, AppLang.code), code)

        if bet:
            if bet.bet_code == BetCode.ONE_X_TWO:
                self._type.setCurrentText(get_bet_name(bet.bet_code, bet.win_team_code, AppLang.code))

        self.addRow(self.tr("Тип:"), self._type)

    @property
    def win_team_code(self) -> Optional[TeamCode]:
        return self._type.currentData()

    @property
    def bet(self) -> OneXTwoBet:
        return OneXTwoBet(
            event_status_code=self.event_status_code,
            win_team_code=self.win_team_code
        )


class DoubleChanceLayout(BaseBetLayout):
    def __init__(self, bet: Optional[DoubleChanceBet] = None, all_events: bool = False, parent: QWidget = None) -> None:
        super().__init__(bet, all_events, parent)
        self._type = QComboBox(parent=parent)
        for code in [*TeamCode, None]:
            self._type.addItem(get_bet_name(BetCode.DOUBLE_CHANCE, code, AppLang.code), code)

        if bet:
            if bet.bet_code == BetCode.DOUBLE_CHANCE:
                self._type.setCurrentText(get_bet_name(bet.bet_code, bet.win_or_draw_team_code, AppLang.code))

        self.addRow(self.tr("Тип:"), self._type)

    @property
    def win_or_draw_team_code(self) -> Optional[TeamCode]:
        return self._type.currentData()

    @property
    def bet(self) -> DoubleChanceBet:
        return DoubleChanceBet(
            event_status_code=self.event_status_code,
            win_or_draw_team_code=self.win_or_draw_team_code
        )


class OddOrEvenLayout(BaseBetLayout):
    def __init__(self, bet: Optional[OddOrEvenBet] = None, all_events: bool = False, parent: QWidget = None) -> None:
        super().__init__(bet, all_events, parent)

        self._type = QComboBox(parent=parent)
        for flag in [True, False]:
            self._type.addItem(get_bet_name(BetCode.ODD_OR_EVEN, flag, AppLang.code), flag)

        self._team_code = QComboBox(parent=parent)
        self._team_code.addItem(self.tr("Нет"), None)
        for code in TeamCode:
            self._team_code.addItem(get_team_name(code, AppLang.code), code)

        if bet:
            if bet.bet_code == BetCode.ODD_OR_EVEN:
                self._type.setCurrentText(get_bet_name(BetCode.ODD_OR_EVEN, bet.is_even, AppLang.code))

                if text := get_team_name(bet.team_code, AppLang.code):
                    self._team_code.setCurrentText(text)
                else:
                    self._team_code.setCurrentText(self.tr("Нет"))

        self.addRow(self.tr("Тип:"), self._type)
        self.addRow(self.tr("Индивидуальный:"), self._team_code)

    @property
    def team_code(self) -> Optional[TeamCode]:
        return self._team_code.currentData()

    @property
    def is_even(self) -> bool:
        return self._type.currentData()

    @property
    def bet(self) -> OddOrEvenBet:
        return OddOrEvenBet(
            event_status_code=self.event_status_code,
            is_even=self.is_even,
            team_code=self.team_code
        )
