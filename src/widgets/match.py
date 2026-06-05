from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QSpacerItem, QSizePolicy
from betsys import (
    MatchDetails,
    get_match_status_name,
    MatchStatusCode,
    get_global_event_name,
    GameCode,
    get_game_name,
    TeamCode,
    get_team_name,
    EncounterCode,
    get_encounter_name
)

from src.utils.lang import AppLang
from src.widgets.table import TableWidget, H2HWidget


class MatchDetailsWidget(QWidget):
    def __init__(self, match_details: MatchDetails, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._match_details = match_details

        teams = QLabel(f"{match_details.match.home_team.name} - {match_details.match.away_team.name}", parent=self)
        status = QLabel(get_match_status_name(match_details.match.match_summary.match_status_code, AppLang.code))

        layout = QFormLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addRow(self.tr("Страна:"), QLabel(match_details.match.league.country_name))
        layout.addRow(self.tr("Лига:"), QLabel(match_details.match.league.league_name))
        layout.addRow(self.tr("Матч:"), teams)
        layout.addRow(self.tr("Статус:"), status)

        if match_details.match.match_summary.match_status_code == MatchStatusCode.IN_PROGRESS:
            event = QLabel(get_global_event_name(match_details.match.match_summary.event_status_code, AppLang.code))
            layout.addRow(self.tr("Событие:"), event)

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
                layout.addRow(self.tr("Счет:"), score)

        if match_details.match.league.tables:
            self._table = TableWidget(parent=self)
            self._table.horizontalHeader().setMinimumSectionSize(150)

            self._table_box = QComboBox(self)
            self._table_box.currentIndexChanged.connect(self._changed_table)

            for game_code in GameCode:
                self._table_box.addItem(get_game_name(game_code, AppLang.code), game_code)

            layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
            layout.addRow(self.tr("Таблица:"), self._table_box)
            layout.addRow(self._table)

            self._table_box.setCurrentText(get_game_name(GameCode.TOTAL, AppLang.code))

        if match_details.h2h:
            self._h2h = H2HWidget(parent=self)
            self._h2h.horizontalHeader().setMinimumSectionSize(150)

            self._team_box = QComboBox(self)
            self._team_box.currentIndexChanged.connect(self._changed_h2h)

            self._game_box = QComboBox(self)
            self._game_box.currentIndexChanged.connect(self._changed_h2h)

            self._encounter_box = QComboBox(self)
            self._encounter_box.currentIndexChanged.connect(self._changed_h2h)

            for team_code in TeamCode:
                self._team_box.addItem(get_team_name(team_code, AppLang.code), team_code)

            for game_code in GameCode:
                self._game_box.addItem(get_game_name(game_code, AppLang.code), game_code)

            for encounter_code in EncounterCode:
                self._encounter_box.addItem(get_encounter_name(encounter_code, AppLang.code), encounter_code)

            layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
            layout.addRow(self.tr("Таблица:"), self._game_box)
            layout.addRow(self.tr("Команда:"), self._team_box)
            layout.addRow(self.tr("Тип:"), self._encounter_box)
            layout.addRow(self._h2h)

            self._team_box.setCurrentText(get_team_name(TeamCode.HOME, AppLang.code))
            self._game_box.setCurrentText(get_game_name(GameCode.TOTAL, AppLang.code))
            self._encounter_box.setCurrentText(get_encounter_name(EncounterCode.REGULAR_GAME, AppLang.code))

    @Slot()
    def _changed_table(self, index: int) -> None:
        gam_code = self._table_box.itemData(index)
        if table := self._match_details.match.league.get_table(gam_code):
            self._table.set_items(table.rows)
        else:
            self._table.clear()

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
