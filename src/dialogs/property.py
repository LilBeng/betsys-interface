from PySide6.QtCore import Qt, QSize, Slot
from PySide6.QtWidgets import QComboBox, QSpinBox, QListWidget, QListWidgetItem, QCheckBox, QLabel, QFormLayout, \
    QHBoxLayout, QGroupBox
from betsys import (
    Script,
    MatchCategoryCode,
    get_match_category_name,
    get_prior_name,
    PriorCode,
    ClassifyLeagueCode,
    get_classify_league_name,
    get_total_bet_name,
    BetCode,
    PriorityCode,
    get_priority_name, AIPromptDBModel
)

from src.dialogs.base import BaseScriptDialog, BaseButtonDialog
from src.dialogs.league import LeagueTreeWidget
from src.layouts.interval import IntervalLayout
from src.layouts.stacked import BetStackedLayout
from src.utils.cache import DataCache
from src.utils.lang import AppLang
from src.widgets.switch import Switch


class MetricPropertyDialog(BaseScriptDialog):
    def __init__(self, script: Script, *args, **kwargs) -> None:
        super().__init__(script, *args, **kwargs)
        self.setWindowTitle(self.tr("Параметры метрики"))

        self._category_code = QComboBox(self)
        for match_category_code in MatchCategoryCode:
            self._category_code.addItem(get_match_category_name(match_category_code, AppLang.code), match_category_code)
        self._category_code.setCurrentText(get_match_category_name(script.metric_property.category_code, AppLang.code))

        self._use_championship = Switch(
            size=QSize(50, 25),
            checked=script.metric_property.use_championship,
            parent=self
        )
        self._use_cup = Switch(size=QSize(50, 25), checked=script.metric_property.use_cup, parent=self)
        self._use_friendly = Switch(size=QSize(50, 25), checked=script.metric_property.use_friendly, parent=self)

        self._min_length_mask = QSpinBox(
            minimum=1,
            maximum=50,
            value=script.metric_property.min_length_mask,
            parent=self
        )

        self._prior_code = QComboBox(self)
        for prior_code in PriorCode:
            self._prior_code.addItem(get_prior_name(prior_code, AppLang.code), prior_code)
        self._prior_code.setCurrentText(get_prior_name(script.metric_property.prior_code, AppLang.code))

        self._number_samples = QSpinBox(
            minimum=100,
            maximum=5000,
            value=script.metric_property.number_samples,
            parent=self
        )

        self.central_layout.addRow(self.tr("Категория:"), self._category_code)
        self.central_layout.addRow(self.tr("Распределение:"), self._prior_code)
        self.central_layout.addRow(self.tr("Чемпионаты:"), self._use_championship)
        self.central_layout.addRow(self.tr("Кубки:"), self._use_cup)
        self.central_layout.addRow(self.tr("Товарищеские:"), self._use_friendly)
        self.central_layout.addRow(self.tr("Минимальная длина маски:"), self._min_length_mask)
        self.central_layout.addRow(self.tr("Количество генераций:"), self._number_samples)

        self.setup_wheel_filter(self)

    @Slot()
    def accept(self) -> None:
        self._script.metric_property.category_code = self._category_code.currentData()
        self._script.metric_property.prior_code = self._prior_code.currentData()
        self._script.metric_property.use_championship = self._use_championship.is_checked()
        self._script.metric_property.use_cup = self._use_cup.is_checked()
        self._script.metric_property.use_friendly = self._use_friendly.is_checked()
        self._script.metric_property.min_length_mask = self._min_length_mask.value()
        self._script.metric_property.number_samples = self._number_samples.value()

        super().accept()


