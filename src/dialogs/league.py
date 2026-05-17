import logging
from collections import defaultdict

from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from betsys import DBContext, LeagueDBModel, get_country_name, MatchCode
from qasync import asyncSlot

from src.dialogs.dao import BaseDAODialog
from src.utils.cache import DataCache
from src.utils.lang import AppLang

_logger = logging.getLogger(__name__)


class LeagueTreeWidget(QTreeWidget):
    update_progress = Signal(int, int)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.header().setVisible(False)

        self.itemChanged.connect(self._handle_item_changed)

    @property
    def active_ids(self) -> set[str]:
        league_ids = set()
        for index in range(self.topLevelItemCount()):
            top_level_item = self.topLevelItem(index)
            if top_level_item.childCount() > 0:
                for child_index in range(top_level_item.childCount()):
                    child_item = top_level_item.child(child_index)

                    league = child_item.data(0, Qt.ItemDataRole.UserRole)
                    if child_item.checkState(0) == Qt.CheckState.Checked:
                        league_ids.add(league.id)

            self.update_progress.emit(index, self.topLevelItemCount() - 1)

        return league_ids

    @property
    def changed_leagues(self) -> list[LeagueDBModel]:
        leagues = []
        for index in range(self.topLevelItemCount()):
            top_level_item = self.topLevelItem(index)
            if top_level_item.childCount() > 0:
                for child_index in range(top_level_item.childCount()):
                    child_item = top_level_item.child(child_index)
                    if child_item.checkState(0) == Qt.CheckState.Checked:
                        flag = True
                    else:
                        flag = False

                    league = child_item.data(0, Qt.ItemDataRole.UserRole)
                    if league.is_active != flag:
                        leagues.append(league)
                        league.is_active = flag

            self.update_progress.emit(index, self.topLevelItemCount() - 1)

        return leagues

    @Slot()
    def _handle_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        state = item.checkState(column)
        parent = item.parent()

        if parent is None:
            for index in range(item.childCount()):
                child = item.child(index)
                self.blockSignals(True)
                child.setCheckState(column, state)
                self.blockSignals(False)
        else:
            checked_children = sum(
                parent.child(index).checkState(column) == Qt.CheckState.Checked for index in range(parent.childCount())
            )

            self.blockSignals(True)
            if checked_children == 0:
                parent.setCheckState(0, Qt.CheckState.Unchecked)
            elif checked_children == parent.childCount():
                parent.setCheckState(0, Qt.CheckState.Checked)
            else:
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
            self.blockSignals(False)

    def set_items(self, initial_leagues: list[LeagueDBModel], active_ids: set[str]) -> None:
        self.clear()

        country_codes = defaultdict(list)
        for league in initial_leagues:
            country_codes[league.country_code].append(league)

        for index, (country_code, leagues) in enumerate(country_codes.items(), start=1):
            top_level_item = QTreeWidgetItem()
            top_level_item.setText(0, get_country_name(country_code, AppLang.code))
            top_level_item.setData(0, Qt.ItemDataRole.UserRole, country_code)

            flags = []
            for league in leagues:

                child_item = QTreeWidgetItem()
                child_item.setText(0, league.league_name)
                child_item.setData(0, Qt.ItemDataRole.UserRole, league)

                # Если есть список с идентификаторами активных лиг
                if active_ids:
                    if league.id in active_ids:
                        child_item.setCheckState(0, Qt.CheckState.Checked)
                    else:
                        child_item.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    child_item.setCheckState(0, Qt.CheckState.Checked if league.is_active else Qt.CheckState.Unchecked)

                flags.append(child_item.checkState(0) == Qt.CheckState.Checked)

                if league.match_code == MatchCode.FOOTBALL:
                    child_item.setIcon(0, QIcon(":/resources/icons/football.png"))
                elif league.match_code == MatchCode.HOCKEY:
                    child_item.setIcon(0, QIcon(":/resources/icons/hockey.png"))
                elif league.match_code == MatchCode.VOLLEYBALL:
                    child_item.setIcon(0, QIcon(":/resources/icons/volleyball.png"))

                self.expandItem(top_level_item)

                top_level_item.addChild(child_item)

            if all(flags):
                top_level_item.setCheckState(0, Qt.CheckState.Checked)
            elif all([not flag for flag in flags]):
                top_level_item.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                top_level_item.setCheckState(0, Qt.CheckState.PartiallyChecked)

            if top_level_item.childCount() > 0:
                self.addTopLevelItem(top_level_item)

            self.update_progress.emit(index, len(country_codes))

        self.sortItems(0, Qt.SortOrder.AscendingOrder)


class LeagueDAODialog(BaseDAODialog):

    def __init__(self, db_context: DBContext, *args, **kwargs) -> None:
        super().__init__(
            db_context,
            LeagueTreeWidget,
            self.tr("БД Лиги"),
            QIcon(":/resources/icons/dao.png"),
            *args,
            **kwargs
        )

        self._save_button = QAction(
            QIcon(":/resources/icons/save.png"),
            self.tr("Сохранить изменения"),
            self
        )

        self._update_button = QAction(
            QIcon(":/resources/icons/update.png"),
            self.tr("Обновить"),
            self
        )

        self._save_button.triggered.connect(self.save_leagues)
        self._update_button.triggered.connect(self.start_update.emit)

        self.toolbar.addAction(self._save_button)
        self.toolbar.addAction(self._update_button)

        self.start_update.connect(self.update_tree)

        self.start_update.emit()

    @asyncSlot()
    async def update_tree(self, batch_size: int = 50) -> None:
        self.started()

        DataCache.leagues = await self.get_leagues(batch_size)
        self.central_widget.set_items(DataCache.leagues, set())

        self.finished()

        self.show_message(self.tr("Данные обновлены"))

    @asyncSlot()
    async def save_leagues(self) -> None:
        self.started()

        if changed_leagues := self.central_widget.changed_leagues:
            for index, league in enumerate(changed_leagues, start=1):
                try:
                    await self.db_context.leagues.update({"id": league.id}, is_active=league.is_active)

                    self.update_progress.emit(index, len(changed_leagues))
                except Exception as exception:
                    _logger.exception(exception)

            self.show_message(self.tr("Данные сохранены"), 2000)
        else:
            self.show_message(self.tr("Нет данных для сохранения"), 2000)

        self.finished()
