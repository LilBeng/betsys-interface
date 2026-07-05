from typing import Optional

from PySide6.QtWidgets import QStackedLayout, QGroupBox, QWidget
from betsys import BET_TYPE, BetCode, MatchCode

from src.layouts.bet import OverUnderLayout, OneXTwoLayout, DoubleChanceLayout, BothToScoreLayout, OddOrEvenLayout


class _BetGroupBox(QGroupBox):
    def __init__(
            self,
            layout: callable,
            bet: BET_TYPE,
            all_events: bool = True,
            match_code: Optional[MatchCode] = None,
            *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        self.setTitle(self.tr("Ставка"))

        self.setLayout(layout(bet, all_events, match_code))

    @property
    def bet(self) -> BET_TYPE:
        return self.layout().bet # noqa


class BetStackedLayout(QStackedLayout):
    def __init__(
            self,
            bet: Optional[BET_TYPE] = None,
            all_events: bool = True,
            match_code: Optional[MatchCode] = None,
            parent_widget: Optional[QWidget] = None,
            *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._over_under = _BetGroupBox(OverUnderLayout, bet, all_events, match_code, parent_widget)
        self._both_to_score = _BetGroupBox(BothToScoreLayout, bet, all_events, match_code, parent_widget)
        self._one_x_two = _BetGroupBox(OneXTwoLayout, bet, all_events, parent_widget)
        self._double_chance = _BetGroupBox(DoubleChanceLayout, bet, all_events, match_code, parent_widget)
        self._odd_or_even = _BetGroupBox(OddOrEvenLayout, bet, all_events, match_code, parent_widget)

        self.addWidget(self._over_under)
        self.addWidget(self._both_to_score)
        self.addWidget(self._one_x_two)
        self.addWidget(self._double_chance)
        self.addWidget(self._odd_or_even)

        if bet:
            self.set_current_widget(bet.bet_code)

    @property
    def bet(self) -> BET_TYPE:
        return self.currentWidget().bet # noqa

    def set_current_widget(self, bet_code: BetCode) -> None:
        match bet_code:
            case BetCode.OVER_UNDER:
                self.setCurrentWidget(self._over_under)
            case BetCode.BOTH_TO_SCORE:
                self.setCurrentWidget(self._both_to_score)
            case BetCode.ONE_X_TWO:
                self.setCurrentWidget(self._one_x_two)
            case BetCode.DOUBLE_CHANCE:
                self.setCurrentWidget(self._double_chance)
            case BetCode.ODD_OR_EVEN:
                self.setCurrentWidget(self._odd_or_even)