class LeaguePropertyDialog(BaseScriptDialog):
    def __init__(self, script: Script, *args, **kwargs) -> None:
        super().__init__(script, *args, **kwargs)
        self.setWindowTitle(self.tr("Параметры лиг"))

        self._set = QListWidget(self)
        self._tree = LeagueTreeWidget(self)
        self._tree.setMinimumWidth(450)
        self._switch = Switch(size=QSize(50, 25), checked=bool(script.league_property.ids), parent=self)
        self._switch.toggled.connect(self.toggled_switch)

        for league_code in ClassifyLeagueCode:
            item = QListWidgetItem(get_classify_league_name(league_code, AppLang.code))
            item.setData(Qt.ItemDataRole.UserRole, league_code)

            if league_code in script.league_property.classify:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            self._set.addItem(item)

        self.central_layout.addRow(QLabel(self.tr("Классификация:")))
        self.central_layout.addRow(self._set)
        self.central_layout.addRow(self.tr("Идентификаторы лиг:"), self._switch)
        self.central_layout.addRow(self._tree)

        self.toggled_switch(self._switch.is_checked())

        self.update_tree()

    @Slot()
    def toggled_switch(self, state: bool) -> None:
        self._tree.setEnabled(state)

    @Slot()
    def update_tree(self) -> None:
        ids = self._script.league_property.ids
        if not ids:
            ids = set()

        self._tree.set_items(DataCache.leagues, ids)

    @Slot()
    def accept(self) -> None:
        codes = set()
        for row in range(self._set.count()):
            item = self._set.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                codes.add(item.data(Qt.ItemDataRole.UserRole))

        self._script.league_property.classify = codes

        if self._switch.is_checked():
            self._script.league_property.ids = self._tree.active_ids
        else:
            self._script.league_property.ids = None

        super().accept()


