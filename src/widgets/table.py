import logging
from typing import Optional, Any

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QTableWidgetItem
from betsys import (
    ScriptDBModel,
    get_match_name,
    get_total_bet_name,
    AIPromptDBModel,
    get_signal_type_name,
    MatchDetails,
    get_match_status_name,
    get_table_headers,
    Row, get_h2h_headers,
    MatchReport, get_players_name, PlayerCode, Player
)

from src.utils.lang import AppLang
from src.utils.delegate import ResultDelegate

_logger = logging.getLogger(__name__)


class BaseTableWidget(QTableWidget):
    update_progress = Signal(int, int)
    show_message = Signal(str)

    def __init__(self, labels: list[str], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._labels = labels

        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)

        self.setSortingEnabled(True)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)

        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self._set_header_labels(self._labels)

    @property
    def models(self) -> list[Any]:
        models = []
        for row_index in range(self.rowCount()):
            item = self.item(row_index, 0)
            models.append(item.data(Qt.ItemDataRole.UserRole))
        return models

    def _set_header_labels(self, labels: list[str]) -> None:
        self.setColumnCount(len(labels))
        self.setRowCount(0)
        self.setHorizontalHeaderLabels(labels)

    def clear(self) -> None:
        super().clear()

        self._set_header_labels(self._labels)

    def get_selected_models(self) -> list[Any]:
        """
        Получить выделенные модели.

        :return: Список сценариев.
        """
        models = []
        for (min_range, max_range) in [(ranges.topRow(), ranges.bottomRow()) for ranges in self.selectedRanges()]:
            for index in range(min_range, max_range + 1):
                item = self.item(index, 0)
                if item:
                    models.append(item.data(Qt.ItemDataRole.UserRole))
                else:
                    _logger.error(f"Item not found (row index {index})")
        return models

    def get_row_index(self, model: Any) -> Optional[int]:
        """
        Получить номер строки в которой содержится модель.

        :param model: Сценарий.

        :return: Номер строки.
        """
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item:
                if item.data(Qt.ItemDataRole.UserRole).id == model.id:
                    return row
            else:
                _logger.error(f"Item not found (row index {row})")

    def remove_item(self, model: Any) -> None:
        row_index = self.get_row_index(model)
        self.removeRow(row_index)

        self.show_message.emit(self.tr("Модель [{}] удалена").format(model.id))

    def set_items(self, models: list[Any]) -> None:
        self.clear()

        for index, model in enumerate(models, start=1):
            self.add_item(model)
            self.update_progress.emit(index, len(models))

    def check_model(self, model: Any) -> bool:
        for row_index in range(self.rowCount()):
            item = self.item(row_index, 0)
            if item.data(Qt.ItemDataRole.DisplayRole) == model.id:
                return True

        return False

    def filter_table_rows(self, search_text: str) -> None:
        for row in range(self.rowCount()):
            found = False
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and search_text.lower() in item.text().lower():
                    found = True
                    break

            self.setRowHidden(row, not found)

    def show_all_rows(self) -> None:
        for row in range(self.rowCount()):
            self.setRowHidden(row, False)

    def add_item(self, model: Any) -> None:
        ...

    def update_item(self, model: Any) -> None:
        ...


class ScriptTableWidget(BaseTableWidget):

    def __init__(self, *args, **kwargs) -> None:
        labels = [
            self.tr("Идентификатор"),
            self.tr("Описание"),
            self.tr("Тип игры"),
            self.tr("Тип ставки"),
            self.tr("Тип сигнала"),
            self.tr("Активность")
        ]

        super().__init__(labels, *args, **kwargs)

    def add_item(self, model: ScriptDBModel) -> None:
        self.setSortingEnabled(False)

        self.insertRow(self.rowCount())

        for index, value in enumerate(
                [
                    model.id,
                    model.description,
                    get_match_name(model.match_code, AppLang.code),
                    get_total_bet_name(model.bet_code, AppLang.code),
                    get_signal_type_name(model.signal_type_code, AppLang.code),
                    self.tr("Да") if model.is_active else self.tr("Нет")
                ]
        ):
            item = QTableWidgetItem(value)
            item.setToolTip(value)
            item.setData(Qt.ItemDataRole.DisplayRole, value)
            item.setData(Qt.ItemDataRole.UserRole, model)

            self.setItem(self.rowCount() - 1, index, item)

        self.setSortingEnabled(True)

        self.show_message.emit(self.tr("Модель [{}] добавлена").format(model.id))

    def update_item(self, model: ScriptDBModel) -> None:
        row_index = self.get_row_index(model)

        for column_index, value in enumerate(
                [
                    model.id,
                    model.description,
                    get_match_name(model.match_code, AppLang.code),
                    get_total_bet_name(model.bet_code, AppLang.code),
                    get_signal_type_name(model.signal_type_code, AppLang.code),
                    self.tr("Да") if model.is_active else self.tr("Нет")
                ]
        ):
            item = self.item(row_index, column_index)
            item.setToolTip(value)
            item.setData(Qt.ItemDataRole.DisplayRole, value)
            item.setData(Qt.ItemDataRole.UserRole, model)

        self.show_message.emit(self.tr("Модель [{}] обновлена").format(model.id))


