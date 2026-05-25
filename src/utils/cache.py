from typing import Optional

from betsys import LeagueDBModel, MatchDetailsDBModel, MatchCode, MatchDetails

from src.utils.decorators import singleton


@singleton
class DataCache(object):
    leagues: list[LeagueDBModel] = []
    matches: list[MatchDetailsDBModel] = []
    details: list[MatchDetails] = []

    def clear(self) -> None:
        self.leagues.clear()
        self.matches.clear()
        self.details.clear()

    def get_leagues(self, match_code: MatchCode, is_active: Optional[bool] = None) -> list[LeagueDBModel]:
        models = []
        for model in self.leagues:
            if model.match_code == match_code and model.is_active == is_active:
                models.append(model)
        return models

    def get_matches(self, match_code: MatchCode) -> list[MatchDetailsDBModel]:
        models = []
        for model in self.matches:
            if model.match_code == match_code:
                models.append(model)
        return models

    def get_details(self, match_code: MatchCode) -> list[MatchDetails]:
        details = []
        for match_details in self.details:
            if match_details.match.match_code == match_code:
                details.append(match_details)
        return details
