from datetime import timedelta
from typing import Union, Optional

from PySide6.QtCore import Slot, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QCheckBox, QSpinBox
from betsys import (
    OddsVar,
    ProbabilityVar,
    KellyCriterionVar,
    BetCode,
    get_total_bet_name,
    TeamCode,
    ValueCode,
    get_value_name,
    OddsValueCode,
    get_odds_value_name,
    PredictorCode,
    get_predictor_name,
    ExpectedScoreVar,
    ShapeVar,
    StrengthRatingVar,
    TotalGoalsBeforeVar,
    get_team_name,
    get_strength_rating_name,
    StrengthRatingCode,
    NumericalVar,
    H2HAverageVar,
    H2HLengthSeriesVar,
    GameCode,
    get_game_name,
    EncounterCode,
    get_encounter_name,
    Interval,
    BET_TYPE,
    StatisticVar,
    FEventStatusCode,
    get_event_name,
    HEventStatusCode,
    VEventStatusCode,
    HStatisticCode,
    FStatisticCode,
    VStatisticCode,
    get_statistic_name,
    TimeLineStatisticVar,
    MetricProbabilityVar,
    MatchCategoryCode,
    get_match_category_name,
    PriorCode,
    get_prior_name,
    TableFormAverageVar,
    TableFormLengthSeriesVar,
    TableTrueRowCountElementVar,
    TableElementVar,
    TableTruePositionVar,
    ElementRowCode,
    get_element_row_name,
    TableAverageGoalsVar
)

from src.dialogs.base import BaseVarDialog
from src.layouts.interval import IntervalLayout
from src.layouts.stacked import BetStackedLayout
from src.utils.lang import AppLang
from src.widgets.switch import Switch