class PromptTableWidget(BaseTableWidget):

    def __init__(self, *args, **kwargs) -> None:
        labels = [
            self.tr("Идентификатор"),
            self.tr("Номер"),
            self.tr("Тип игры"),
            self.tr("Тип ставки"),
            self.tr("Тип сигнала")
        ]

        super().__init__(labels, *args, **kwargs)

    def add_item(self, model: AIPromptDBModel) -> None:
        self.setSortingEnabled(False)

        self.insertRow(self.rowCount())

        for index, value in enumerate(
                [
                    model.id,
                    model.number,
                    get_match_name(model.match_code, AppLang.code),
                    get_total_bet_name(model.bet_code, AppLang.code),
                    get_signal_type_name(model.signal_type_code, AppLang.code)
                ]
        ):
            item = QTableWidgetItem(value)
            item.setToolTip(str(value))
            item.setData(Qt.ItemDataRole.DisplayRole, value)
            item.setData(Qt.ItemDataRole.UserRole, model)

            self.setItem(self.rowCount() - 1, index, item)

        self.setSortingEnabled(True)

        self.show_message.emit(self.tr("Модель [{}] добавлена").format(model.id))

    def update_item(self, model: AIPromptDBModel) -> None:
        row_index = self.get_row_index(model)

        for column_index, value in enumerate(
                [
                    model.id,
                    model.number,
                    get_match_name(model.match_code, AppLang.code),
                    get_total_bet_name(model.bet_code, AppLang.code),
                    get_signal_type_name(model.signal_type_code, AppLang.code)
                ]
        ):
            item = self.item(row_index, column_index)
            item.setToolTip(str(value))
            item.setData(Qt.ItemDataRole.DisplayRole, value)
            item.setData(Qt.ItemDataRole.UserRole, model)

        self.show_message.emit(self.tr("Модель [{}] обновлена").format(model.id))


