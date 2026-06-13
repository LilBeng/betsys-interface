from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QGroupBox
from betsys import (
    MatchDetails,
    get_match_status_name,
    MatchStatusCode,
    get_global_event_status_name,
    GameCode,
    get_game_name,
    TeamCode,
    get_team_name,
    EncounterCode,
    get_encounter_name,
    PlayerCode,
    get_players_name,
    MatchCode,
    FEventStatusCode,
    get_event_status_name,
    HEventStatusCode,
    VEventStatusCode
)

from src.utils.blocker import WheelBlocker
from src.utils.lang import AppLang
from src.widgets.table import TableWidget, H2HWidget, TeamWidget, StatisticWidget


class MatchDetailsWidget(QWidget):
    def __init__(self, match_details: MatchDetails, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._match_details = match_details

        self.wheel_blocker = WheelBlocker()

        teams = QLabel(f"{match_details.match.home_team.name} - {match_details.match.away_team.name}", parent=self)
        status = QLabel(get_match_status_name(match_details.match.match_summary.match_status_code, AppLang.code))

        layout = QFormLayout(self, horizontalSpacing=40, verticalSpacing=20)

        data = QGroupBox(self.tr("Общие данные"), self)
        layout.addRow(data)

        data_layout = QFormLayout(data, horizontalSpacing=10, verticalSpacing=10)
        data_layout.addRow(self.tr("Страна:"), QLabel(match_details.match.league.country_name))
        data_layout.addRow(self.tr("Лига:"), QLabel(match_details.match.league.league_name))
        data_layout.addRow(self.tr("Матч:"), teams)
        data_layout.addRow(self.tr("Статус:"), status)

        if match_details.match.match_summary.match_status_code == MatchStatusCode.IN_PROGRESS:
            event = QLabel(
                get_global_event_status_name(match_details.match.match_summary.event_status_code, AppLang.code)
            )
            data_layout.addRow(self.tr("Событие:"), event)

        if match_details.match.match_summary.match_status_code != MatchStatusCode.NOT_STARTED:
            if match_details.match.match_summary.home_team_score is not None:
                if match_details.match.match_summary.current_time > 0:
                    score = QLabel(
                        f"{match_details.match.match_summary.home_team_score} - "
                        f"{match_details.match.match_summary.away_team_score} "
                        f"({match_details.match.match_summary.current_time}\')"
                    )
                else:
                    score = QLabel(
                        f"{match_details.match.match_summary.home_team_score} - "
                        f"{match_details.match.match_summary.away_team_score}"
                    )
                data_layout.addRow(self.tr("Счет:"), score)

        if match_details.match.statistic.total:
            self._statistics = StatisticWidget(parent=self)
            self._statistics.horizontalHeader().setMinimumSectionSize(150)
            self._statistics.setMinimumHeight(250)

            self._statistic_box = QComboBox(self)
            self._statistic_box.installEventFilter(self.wheel_blocker)
            self._statistic_box.currentIndexChanged.connect(self._changed_statistics)

            if match_details.match.match_code == MatchCode.FOOTBALL:
                for code in FEventStatusCode:
                    if match_details.match.statistic.get_statistics(code):
                        self._statistic_box.addItem(get_event_status_name(code, AppLang.code), code)

                self._statistic_box.setCurrentText(get_event_status_name(FEventStatusCode.FULL_TIME, AppLang.code))

            elif match_details.match.match_code == MatchCode.HOCKEY:
                for code in HEventStatusCode:
                    if match_details.match.statistic.get_statistics(code):
                        self._statistic_box.addItem(get_event_status_name(code, AppLang.code), code)

                self._statistic_box.setCurrentText(get_event_status_name(HEventStatusCode.FULL_TIME, AppLang.code))
            else:
                for code in VEventStatusCode:
                    if match_details.match.statistic.get_statistics(code):
                        self._statistic_box.addItem(get_event_status_name(code, AppLang.code), code)

                self._statistic_box.setCurrentText(get_event_status_name(VEventStatusCode.FULL_TIME, AppLang.code))

            statistic = QGroupBox(self.tr("Статистика"), self)
            layout.addRow(statistic)

            statistic_layout = QFormLayout(statistic, horizontalSpacing=10, verticalSpacing=10)
            statistic_layout.addRow(self.tr("Событие:"), self._statistic_box)
            statistic_layout.addRow(self._statistics)

        if match_details.match.league.tables:
            self._table = TableWidget(parent=self)
            self._table.horizontalHeader().setMinimumSectionSize(150)

            self._table_box = QComboBox(self)
            self._table_box.installEventFilter(self.wheel_blocker)
            self._table_box.currentIndexChanged.connect(self._changed_table)

            for game_code in GameCode:
                self._table_box.addItem(get_game_name(game_code, AppLang.code), game_code)

            table = QGroupBox(self.tr("Турнирная таблица"), self)
            layout.addRow(table)

            table_layout = QFormLayout(table, horizontalSpacing=10, verticalSpacing=10)
            table_layout.addRow(self.tr("Таблица:"), self._table_box)
            table_layout.addRow(self._table)

            self._table_box.setCurrentText(get_game_name(GameCode.TOTAL, AppLang.code))

        if match_details.h2h:
            self._h2h = H2HWidget(parent=self)
            self._h2h.horizontalHeader().setMinimumSectionSize(150)
            self._h2h.setMinimumHeight(250)

            self._team_box = QComboBox(self)
            self._team_box.installEventFilter(self.wheel_blocker)
            self._team_box.currentIndexChanged.connect(self._changed_h2h)

            self._game_box = QComboBox(self)
            self._game_box.installEventFilter(self.wheel_blocker)
            self._game_box.currentIndexChanged.connect(self._changed_h2h)

            self._encounter_box = QComboBox(self)
            self._encounter_box.installEventFilter(self.wheel_blocker)
            self._encounter_box.currentIndexChanged.connect(self._changed_h2h)

            for team_code in TeamCode:
                self._team_box.addItem(get_team_name(team_code, AppLang.code), team_code)

            for game_code in GameCode:
                self._game_box.addItem(get_game_name(game_code, AppLang.code), game_code)

            for encounter_code in EncounterCode:
                self._encounter_box.addItem(get_encounter_name(encounter_code, AppLang.code), encounter_code)

            h2h = QGroupBox(self.tr("H2H"), self)
            layout.addRow(h2h)

            h2h_layout = QFormLayout(h2h, horizontalSpacing=10, verticalSpacing=10)
            h2h_layout.addRow(self.tr("Игра:"), self._game_box)
            h2h_layout.addRow(self.tr("Команда:"), self._team_box)
            h2h_layout.addRow(self.tr("Тип:"), self._encounter_box)
            h2h_layout.addRow(self._h2h)

            self._team_box.setCurrentText(get_team_name(TeamCode.HOME, AppLang.code))
            self._game_box.setCurrentText(get_game_name(GameCode.TOTAL, AppLang.code))
            self._encounter_box.setCurrentText(get_encounter_name(EncounterCode.REGULAR_GAME, AppLang.code))

        if match_details.match.home_team.players or match_details.match.away_team.players:
            self._teams = TeamWidget(parent=self)
            self._teams.horizontalHeader().setMinimumSectionSize(150)
            self._teams.setMinimumHeight(250)

            self._players_box = QComboBox(self)
            self._players_box.installEventFilter(self.wheel_blocker)
            self._players_box.currentIndexChanged.connect(self._changed_players)

            self._players_type_box = QComboBox(self)
            self._players_type_box.installEventFilter(self.wheel_blocker)
            self._players_type_box.currentIndexChanged.connect(self._changed_players)

            for team_code in TeamCode:
                self._players_box.addItem(get_team_name(team_code, AppLang.code), team_code)

            for player_code in PlayerCode:
                self._players_type_box.addItem(get_players_name(player_code, AppLang.code), player_code)

            players = QGroupBox(self.tr("Составы"), self)
            layout.addRow(players)

            players_layout = QFormLayout(players, horizontalSpacing=10, verticalSpacing=10)
            players_layout.addRow(self.tr("Команда:"), self._players_box)
            players_layout.addRow(self.tr("Тип:"), self._players_type_box)
            players_layout.addRow(self._teams)

            self._players_box.setCurrentText(get_team_name(TeamCode.HOME, AppLang.code))
            self._players_type_box.setCurrentText(get_players_name(PlayerCode.PLAYERS, AppLang.code))

    @Slot()
    def _changed_table(self, index: int) -> None:
        gam_code = self._table_box.itemData(index)
        if table := self._match_details.match.league.get_table(gam_code):
            self._table.set_items(table.rows)
        else:
            self._table.clear()

    @Slot()
    def _changed_statistics(self, index: int) -> None:
        status_code = self._statistic_box.itemData(index)
        if statistics := self._match_details.match.statistic.get_statistics(status_code):
            self._statistics.set_items(statistics)
        else:
            self._statistics.clear()

    @Slot()
    def _changed_h2h(self, /) -> None:
        if reports := self._match_details.h2h.get_match_reports(
            team_code=self._team_box.currentData(),
            game_code=self._game_box.currentData(),
            encounter_code=self._encounter_box.currentData()
        ):
            self._h2h.set_items(reports)
        else:
            self._h2h.clear()

    @Slot()
    def _changed_players(self, /) -> None:
        if self._players_box.currentData() == TeamCode.HOME:
            team = self._match_details.match.home_team
        else:
            team = self._match_details.match.away_team

        if self._players_type_box.currentData() == PlayerCode.PLAYERS:
            players = team.players
        else:
            players = team.substitutes

        if players:
            self._teams.set_items(players)
        else:
            self._teams.clear()
