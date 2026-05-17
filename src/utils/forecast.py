import sys
from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as pysideSignal
from betsys import (
    MatchDetails,
    SignalProperty,
    ForecastCode,
    FEventStatusCode,
    Interval,
    HEventStatusCode,
    MatchCode,
    BetCode,
    TeamCode,
    Script,
    League,
    get_weekday_name,
    get_country_name, ScriptDBModel
)

from src.utils.cache import DataCache
from src.utils.lang import AppLang


class Forecast(QObject):
    send_message = pysideSignal(str)
    update_progress = pysideSignal(int, int)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._cache = DataCache()

    @staticmethod
    def forecast(match_details: MatchDetails, signal_property: SignalProperty) -> Optional[ForecastCode]:
        match signal_property.bet.event_status_code:
            case FEventStatusCode.FULL_TIME:
                interval = Interval(
                    min=0,
                    max=sys.maxsize
                )
            case FEventStatusCode.REGULAR_TIME:
                interval = Interval(
                    min=0,
                    max=90
                )
            case FEventStatusCode.FIRST_HALF:
                interval = Interval(
                    min=0,
                    max=45
                )
            case FEventStatusCode.SECOND_HALF:
                interval = Interval(
                    min=46,
                    max=sys.maxsize
                )
            case FEventStatusCode.AFTER_EXTRA_TIME:
                interval = Interval(
                    min=0,
                    max=sys.maxsize
                )
            case FEventStatusCode.AFTER_PENALTY_SHOOTOUT:
                interval = Interval(
                    min=0,
                    max=sys.maxsize
                )

            case HEventStatusCode.FULL_TIME:
                interval = Interval(
                    min=0,
                    max=sys.maxsize
                )

            case HEventStatusCode.REGULAR_TIME:
                interval = Interval(
                    min=0,
                    max=60
                )

            case HEventStatusCode.FIRST_PERIOD:
                interval = Interval(
                    min=0,
                    max=20
                )

            case HEventStatusCode.SECOND_PERIOD:
                interval = Interval(
                    min=21,
                    max=40
                )

            case HEventStatusCode.THIRD_PERIOD:
                interval = Interval(
                    min=41,
                    max=sys.maxsize
                )

            case HEventStatusCode.AFTER_EXTRA_TIME:
                interval = Interval(
                    min=0,
                    max=sys.maxsize
                )

            case HEventStatusCode.AFTER_PENALTY_SHOOTOUT:
                interval = Interval(
                    min=0,
                    max=sys.maxsize
                )

            case _:
                interval = Interval(
                    min=0,
                    max=0
                )

        # Для волейбола нет счета по времени (только сколько забито в каждом сете)
        if not signal_property.interval or match_details.match.match_code == MatchCode.VOLLEYBALL:
            # Если это тотал до минуты
            if signal_property.bet.bet_code == BetCode.OVER_UNDER:
                if signal_property.bet.up_to_time:
                    interval.max = signal_property.bet.up_to_time

                    if not match_details.match.statistic.score_statistics:
                        if (
                                match_details.match.match_summary.home_team_score == 0 and
                                match_details.match.match_summary.away_team_score == 0
                        ):
                            return ForecastCode.UNSUCCESSFUL
                        else:
                            return None

                    score_times = match_details.match.statistic.get_score_times(signal_property.bet.team_code)

                    times = []
                    for score_time in score_times:
                        if signal_property.interval.min <= score_time.minute <= interval.max:
                            times.append(score_time)

                    if signal_property.bet.is_over:
                        if signal_property.bet.value < len(times):
                            return ForecastCode.SUCCESSFUL
                        elif signal_property.bet.value == len(times):
                            return ForecastCode.REFUND
                        else:
                            return ForecastCode.UNSUCCESSFUL
                    else:
                        if signal_property.bet.value > len(times):
                            return ForecastCode.SUCCESSFUL
                        elif signal_property.bet.value == len(times):
                            return ForecastCode.REFUND
                        else:
                            return ForecastCode.UNSUCCESSFUL

            return signal_property.forecast(match_details.match)
        else:
            if signal_property.bet.bet_code in [BetCode.ODD_OR_EVEN, BetCode.ONE_X_TWO, BetCode.DOUBLE_CHANCE]:
                return signal_property.forecast(match_details.match)

            elif signal_property.bet.bet_code == BetCode.OVER_UNDER:
                if signal_property.bet.up_to_time:
                    if signal_property.interval.is_lies(signal_property.bet.up_to_time):
                        interval.max = signal_property.bet.up_to_time
                    else:
                        return None

                if interval.is_lies(signal_property.interval.min):

                    if not match_details.match.statistic.score_statistics:
                        if (
                                match_details.match.match_summary.home_team_score == 0 and
                                match_details.match.match_summary.away_team_score == 0
                        ):
                            return ForecastCode.UNSUCCESSFUL
                        else:
                            return None

                    score_times = match_details.match.statistic.get_score_times(signal_property.bet.team_code)
                    if score_times:
                        times = []
                        for score_time in score_times:
                            if signal_property.interval.min < score_time.minute <= interval.max:
                                times.append(score_time)
                    else:
                        home_score = match_details.match.match_summary.home_team_score
                        away_score = match_details.match.match_summary.away_team_score

                        if home_score is not None and away_score is not None:
                            if signal_property.bet.team_code == TeamCode.HOME:
                                score = home_score
                            elif signal_property.bet.team_code == TeamCode.AWAY:
                                score = away_score
                            else:
                                score = home_score + away_score

                            if score > 0:
                                return None
                            else:
                                times = []
                        else:
                            return None

                    if signal_property.bet.is_over:
                        if signal_property.bet.value < len(times):
                            return ForecastCode.SUCCESSFUL
                        elif signal_property.bet.value == len(times):
                            return ForecastCode.REFUND
                        else:
                            return ForecastCode.UNSUCCESSFUL
                    else:
                        if signal_property.bet.value > len(times):
                            return ForecastCode.SUCCESSFUL
                        elif signal_property.bet.value == len(times):
                            return ForecastCode.REFUND
                        else:
                            return ForecastCode.UNSUCCESSFUL
                else:
                    return None

            elif signal_property.bet.bet_code == BetCode.BOTH_TO_SCORE:
                if interval.is_lies(signal_property.interval.min):

                    if not match_details.match.statistic.score_statistics:
                        if (
                                match_details.match.match_summary.home_team_score == 0 and
                                match_details.match.match_summary.away_team_score == 0
                        ):
                            if signal_property.bet.is_both_to_score:
                                return ForecastCode.UNSUCCESSFUL
                            else:
                                return ForecastCode.SUCCESSFUL
                        else:
                            return None

                    score_times = []
                    for score_statistic in match_details.match.statistic.score_statistics:
                        if signal_property.bet.is_both_to_score:
                            if score_statistic.home_team_score >= 1 and score_statistic.away_team_score >= 1:
                                score_times.append(score_statistic.score_time)
                        else:
                            if score_statistic.home_team_score == 0 or score_statistic.away_team_score == 0:
                                score_times.append(score_statistic.score_time)

                    if score_times:
                        times = []
                        for score_time in score_times:
                            if signal_property.interval.min < score_time.minute <= interval.max:
                                times.append(score_time)
                    else:
                        home_score = match_details.match.match_summary.home_team_score
                        away_score = match_details.match.match_summary.away_team_score

                        if home_score is not None and away_score is not None:
                            if signal_property.bet.is_both_to_score:
                                if home_score >= 1 and away_score >= 1:
                                    return None
                                else:
                                    times = []
                            else:
                                if home_score == 0 or away_score == 0:
                                    return None
                                else:
                                    times = []
                        else:
                            return None

                    if signal_property.bet.is_both_to_score:
                        if times:
                            return ForecastCode.SUCCESSFUL
                        else:
                            return ForecastCode.UNSUCCESSFUL
                    else:
                        if times:
                            return ForecastCode.UNSUCCESSFUL
                        else:
                            return ForecastCode.SUCCESSFUL

                else:
                    return None
            else:
                return signal_property.forecast(match_details.match)

    def run(self, script_model: ScriptDBModel, weekdays_info: bool = True, leagues_info: bool = True) -> None:
        self.send_message.emit(
            self.tr("\nНачало анализа: {}\n").format(datetime.today().strftime("%d.%m.%Y, %H:%M:%S"))
        )

        script = Script.decompress(script_model.obj)

        self.send_message.emit(self.tr("Сценарий: {}").format(script.script_id))
        self.send_message.emit(self.tr("Информация по дням недели: {}").format(weekdays_info))
        self.send_message.emit(self.tr("Информация по лигам: {}").format(leagues_info))

        matches = []
        flags = []
        errors = []

        weekdays_flags = []
        leagues_flags = []

        leagues = self._cache.get_leagues(script.match_code, True)
        models = self._cache.get_matches(script.match_code)

        self.send_message.emit(self.tr("Количество лиг: {}").format(len(leagues)))
        self.send_message.emit(self.tr("Количество матчей: {}").format(len(models)))

        for index, model in enumerate(models, start=1):
            match_details = MatchDetails.decompress(model.obj)

            # Если указаны лиги
            if not script.validate_league(match_details):
                del match_details
                continue

            # Если указаны дни недели
            if not script.validate_weekdays(match_details):
                del match_details
                continue

            if script.validate_match_details(match_details):
                matches.append(match_details)
            else:
                del match_details

            self.update_progress.emit(index, len(models))

        if matches:
            self.send_message.emit(self.tr("\n>>> Общие данные\n"))

            for index, match in enumerate(matches, start=1):
                code = self.forecast(match, script.signal_property)
                if code is not None:
                    flags.append(code)
                else:
                    errors.append(match)

                self.update_progress.emit(index, len(matches))

            if flags:
                if len(flags):
                    successful_value = int(100 * flags.count(ForecastCode.SUCCESSFUL) / len(flags))
                    refund_value = int(100 * flags.count(ForecastCode.REFUND) / len(flags))
                else:
                    successful_value = 0
                    refund_value = 0

                self.send_message.emit(
                    self.tr("Подошло по условиям - {}\nНет данных - {}\nПроходимость - {}%\nВозврат - {}%").format(
                        len(matches) - len(errors),
                        len(errors),
                        successful_value,
                        refund_value
                    )
                )

            if weekdays_info:
                weekdays_report = defaultdict(list)
                datetime_matches = defaultdict(list)

                for index, model in enumerate(matches, start=1):
                    datetime_matches[model.match.match_summary.match_datetime.date()].append(model)

                    self.update_progress.emit(index, len(matches))

                self.send_message.emit(self.tr("\n>>> Проходимость по дням недели\n"))

                years = defaultdict(lambda: defaultdict(list))
                for match_date, matches in datetime_matches.items():
                    calendar = match_date.isocalendar()

                    for index, model in enumerate(matches, start=1):
                        code = self.forecast(model, script.signal_property)
                        if code is not None:
                            weekdays_flags.append(code)

                        self.update_progress.emit(index, len(matches))

                    if len(weekdays_flags):
                        successful_value = int(
                            100 * weekdays_flags.count(ForecastCode.SUCCESSFUL) / len(weekdays_flags)
                        )
                        refund_value = int(100 * weekdays_flags.count(ForecastCode.REFUND) / len(weekdays_flags))
                    else:
                        successful_value = 0
                        refund_value = 0

                    if weekdays_flags:
                        if weekdays_flags.count(ForecastCode.REFUND):
                            text = self.tr("{} - Проход {}/{} [{}%], Возврат {}/{} [{}%]").format(
                                get_weekday_name(match_date.weekday(), AppLang.code),
                                weekdays_flags.count(ForecastCode.SUCCESSFUL),
                                len(weekdays_flags),
                                successful_value,
                                weekdays_flags.count(ForecastCode.REFUND),
                                len(weekdays_flags),
                                refund_value
                            )
                        else:
                            text = self.tr("{} - Проход {}/{} [{}%]").format(
                                get_weekday_name(match_date.weekday(), AppLang.code),
                                weekdays_flags.count(ForecastCode.SUCCESSFUL),
                                len(weekdays_flags),
                                successful_value
                            )

                        weekdays_report[match_date.weekday()].append(successful_value)

                        years[calendar.year][calendar.week].insert(match_date.weekday(), text)

                sorted_years = {key: years[key] for key in sorted(years)}
                for i, (number_year, weeks) in enumerate(sorted_years.items(), start=1):
                    sorted_weeks = {key: weeks[key] for key in sorted(weeks)}
                    for j, (number_week, days) in enumerate(sorted_weeks.items(), start=1):
                        self.send_message.emit(self.tr("{} год, неделя №{}").format(number_year, number_week))

                        for weekday in days:
                            self.send_message.emit(f"{weekday}")

                        if j != len(sorted_weeks.items()):
                            self.send_message.emit("")

                        self.update_progress.emit(j, len(sorted_weeks))

                    self.update_progress.emit(i, len(sorted_years))

                self.send_message.emit("\n>>> Итоговая сводка по дням недели\n")

                for weekday, reports in weekdays_report.items():
                    self.send_message.emit(f"{get_weekday_name(weekday, AppLang.code)} - {int(mean(reports))}%")

                del weekdays_report
                del datetime_matches

            if leagues_info:
                self.send_message.emit(self.tr("\n>>> Проходимость по лигам\n"))

                league_matches = defaultdict(list)
                for index, model in enumerate(matches, start=1):
                    league = League(
                        country_code=model.match.league.country_code,
                        country_name=model.match.league.country_name,
                        league_name=model.match.league.league_name,
                        league_id=model.match.league.league_id,
                        table_id=model.match.league.table_id,
                        season_id=model.match.league.season_id
                    )
                    league_matches[league].append(model)

                    self.update_progress.emit(index, len(matches))

                self.send_message.emit(self.tr("Подошло лиг: {}").format(len(league_matches)))

                country_codes = set(league.country_code for league in league_matches.keys())
                for i, country_code in enumerate(country_codes, start=1):

                    self.send_message.emit(self.tr("\nСтрана: {}").format(get_country_name(country_code, AppLang.code)))

                    for j, (league, matches) in enumerate(league_matches.items(), start=1):

                        self.update_progress.emit(j, len(league_matches))

                        if country_code == league.country_code:
                            for index, model in enumerate(matches, start=1):
                                code = self.forecast(model, script.signal_property)
                                if code is not None:
                                    leagues_flags.append(code)

                                self.update_progress.emit(index, len(matches))

                            if len(leagues_flags):
                                successful_value = int(
                                    100 * leagues_flags.count(ForecastCode.SUCCESSFUL) / len(leagues_flags)
                                )
                                refund_value = int(100 * leagues_flags.count(ForecastCode.REFUND) / len(leagues_flags))
                            else:
                                successful_value = 0
                                refund_value = 0

                            if leagues_flags:
                                if leagues_flags.count(ForecastCode.REFUND):
                                    text = self.tr("Лига: {} - Проход {}/{} [{}%], Возврат {}/{} [{}%]").format(
                                        league.league_name,
                                        leagues_flags.count(ForecastCode.SUCCESSFUL),
                                        len(leagues_flags),
                                        successful_value,
                                        leagues_flags.count(ForecastCode.REFUND),
                                        len(leagues_flags),
                                        refund_value
                                    )
                                else:
                                    text = self.tr("Лига: {} - Проход {}/{} [{}%]").format(
                                        league.league_name,
                                        leagues_flags.count(ForecastCode.SUCCESSFUL),
                                        len(leagues_flags),
                                        successful_value
                                    )

                                self.send_message.emit(text)

                    self.update_progress.emit(i, len(country_codes))

                del league_matches

        else:
            self.send_message.emit(self.tr("\nПодходящие матчи не обнаружены"))

        del matches
        del flags
        del weekdays_flags
        del leagues_flags
        del script

        self.send_message.emit(
            self.tr("\nКонец анализа: {}").format(datetime.today().strftime("%d.%m.%Y, %H:%M:%S"))
        )