class MatchTableWidget(BaseTableWidget):

    def __init__(self, *args, **kwargs) -> None:
        labels = [
            self.tr("Идентификатор"),
            self.tr("Время начала"),
            self.tr("Страна"),
            self.tr("Лига"),
            self.tr("Хозяева"),
            self.tr("Гости"),
            self.tr("Статус")
        ]

        super().__init__(labels, *args, **kwargs)

    def get_row_index(self, model: MatchDetails) -> Optional[int]:
        """
        Получить номер строки в которой содержится модель.

        :param model: Сценарий.

        :return: Номер строки.
        """
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item:
                if item.data(Qt.ItemDataRole.UserRole).match.match_id == model.match.match_id:
                    return row
            else:
                _logger.error(f"Item not found (row index {row})")

    def remove_item(self, model: MatchDetails) -> None:
        row_index = self.get_row_index(model)
        self.removeRow(row_index)

        self.show_message.emit(self.tr("Модель [{}] удалена").format(model.match.match_id))

    def check_model(self, model: MatchDetails) -> bool:
        for row_index in range(self.rowCount()):
            item = self.item(row_index, 0)
            if item.data(Qt.ItemDataRole.DisplayRole) == model.match.match_id:
                return True

        return False

    def add_item(self, model: MatchDetails) -> None:
        self.setSortingEnabled(False)

        self.insertRow(self.rowCount())

        for index, value in enumerate(
                [
                    model.match.match_id,
                    model.match.match_summary.match_datetime.strftime("%d.%m.%Y %H:%M"),
                    model.match.league.country_name,
                    model.match.league.league_name,
                    model.match.home_team.name,
                    model.match.away_team.name,
                    get_match_status_name(model.match.match_summary.match_status_code, AppLang.code)
                ]
        ):
            item = QTableWidgetItem(value)
            item.setToolTip(str(value))
            item.setData(Qt.ItemDataRole.DisplayRole, value)
            item.setData(Qt.ItemDataRole.UserRole, model)

            self.setItem(self.rowCount() - 1, index, item)

        self.setSortingEnabled(True)

        self.show_message.emit(self.tr("Модель [{}] добавлена").format(model.match.match_id))

    def update_item(self, model: MatchDetails) -> None:
        row_index = self.get_row_index(model)

        for column_index, value in enumerate(
                [
                    model.match.match_id,
                    model.match.match_summary.match_datetime.strftime("%d.%m.%Y %H:%M"),
                    model.match.league.country_name,
                    model.match.league.league_name,
                    model.match.home_team.name,
                    model.match.away_team.name,
                    get_match_status_name(model.match.match_summary.match_status_code, AppLang.code)
                ]
        ):
            item = self.item(row_index, column_index)
            item.setToolTip(str(value))
            item.setData(Qt.ItemDataRole.DisplayRole, value)
            item.setData(Qt.ItemDataRole.UserRole, model)

        self.show_message.emit(self.tr("Модель [{}] обновлена").format(model.match.match_id))


class TableWidget(BaseTableWidget):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(get_table_headers(AppLang.code), *args, **kwargs)

        self.setItemDelegateForColumn(len(self._labels) - 1, ResultDelegate(self))

    def add_item(self, row: Row) -> None:
        self.setSortingEnabled(False)

        self.insertRow(self.rowCount())

        for index, value in enumerate(
                [
                    row.position,
                    row.team_name,
                    row.total_matches,
                    row.win_matches,
                    row.draw_matches,
                    row.loss_matches,
                    row.goals_scored,
                    row.goals_conceded,
                    row.points,
                    [form.result_code for form in row.team_form]
                ]
        ):
            if index != len(self._labels) - 1:
                item = QTableWidgetItem(value)
                item.setToolTip(str(value))
            else:
                item = QTableWidgetItem()

            item.setData(Qt.ItemDataRole.DisplayRole, value)
            item.setData(Qt.ItemDataRole.UserRole, value)

            self.setItem(self.rowCount() - 1, index, item)

        self.setSortingEnabled(True)


class H2HWidget(BaseTableWidget):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(get_h2h_headers(AppLang.code), *args, **kwargs)

        self.setItemDelegateForColumn(len(self._labels) - 1, ResultDelegate(self))

    def add_item(self, report: MatchReport) -> None:
        self.setSortingEnabled(False)

        self.insertRow(self.rowCount())

        for index, value in enumerate(
                [
                    report.home_team_name,
                    report.away_team_name,
                    report.match_datetime.strftime("%d/%m/%Y"),
                    report.league_name,
                    report.home_team_score,
                    report.away_team_score,
                    [report.result_code]
                ]
        ):
            if index != len(self._labels) - 1:
                item = QTableWidgetItem(value)
                item.setToolTip(str(value))
            else:
                item = QTableWidgetItem()

            item.setData(Qt.ItemDataRole.DisplayRole, value)
            item.setData(Qt.ItemDataRole.UserRole, value)

            self.setItem(self.rowCount() - 1, index, item)

        self.setSortingEnabled(True)


class TeamWidget(BaseTableWidget):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(get_h2h_headers(AppLang.code), *args, **kwargs)

        self.setItemDelegateForColumn(len(self._labels) - 1, ResultDelegate(self))

    def add_item(self, player: Player) -> None:
        self.setSortingEnabled(False)

        self.insertRow(self.rowCount())

        for index, value in enumerate(
                [
                    player.name,
                    player.rating
                ]
        ):
            item = QTableWidgetItem(value)
            item.setToolTip(str(value))
            item.setData(Qt.ItemDataRole.DisplayRole, value)
            item.setData(Qt.ItemDataRole.UserRole, value)

            self.setItem(self.rowCount() - 1, index, item)

        self.setSortingEnabled(True)