class BaseH2HDialog(BaseVarDialog):
    def __init__(self, variable: Union[H2HAverageVar, H2HLengthSeriesVar], *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._team_code = QComboBox(self)
        for code in TeamCode:
            self._team_code.addItem(get_team_name(code, AppLang.code), code)

        self._game_code = QComboBox(self)
        for code in GameCode:
            self._game_code.addItem(get_game_name(code, AppLang.code), code)

        self._encounter_code = QComboBox(self)
        for code in EncounterCode:
            self._encounter_code.addItem(get_encounter_name(code, AppLang.code), code)

        self._only_this_league = Switch(size=QSize(50, 25), checked=variable.only_this_league, parent=self)

        self._is_interval = QCheckBox(self.tr("Интервал:"), self)

        self._interval_layout = IntervalLayout(1, 50, self)
        self._is_interval.stateChanged.connect(self._state_interval_value)

        self._is_period = QCheckBox(self.tr("Временной отрезок:"), self)

        self._period = QSpinBox(minimum=1, maximum=1825, singleStep=1, value=365, parent=self)
        self._is_period.stateChanged.connect(self._state_period_value)

        if isinstance(variable, H2HAverageVar):
            bet = variable.average_bet
        elif isinstance(variable, H2HLengthSeriesVar):
            bet = variable.length_series_bet
        else:
            bet = None

        self._bet_stacked = BetStackedLayout(bet, False, self)

        self._bet = QComboBox(self)
        for code in BetCode:
            self._bet.addItem(get_total_bet_name(code, AppLang.code), code)
        self._bet.currentIndexChanged.connect(self._changed_bet)
        if bet:
            self._bet.setCurrentText(get_total_bet_name(bet.bet_code, AppLang.code))

        self._team_code.setCurrentText(get_team_name(variable.team_code, AppLang.code))
        self._game_code.setCurrentText(get_game_name(variable.game_code, AppLang.code))
        self._encounter_code.setCurrentText(get_encounter_name(variable.encounter_code, AppLang.code))

        if variable.interval:
            self._is_interval.setCheckState(Qt.CheckState.Checked)

            self._interval_layout.setEnabled(True)

            self._interval_layout.min.setValue(variable.interval.min)
            self._interval_layout.max.setValue(variable.interval.max)
        else:
            self._is_interval.setCheckState(Qt.CheckState.Unchecked)
            self._interval_layout.setEnabled(False)

        if variable.period:
            self._is_period.setCheckState(Qt.CheckState.Checked)
            self._period.setEnabled(True)

            self._period.setValue(variable.period.days)
        else:
            self._is_period.setCheckState(Qt.CheckState.Unchecked)
            self._period.setEnabled(False)

        self.central_layout.addRow(self.tr("Команда:"), self._team_code)
        self.central_layout.addRow(self.tr("Игра:"), self._game_code)
        self.central_layout.addRow(self.tr("Тип игры:"), self._encounter_code)
        self.central_layout.addRow(self.tr("Ставка:"), self._bet)
        self.central_layout.addRow(self.tr("Текущая лига:"), self._only_this_league)
        self.central_layout.addRow(self._is_interval, self._interval_layout)
        self.central_layout.addRow(self._is_period, self._period)
        self.central_layout.addRow(self._bet_stacked)

        self.setup_wheel_filter(self)

    @property
    def team_code(self) -> TeamCode:
        return self._team_code.currentData()

    @property
    def game_code(self) -> GameCode:
        return self._game_code.currentData()

    @property
    def encounter_code(self) -> EncounterCode:
        return self._encounter_code.currentData()

    @property
    def only_this_league(self) -> bool:
        return self._only_this_league.is_checked()

    @property
    def interval(self) -> Optional[Interval]:
        if self._is_interval.checkState() == Qt.CheckState.Checked:
            return self._interval_layout.interval

    @property
    def period(self) -> Optional[timedelta]:
        if self._is_period.checkState() == Qt.CheckState.Checked:
            return timedelta(days=self._period.value())

    @property
    def bet(self) -> BET_TYPE:
        return self._bet_stacked.bet

    @Slot()
    def _state_interval_value(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            self._interval_layout.setEnabled(True)
        else:
            self._interval_layout.setEnabled(False)

    @Slot()
    def _state_period_value(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            self._period.setEnabled(True)
        else:
            self._period.setEnabled(False)

    @Slot()
    def _changed_bet(self, index: int) -> None:
        code = self._bet.itemData(index)
        self._bet_stacked.set_current_widget(code)

    @Slot()
    def accept(self) -> None:
        if isinstance(self._variable, H2HAverageVar):
            self._variable.team_code = self.team_code
            self._variable.average_bet = self.bet
            self._variable.game_code = self.game_code
            self._variable.encounter_code = self.encounter_code
            self._variable.only_this_league = self.only_this_league
            self._variable.interval = self.interval
            self._variable.period = self.period

        elif isinstance(self._variable, H2HLengthSeriesVar):
            self._variable.team_code = self.team_code
            self._variable.length_series_bet = self.bet
            self._variable.game_code = self.game_code
            self._variable.encounter_code = self.encounter_code
            self._variable.only_this_league = self.only_this_league
            self._variable.interval = self.interval
            self._variable.period = self.period

        super().accept()


class BaseOtherDialog(BaseVarDialog):
    def __init__(
            self,
            variable: Union[OddsVar, ProbabilityVar, KellyCriterionVar],
            all_events: bool,
            *args,
            **kwargs
    ) -> None:
        super().__init__(variable, *args, **kwargs)
        self._bet = QComboBox(self)
        for code in BetCode:
            self._bet.addItem(get_total_bet_name(code, AppLang.code), code)

        if isinstance(variable, OddsVar):
            bet = variable.odds_bet
        elif isinstance(variable, ProbabilityVar):
            bet = variable.probability_bet
        elif isinstance(variable, KellyCriterionVar):
            bet = variable.criterion_bet
        else:
            bet = None

        self._bet_stacked = BetStackedLayout(bet, all_events, self)

        self._bet.currentIndexChanged.connect(self._changed_bet)
        if bet:
            self._bet.setCurrentText(get_total_bet_name(bet.bet_code, AppLang.code))

        self._value = QComboBox(self)
        for code in ValueCode:
            self._value.addItem(get_value_name(code, AppLang.code), code)
        self._value.setCurrentText(get_value_name(variable.value_code, AppLang.code))

        self.central_layout.addRow(self.tr("Значение:"), self._value)

        if isinstance(variable, OddsVar) or isinstance(variable, KellyCriterionVar):
            self._odds_value = QComboBox(self)
            for code in OddsValueCode:
                self._odds_value.addItem(get_odds_value_name(code, AppLang.code), code)
            self._odds_value.setCurrentText(get_odds_value_name(variable.odds_value_code, AppLang.code))

            self.central_layout.addRow(self.tr("Тип коэффициента:"), self._odds_value)

        self.central_layout.addRow(self.tr("Ставка:"), self._bet)
        self.central_layout.addRow(self._bet_stacked)

        self.setup_wheel_filter(self)

    @Slot()
    def _changed_bet(self, index: int) -> None:
        code = self._bet.itemData(index)
        self._bet_stacked.set_current_widget(code)

    @Slot()
    def accept(self) -> None:
        if isinstance(self._variable, OddsVar):
            self._variable.odds_bet = self._bet_stacked.bet
            self._variable.odds_value_code = self._odds_value.currentData()
        elif isinstance(self._variable, ProbabilityVar):
            self._variable.probability_bet = self._bet_stacked.bet
        elif isinstance(self._variable, KellyCriterionVar):
            self._variable.criterion_bet = self._bet_stacked.bet
            self._variable.odds_value_code = self._odds_value.currentData()

        self._variable.value_code = self._value.currentData()

        super().accept()


class ProbabilityDialog(BaseVarDialog):
    def __init__(self, variable: ProbabilityVar, *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._predictor = QComboBox()
        self._predictor.addItem(self.tr("Любой"), None)
        for code in PredictorCode:
            self._predictor.addItem(get_predictor_name(code, AppLang.code), code)

        self._predictor.setCurrentText(get_predictor_name(variable.probability_predictor_code, AppLang.code))

        self.central_layout.addRow(self.tr("Предсказатель:"), self._predictor)

        self.setup_wheel_filter(self)

    @Slot()
    def accept(self) -> None:
        self._variable.probability_predictor_code = self._predictor.currentData()

        super().accept()


class ExpectedScoreDialog(BaseVarDialog):
    def __init__(self, variable: ExpectedScoreVar, *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._team_code = QComboBox(self)
        self._team_code.addItem(self.tr("Нет"), None)
        for code in TeamCode:
            self._team_code.addItem(get_team_name(code, AppLang.code), code)

        self._predictor = QComboBox(self)
        self._predictor.addItem(self.tr("Любой"), None)
        for code in PredictorCode:
            self._predictor.addItem(get_predictor_name(code, AppLang.code), code)

        if text := get_team_name(variable.team_code, AppLang.code):
            self._team_code.setCurrentText(text)
        else:
            self._team_code.setCurrentText(self.tr("Нет"))

        self._predictor.setCurrentText(get_predictor_name(variable.predictor_code, AppLang.code))

        self.central_layout.addRow(self.tr("Команда:"), self._team_code)
        self.central_layout.addRow(self.tr("Предсказатель:"), self._predictor)

        self.setup_wheel_filter(self)

    @Slot()
    def accept(self) -> None:
        self._variable.team_code = self._team_code.currentData()
        self._variable.predictor_code = self._predictor.currentData()

        super().accept()


class ShapeDialog(BaseVarDialog):
    def __init__(self, variable: ShapeVar, *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._team_code = QComboBox(self)
        for code in TeamCode:
            self._team_code.addItem(get_team_name(code, AppLang.code), code)

        self._team_code.setCurrentText(get_team_name(variable.shape_team_code, AppLang.code))

        self.central_layout.addRow("Команда:", self._team_code)

        self.setup_wheel_filter(self)

    @Slot()
    def accept(self) -> None:
        self._variable.shape_team_code = self._team_code.currentData()

        super().accept()


class StrengthRatingDialog(BaseVarDialog):
    def __init__(self, variable: StrengthRatingVar, *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._team_code = QComboBox(self)
        for code in TeamCode:
            self._team_code.addItem(get_team_name(code, AppLang.code), code)

        self._strength_rating_code = QComboBox(self)
        for code in StrengthRatingCode:
            self._strength_rating_code.addItem(get_strength_rating_name(code, AppLang.code), code)

        self._team_code.setCurrentText(get_team_name(variable.strength_rating_team_code, AppLang.code))
        self._strength_rating_code.setCurrentText(get_strength_rating_name(variable.strength_rating_code, AppLang.code))

        self.central_layout.addRow(self.tr("Команда:"), self._team_code)
        self.central_layout.addRow(self.tr("Показатель:"), self._strength_rating_code)

        self.setup_wheel_filter(self)

    @Slot()
    def accept(self) -> None:
        self._variable.strength_rating_team_code = self._team_code.currentData()
        self._variable.strength_rating_code = self._strength_rating_code.currentData()

        super().accept()


class TotalGoalsBeforeDialog(BaseVarDialog):
    def __init__(self, variable: TotalGoalsBeforeVar, *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._team_code = QComboBox(self)
        self._team_code.addItem(self.tr("Общее"), None)
        for code in TeamCode:
            self._team_code.addItem(get_team_name(code, AppLang.code), code)

        self._is_dynamic = Switch(size=QSize(50, 25), checked=variable.is_dynamic, parent=self)

        self._interval_layout = IntervalLayout(0, 120, self)

        self._team_code.setCurrentText(get_team_name(variable.goals_team_code, AppLang.code))
        self._interval_layout.min.setValue(variable.interval.min)
        self._interval_layout.max.setValue(variable.interval.max)

        self.central_layout.addRow(self.tr("В процессе матча:"), self._is_dynamic)
        self.central_layout.addRow(self.tr("Кол-во голов:"), self._team_code)
        self.central_layout.addRow(self.tr("Интервал:"), self._interval_layout)

        self.setup_wheel_filter(self)

    @Slot()
    def accept(self) -> None:
        self._variable.goals_team_code = self._team_code.currentData()
        self._variable.is_dynamic = self._is_dynamic.is_checked()
        self._variable.interval = self._interval_layout.interval

        super().accept()


class NumericalDialog(BaseVarDialog):
    def __init__(self, variable: NumericalVar, *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._numeric = QDoubleSpinBox(minimum=-1e3, maximum=1e3, singleStep=0.1, decimals=3, value=variable.numeric)

        self._is_int = Switch(size=QSize(50, 25), checked=isinstance(variable.numeric, int), parent=self)
        self._is_int.toggled.connect(self._toggled_int)

        self.central_layout.addRow(self.tr("Целое число:"), self._is_int)
        self.central_layout.addRow(self.tr("Значение:"), self._numeric)

        self._toggled_int(isinstance(variable.numeric, int))

        self.setup_wheel_filter(self)

    def _toggled_int(self, flag: bool) -> None:
        if flag:
            self._numeric.setDecimals(0)
        else:
            self._numeric.setDecimals(3)

    @Slot()
    def accept(self) -> None:
        if self._is_int.is_checked():
            self._variable.numeric = int(self._numeric.value())
        else:
            self._variable.numeric = float(self._numeric.value())

        super().accept()


class StatisticDialog(BaseVarDialog):
    def __init__(self, variable: Union[StatisticVar, TimeLineStatisticVar], *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._team_code = QComboBox(self)
        for code in TeamCode:
            self._team_code.addItem(get_team_name(code, AppLang.code), code)

        if isinstance(variable, StatisticVar):
            self._event_status_codes = QComboBox(self)
            for code in FEventStatusCode:
                self._event_status_codes.addItem(
                    QIcon(":/resources/icons/football.png"),
                    get_event_name(code, AppLang.code),
                    code
                )
            for code in HEventStatusCode:
                self._event_status_codes.addItem(
                    QIcon(":/resources/icons/hockey.png"),
                    get_event_name(code, AppLang.code),
                    code
                )
            for code in VEventStatusCode:
                self._event_status_codes.addItem(
                    QIcon(":/resources/icons/volleyball.png"),
                    get_event_name(code, AppLang.code),
                    code
                )

            self._event_status_codes.setCurrentText(get_event_name(variable.event_status_code, AppLang.code))
        else:
            self._current_time = QSpinBox(value=variable.current_time, minimum=1, maximum=200, parent=self)

        self._statistic_codes = QComboBox(self)
        for code in FStatisticCode:
            self._statistic_codes.addItem(
                QIcon(":/resources/icons/football.png"),
                get_statistic_name(code, AppLang.code),
                code
            )
        for code in HStatisticCode:
            self._statistic_codes.addItem(
                QIcon(":/resources/icons/hockey.png"),
                get_statistic_name(code, AppLang.code),
                code
            )
        for code in VStatisticCode:
            self._statistic_codes.addItem(
                QIcon(":/resources/icons/volleyball.png"),
                get_statistic_name(code, AppLang.code),
                code
            )

        self._team_code.setCurrentText(get_team_name(variable.team_code, AppLang.code))
        self._statistic_codes.setCurrentText(get_statistic_name(variable.statistic_code, AppLang.code))

        self.central_layout.addRow(self.tr("Команда:"), self._team_code)
        self.central_layout.addRow(self.tr("Статистика:"), self._statistic_codes)
        if isinstance(variable, StatisticVar):
            self.central_layout.addRow(self.tr("Событие:"), self._event_status_codes)
        else:
            self.central_layout.addRow(self.tr("До минуты:"), self._current_time)

        self.setup_wheel_filter(self)

    @Slot()
    def accept(self) -> None:
        if isinstance(self._variable, StatisticVar):
            self._variable.event_status_code = self._event_status_codes.currentData()
        else:
            self._variable.current_time = self._current_time.value()

        self._variable.statistic_code = self._statistic_codes.currentData()
        self._variable.team_code = self._team_code.currentData()

        super().accept()


class MetricProbabilityDialog(BaseVarDialog):
    def __init__(self, variable: MetricProbabilityVar, *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._category_code = QComboBox(self)
        for match_category_code in MatchCategoryCode:
            self._category_code.addItem(get_match_category_name(match_category_code, AppLang.code), match_category_code)
        self._category_code.setCurrentText(get_match_category_name(variable.category_code, AppLang.code))

        self._use_championship = Switch(size=QSize(50, 25), checked=variable.use_championship, parent=self)
        self._use_cup = Switch(size=QSize(50, 25), checked=variable.use_cup, parent=self)
        self._use_friendly = Switch(size=QSize(50, 25), checked=variable.use_friendly, parent=self)

        self._min_length_mask = QSpinBox(
            minimum=1,
            maximum=50,
            value=variable.min_length_mask,
            parent=self
        )

        self._prior_code = QComboBox(self)
        for prior_code in PriorCode:
            self._prior_code.addItem(get_prior_name(prior_code, AppLang.code), prior_code)
        self._prior_code.setCurrentText(get_prior_name(variable.prior_code, AppLang.code))

        self._number_samples = QSpinBox(
            minimum=100,
            maximum=5000,
            value=variable.number_samples,
            parent=self
        )

        self._bet_stacked = BetStackedLayout(variable.bet, False, self)

        self._bet = QComboBox(self)
        for code in BetCode:
            self._bet.addItem(get_total_bet_name(code, AppLang.code), code)
        self._bet.currentIndexChanged.connect(self._changed_bet)
        self._bet.setCurrentText(get_total_bet_name(variable.bet.bet_code, AppLang.code))

        self.central_layout.addRow(self.tr("Категория:"), self._category_code)
        self.central_layout.addRow(self.tr("Распределение:"), self._prior_code)
        self.central_layout.addRow(self.tr("Ставка:"), self._bet)
        self.central_layout.addRow(self.tr("Чемпионаты:"), self._use_championship)
        self.central_layout.addRow(self.tr("Кубки:"), self._use_cup)
        self.central_layout.addRow(self.tr("Товарищеские:"), self._use_friendly)
        self.central_layout.addRow(self.tr("Минимальная длина маски:"), self._min_length_mask)
        self.central_layout.addRow(self.tr("Количество генераций:"), self._number_samples)
        self.central_layout.addRow(self._bet_stacked)

        self.setup_wheel_filter(self)

    @Slot()
    def _changed_bet(self, index: int) -> None:
        code = self._bet.itemData(index)
        self._bet_stacked.set_current_widget(code)

    @Slot()
    def accept(self) -> None:
        self._variable.category_code = self._category_code.currentData()
        self._variable.bet = self._bet_stacked.bet
        self._variable.prior_code = self._prior_code.currentData()
        self._variable.use_championship = self._use_championship.is_checked()
        self._variable.use_cup = self._use_cup.is_checked()
        self._variable.use_friendly = self._use_friendly.is_checked()
        self._variable.min_length_mask = self._min_length_mask.value()
        self._variable.number_samples = self._number_samples.value()

        super().accept()


class TableFormDialog(BaseVarDialog):
    def __init__(self, variable: Union[TableFormAverageVar, TableFormLengthSeriesVar], *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._team_code = QComboBox(self)
        for code in TeamCode:
            self._team_code.addItem(get_team_name(code, AppLang.code), code)

        self._game_code = QComboBox(self)
        for code in GameCode:
            self._game_code.addItem(get_game_name(code, AppLang.code), code)

        self._is_interval = QCheckBox(self.tr("Интервал:"), self)

        self._interval_layout = IntervalLayout(1, 5, self)
        self._is_interval.stateChanged.connect(self._state_interval_value)

        if isinstance(variable, TableFormAverageVar):
            bet = variable.average_bet
        elif isinstance(variable, TableFormLengthSeriesVar):
            bet = variable.length_series_bet
        else:
            bet = None

        self._bet_stacked = BetStackedLayout(bet, False, self)

        self._bet = QComboBox(self)
        for code in BetCode:
            self._bet.addItem(get_total_bet_name(code, AppLang.code), code)
        self._bet.currentIndexChanged.connect(self._changed_bet)
        if bet:
            self._bet.setCurrentText(get_total_bet_name(bet.bet_code, AppLang.code))

        self._team_code.setCurrentText(get_team_name(variable.team_code, AppLang.code))
        self._game_code.setCurrentText(get_game_name(variable.game_code, AppLang.code))

        if variable.interval:
            self._is_interval.setCheckState(Qt.CheckState.Checked)

            self._interval_layout.setEnabled(True)

            self._interval_layout.min.setValue(variable.interval.min)
            self._interval_layout.max.setValue(variable.interval.max)
        else:
            self._is_interval.setCheckState(Qt.CheckState.Unchecked)
            self._interval_layout.setEnabled(False)

        self.central_layout.addRow(self.tr("Команда:"), self._team_code)
        self.central_layout.addRow(self.tr("Игра:"), self._game_code)
        self.central_layout.addRow(self.tr("Исход:"), self._bet)
        self.central_layout.addRow(self._is_interval, self._interval_layout)
        self.central_layout.addRow(self._bet_stacked)

        self.setup_wheel_filter(self)

    @property
    def team_code(self) -> TeamCode:
        return self._team_code.currentData()

    @property
    def game_code(self) -> GameCode:
        return self._game_code.currentData()

    @property
    def interval(self) -> Optional[Interval]:
        if self._is_interval.checkState() == Qt.CheckState.Checked:
            return self._interval_layout.interval

    @property
    def bet(self) -> BET_TYPE:
        return self._bet_stacked.bet

    @Slot()
    def _state_interval_value(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            self._interval_layout.setEnabled(True)
        else:
            self._interval_layout.setEnabled(False)

    @Slot()
    def _changed_bet(self, index: int) -> None:
        code = self._bet.itemData(index)
        self._bet_stacked.set_current_widget(code)

    @Slot()
    def accept(self) -> None:
        if isinstance(self._variable, TableFormAverageVar):
            self._variable.team_code = self.team_code
            self._variable.average_bet = self.bet
            self._variable.game_code = self.game_code
            self._variable.interval = self.interval

        elif isinstance(self._variable, TableFormLengthSeriesVar):
            self._variable.team_code = self.team_code
            self._variable.length_series_bet = self.bet
            self._variable.game_code = self.game_code
            self._variable.interval = self.interval

        super().accept()


class TableTrueDialog(BaseVarDialog):
    def __init__(
            self,
            variable: Union[TableTrueRowCountElementVar, TableElementVar, TableTruePositionVar],
            *args,
            **kwargs
    ) -> None:
        super().__init__(variable, *args, **kwargs)
        self._game_code = QComboBox(self)
        for code in GameCode:
            self._game_code.addItem(get_game_name(code, AppLang.code), code)

        self._element_row_code = QComboBox(self)
        for code in ElementRowCode:
            self._element_row_code .addItem(get_element_row_name(code, AppLang.code), code)

        self._game_code.setCurrentText(get_game_name(variable.game_code, AppLang.code))
        self._element_row_code.setCurrentText(get_element_row_name(variable.element_row_code, AppLang.code))

        self.central_layout.addRow(self.tr("Игра:"), self._game_code)
        self.central_layout.addRow(self.tr("Элемент:"), self._element_row_code)

        if isinstance(variable, (TableElementVar, TableTruePositionVar)):
            self._team_code = QComboBox(self)
            for code in TeamCode:
                self._team_code.addItem(get_team_name(code, AppLang.code), code)

            self._team_code.setCurrentText(get_team_name(variable.team_code, AppLang.code))

            self.central_layout.addRow(self.tr("Команда:"), self._team_code)

            if isinstance(variable, TableTruePositionVar):
                self._reverse = Switch(size=QSize(50, 25), checked=variable.reverse, parent=self)

                self.central_layout.addRow(self.tr("По убыванию:"), self._reverse)

        self.setup_wheel_filter(self)

    @Slot()
    def accept(self) -> None:
        self._variable.game_code = self._game_code.currentData()
        self._variable.element_row_code = self._element_row_code.currentData()

        if isinstance(self._variable, (TableElementVar, TableTruePositionVar)):
            self._variable.team_code = self._team_code.currentData()

            if isinstance(self._variable, TableTruePositionVar):
                self._variable.reverse = self._reverse.is_checked()

        super().accept()


class TableAverageGoalsDialog(BaseVarDialog):
    def __init__(self, variable: TableAverageGoalsVar, *args, **kwargs) -> None:
        super().__init__(variable, *args, **kwargs)
        self._game_code = QComboBox(self)
        for code in GameCode:
            self._game_code.addItem(get_game_name(code, AppLang.code), code)

        self._game_code.setCurrentText(get_game_name(variable.game_code, AppLang.code))

        self._is_scored = QComboBox(self)
        for code in [True, False]:
            self._is_scored.addItem(self.tr("Забито") if code else self.tr("Пропущено"), code)

        self._game_code.setCurrentText(self.tr("Забито") if variable.is_scored else self.tr("Пропущено"))

        self.central_layout.addRow(self.tr("Игра:"), self._game_code)
        self.central_layout.addRow(self.tr("Параметр:"), self._is_scored)

    @Slot()
    def accept(self) -> None:
        self._variable.game_code = self._game_code.currentData()
        self._variable.is_scored = self._is_scored.currentData()

        super().accept()
