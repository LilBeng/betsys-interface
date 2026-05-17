from typing import Optional

from betsys import LeagueDBModel, MatchDetailsDBModel, MatchCode

from src.utils.decorators import singleton


@singleton
class DataCache(object):
    leagues: list[LeagueDBModel] = []
    matches: list[MatchDetailsDBModel] = []

    def clear(self) -> None:
        self.leagues.clear()
        self.matches.clear()

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