class BetPropertyDialog(BaseScriptDialog):
    def __init__(self, script: Script, *args, **kwargs) -> None:
        super().__init__(script, *args, **kwargs)
        self.setWindowTitle(self.tr("Параметры сигнала"))

        self._priority_code = QComboBox(self)
        for priority_code in [*PriorityCode, None]:
            self._priority_code.addItem(get_priority_name(priority_code, AppLang.code), priority_code)

        self._layout = BetStackedLayout(script.signal_property.bet, parent_widget=self)

        self._interval_layout = IntervalLayout(1, 120, self)

        self._type = QComboBox(self)
        self._type.currentIndexChanged.connect(self.changed_type)
        for code in BetCode:
            self._type.addItem(get_total_bet_name(code, AppLang.code), code)

        self._is_single = Switch(size=QSize(50, 25), checked=script.signal_property.is_single, parent=self)
        self._check_ai = Switch(size=QSize(50, 25), checked=script.signal_property.check_ai, parent=self)
        self._interval = QCheckBox(self.tr("Время сигнала:"))
        self._interval.checkStateChanged.connect(self.change_interval)

        self._type.setCurrentText(get_total_bet_name(script.signal_property.bet.bet_code, AppLang.code))
        self._priority_code.setCurrentText(get_priority_name(script.signal_property.priority_code, AppLang.code))
        if script.signal_property.interval:
            self._interval.setCheckState(Qt.CheckState.Checked)
            self.change_interval(Qt.CheckState.Checked)
            self._interval_layout.min.setValue(script.signal_property.interval.min)
            self._interval_layout.max.setValue(script.signal_property.interval.max)
        else:
            self._interval.setCheckState(Qt.CheckState.Unchecked)
            self.change_interval(Qt.CheckState.Unchecked)

        self.central_layout.addRow(self.tr("Приоритет:"), self._priority_code)
        self.central_layout.addRow(self.tr("Тип ставки:"), self._type)
        self.central_layout.addRow(self._interval, self._interval_layout)
        self.central_layout.addRow(self._layout)
        self.central_layout.addRow(self.tr("Одиночный:"), self._is_single)
        self.central_layout.addRow(self.tr("Рекомендация ИИ:"), self._check_ai)

        self.setup_wheel_filter(self)

    @Slot()
    def changed_type(self, index: int) -> None:
        code = self._type.itemData(index)
        self._layout.set_current_widget(code)

    @Slot()
    def change_interval(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._interval_layout.setEnabled(True)
        else:
            self._interval_layout.setEnabled(False)

    @Slot()
    def accept(self) -> None:
        self._script.signal_property.priority_code = self._priority_code.currentData()
        self._script.signal_property.bet = self._layout.bet
        self._script.signal_property.is_single = self._is_single.is_checked()
        self._script.signal_property.check_ai = self._check_ai.is_checked()
        if self._interval.isChecked():
            self._script.signal_property.interval = self._interval_layout.interval
        else:
            self._script.signal_property.interval = None

        super().accept()


class PromptDialog(BaseButtonDialog):
    def __init__(self, model: AIPromptDBModel, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._model = model

        self.setWindowTitle(self.tr("Параметры матча"))

        self._bet_name_flag = Switch(size=QSize(45, 23), checked=model.bet_name_flag, parent=self)
        self._league_name_flag = Switch(size=QSize(45, 23), checked=model.league_name_flag, parent=self)
        self._home_name_flag = Switch(size=QSize(50, 25), checked=model.home_name_flag, parent=self)
        self._away_name_flag = Switch(size=QSize(50, 25), checked=model.away_name_flag, parent=self)
        self._match_date_flag = Switch(size=QSize(50, 25), checked=model.match_date_flag, parent=self)
        self._table_total_flag = Switch(size=QSize(50, 25), checked=model.table_total_flag, parent=self)
        self._table_home_flag = Switch(size=QSize(50, 25), checked=model.table_home_flag, parent=self)
        self._table_away_flag = Switch(size=QSize(50, 25), checked=model.table_away_flag, parent=self)
        self._home_matches_flag = Switch(size=QSize(50, 25), checked=model.home_matches_flag, parent=self)
        self._away_matches_flag = Switch(size=QSize(50, 25), checked=model.away_matches_flag, parent=self)
        self._h2h_matches_flag = Switch(size=QSize(50, 25), checked=model.h2h_matches_flag, parent=self)
        self._home_team_players_flag = Switch(size=QSize(50, 25), checked=model.home_team_players_flag, parent=self)
        self._home_team_substitutes_flag = Switch(
            size=QSize(50, 25),
            checked=model.home_team_substitutes_flag,
            parent=self
        )
        self._away_team_players_flag = Switch(size=QSize(50, 25), checked=model.away_team_players_flag, parent=self)
        self._away_team_substitutes_flag = Switch(
            size=QSize(50, 25),
            checked=model.away_team_substitutes_flag,
            parent=self
        )

        self._is_playing_teams = Switch(size=QSize(50, 25), checked=model.is_playing_teams, parent=self)
        self._is_playing_home = Switch(size=QSize(50, 25), checked=model.is_playing_home, parent=self)
        self._is_playing_away = Switch(size=QSize(50, 25), checked=model.is_playing_away, parent=self)
        self._count_home_matches = QSpinBox(minimum=0, maximum=100, singleStep=1, value=model.count_home_matches)
        self._count_away_matches = QSpinBox(minimum=0, maximum=100, singleStep=1, value=model.count_away_matches)
        self._count_h2h_matches = QSpinBox(minimum=0, maximum=100, singleStep=1, value=model.count_h2h_matches)

        self._is_playing_teams.setEnabled(self._table_total_flag.is_checked())
        self._is_playing_home.setEnabled(self._table_home_flag.is_checked())
        self._is_playing_away.setEnabled(self._table_away_flag.is_checked())
        self._count_home_matches.setEnabled(self._home_matches_flag.is_checked())
        self._count_away_matches.setEnabled(self._away_matches_flag.is_checked())
        self._count_h2h_matches.setEnabled(self._h2h_matches_flag.is_checked())

        self._table_total_flag.toggled.connect(self.change_table_total)
        self._table_home_flag.toggled.connect(self.change_table_home)
        self._table_away_flag.toggled.connect(self.change_table_away)
        self._home_matches_flag.toggled.connect(self.change_home_matches)
        self._away_matches_flag.toggled.connect(self.change_away_matches)
        self._h2h_matches_flag.toggled.connect(self.change_h2h_matches)

        param_layout = QFormLayout()
        param_layout.setSpacing(10)
        param_layout.setHorizontalSpacing(35)
        param_layout.addRow(self.tr("Ставка для анализа:"), self._bet_name_flag)
        param_layout.addRow(self.tr("Наименование лиги:"), self._league_name_flag)
        param_layout.addRow(self.tr("Наименование хозяев:"), self._home_name_flag)
        param_layout.addRow(self.tr("Наименование гостей:"), self._away_name_flag)
        param_layout.addRow(self.tr("Дата матча:"), self._match_date_flag)

        table_layout = QFormLayout()
        table_layout.setSpacing(10)
        table_layout.setHorizontalSpacing(25)
        table_layout.addRow(self.tr("Таблица - Итоговая:"), self._table_total_flag)
        table_layout.addRow(self.tr("Только команды матча:"), self._is_playing_teams)
        table_layout.addRow(self.tr("Таблица - Дома:"), self._table_home_flag)
        table_layout.addRow(self.tr("Только хозяева:"), self._is_playing_home)
        table_layout.addRow(self.tr("Таблица - Гости:"), self._table_away_flag)
        table_layout.addRow(self.tr("Только гости:"), self._is_playing_away)

        match_layout = QFormLayout()
        match_layout.setSpacing(10)
        match_layout.setHorizontalSpacing(45)
        match_layout.addRow(self.tr("Матчи хозяев:"), self._home_matches_flag)
        match_layout.addRow(self.tr("Количество [Хозяева]:"), self._count_home_matches)
        match_layout.addRow(self.tr("Матчи гостей:"), self._away_matches_flag)
        match_layout.addRow(self.tr("Количество [Гости]:"), self._count_away_matches)
        match_layout.addRow(self.tr("Личные встречи:"), self._h2h_matches_flag)
        match_layout.addRow(self.tr("Количество:"), self._count_h2h_matches)

        lineups_layout = QFormLayout()
        lineups_layout.setSpacing(10)
        lineups_layout.setHorizontalSpacing(35)
        lineups_layout.addRow(self.tr("Состав хозяев:"), self._home_team_players_flag)
        lineups_layout.addRow(self.tr("Игроки хозяев в запасе:"), self._home_team_substitutes_flag)
        lineups_layout.addRow(self.tr("Состав гостей:"), self._away_team_players_flag)
        lineups_layout.addRow(self.tr("Игроки гостей в запасе:"), self._away_team_substitutes_flag)

        param = QGroupBox(self.tr("Основные"), self)
        param.setLayout(param_layout)

        lineups = QGroupBox(self.tr("Составы"), self)
        lineups.setLayout(lineups_layout)

        table = QGroupBox(self.tr("Таблицы"), self)
        table.setLayout(table_layout)

        match = QGroupBox(self.tr("Матчи"), self)
        match.setLayout(match_layout)

        max_width = max(
            param.sizeHint().width(),
            lineups.sizeHint().width(),
            table.sizeHint().width(),
            match.sizeHint().width()
        )

        # Устанавливаем всем
        for group in [param, lineups, table, match]:
            group.setMinimumWidth(max_width)

        top_layout = QHBoxLayout()
        top_layout.addWidget(param)
        top_layout.addWidget(lineups)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(table)
        bottom_layout.addWidget(match)

        self.central_layout.addRow(top_layout)
        self.central_layout.addRow(bottom_layout)

        self.setup_wheel_filter(self)

    @Slot()
    def change_table_total(self, flag: bool) -> None:
        self._is_playing_teams.setEnabled(flag)

    @Slot()
    def change_table_home(self, flag: bool) -> None:
        self._is_playing_home.setEnabled(flag)

    @Slot()
    def change_table_away(self, flag: bool) -> None:
        self._is_playing_away.setEnabled(flag)

    @Slot()
    def change_home_matches(self, flag: bool) -> None:
        self._count_home_matches.setEnabled(flag)

    @Slot()
    def change_away_matches(self, flag: bool) -> None:
        self._count_away_matches.setEnabled(flag)

    @Slot()
    def change_h2h_matches(self, flag: bool) -> None:
        self._count_h2h_matches.setEnabled(flag)

    @Slot()
    def accept(self) -> None:
        self._model.bet_name_flag = self._bet_name_flag.is_checked()
        self._model.league_name_flag = self._league_name_flag.is_checked()
        self._model.home_name_flag = self._home_name_flag.is_checked()
        self._model.away_name_flag = self._away_name_flag.is_checked()
        self._model.match_date_flag = self._match_date_flag.is_checked()
        self._model.table_total_flag = self._table_total_flag.is_checked()
        self._model.is_playing_teams = self._is_playing_teams.is_checked()
        self._model.table_home_flag = self._table_home_flag.is_checked()
        self._model.is_playing_home = self._is_playing_home.is_checked()
        self._model.table_away_flag = self._table_away_flag.is_checked()
        self._model.is_playing_away = self._is_playing_away.is_checked()
        self._model.home_matches_flag = self._home_matches_flag.is_checked()
        self._model.count_home_matches = self._count_home_matches.value()
        self._model.away_matches_flag = self._away_matches_flag.is_checked()
        self._model.count_away_matches = self._count_away_matches.value()
        self._model.h2h_matches_flag = self._h2h_matches_flag.is_checked()
        self._model.count_h2h_matches = self._count_h2h_matches.value()
        self._model.home_team_players_flag = self._home_team_players_flag.is_checked()
        self._model.home_team_substitutes_flag = self._home_team_substitutes_flag.is_checked()
        self._model.away_team_players_flag = self._away_team_players_flag.is_checked()
        self._model.away_team_substitutes_flag = self._away_team_substitutes_flag.is_checked()
        super().accept()
