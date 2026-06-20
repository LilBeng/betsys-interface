import logging
import uuid
from typing import Optional

from PySide6.QtCore import Qt, Slot, QPoint
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMenu, QTabWidget, QLineEdit, QWidget
from betsys import DBContext, AIPromptDBModel, MatchCode, SignalTypeCode, BetCode
from qasync import asyncSlot

from src.dialogs.dao import BaseDAODialog
from src.widgets.editor import PromptEditorWidget
from src.widgets.table import PromptTableWidget

_logger = logging.getLogger(__name__)


class PromptDAODialog(BaseDAODialog):
    def __init__(self, db_context: DBContext, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(
            db_context,
            PromptTableWidget,
            self.tr("БД Промты"),
            QIcon(":/resources/icons/dao.png"),
            parent,
            *args,
            **kwargs
        )

        self._create_action = QAction(
            QIcon(":/resources/icons/create.png"),
            self.tr("Создать"),
            self
        )

        self._edit_action = QAction(
            QIcon(":/resources/icons/edit.png"),
            self.tr("Редактировать"),
            self
        )

        self._delete_action = QAction(
            QIcon(":/resources/icons/delete.png"),
            self.tr("Удалить"),
            self
        )

        self._remove_action = QAction(
            QIcon(":/resources/icons/remove.png"),
            self.tr("Очистить"),
            self
        )

        self._update_action = QAction(
            QIcon(":/resources/icons/update.png"),
            self.tr("Обновить"),
            self
        )

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setVisible(False)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        self._search_input = QLineEdit(self)
        self._search_input.setPlaceholderText(self.tr("Введите текст для поиска ..."))
        self._search_input.textChanged.connect(self.on_search)

        self.central_layout.addWidget(self._search_input)
        self.central_layout.addWidget(self.tab_widget, alignment=Qt.AlignmentFlag.AlignBottom)

        self.central_widget.cellDoubleClicked.connect(self.edit_models)

        self.toolbar.addAction(self._create_action)
        self.toolbar.addAction(self._edit_action)
        self.toolbar.addAction(self._delete_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self._remove_action)
        self.toolbar.addAction(self._update_action)

        self.start_update.connect(self.update_table)

        self.central_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.central_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.central_widget.update_progress.connect(self.update_progress.emit)
        self.central_widget.show_message.connect(self.show_message)

        self._create_action.triggered.connect(self.create_model)
        self._edit_action.triggered.connect(self.edit_models)
        self._delete_action.triggered.connect(self.delete_models)
        self._remove_action.triggered.connect(self.remove_models)
        self._update_action.triggered.connect(self.start_update.emit)

        self.start_update.emit()

    @asyncSlot()
    async def _create_model(self, model: AIPromptDBModel) -> None:
        try:
            obj = await self.db_context.prompts.get_prompt(
                model.number,
                model.bet_code,
                model.match_code,
                model.signal_type_code
            )
            if obj:
                if obj.id != model.id:
                    _logger.error(f"Model (id={model.id}) - failed to update, key already exists")
                    self.show_message(self.tr("Не удалось выполнить операцию, ключ уже занят"))
                    return

            flag = await self.db_context.prompts.add_prompt(
                id=model.id,
                number=model.number,
                bet_code=model.bet_code,
                match_code=model.match_code,
                signal_type_code=model.signal_type_code,
                text=model.text,
                bet_name_flag=model.bet_name_flag,
                league_name_flag=model.league_name_flag,
                home_name_flag=model.home_name_flag,
                away_name_flag=model.away_name_flag,
                match_date_flag=model.match_date_flag,
                table_total_flag=model.table_total_flag,
                is_playing_teams=model.is_playing_teams,
                table_home_flag=model.table_home_flag,
                is_playing_home=model.is_playing_home,
                table_away_flag=model.table_away_flag,
                is_playing_away=model.is_playing_away,
                home_matches_flag=model.home_matches_flag,
                count_home_matches=model.count_home_matches,
                away_matches_flag=model.away_matches_flag,
                count_away_matches=model.count_away_matches,
                h2h_matches_flag=model.h2h_matches_flag,
                count_h2h_matches=model.count_h2h_matches,
                home_team_players_flag=model.home_team_players_flag,
                home_team_substitutes_flag=model.home_team_substitutes_flag,
                away_team_players_flag=model.away_team_players_flag,
                away_team_substitutes_flag=model.away_team_substitutes_flag
            )
            if flag:
                self.central_widget.add_item(model)
            else:
                _logger.error(f"Model (id={model.id}) - failed to create")
                self.show_message(self.tr("Не удалось выполнить операцию"))
        except Exception as exception:
            _logger.exception(exception)

    @asyncSlot()
    async def _update_model(self, model: AIPromptDBModel) -> None:
        try:
            obj = await self.db_context.prompts.get_prompt(
                model.number,
                model.bet_code,
                model.match_code,
                model.signal_type_code
            )
            if obj:
                if obj.id != model.id:
                    _logger.error(f"Model (id={model.id}) - failed to update, key already exists")
                    self.show_message(self.tr("Не удалось выполнить операцию, ключ уже занят"))
                    return

            flag = await self.db_context.prompts.update(
                {"id": model.id},
                number=model.number,
                bet_code=model.bet_code,
                match_code=model.match_code,
                signal_type_code=model.signal_type_code,
                text=model.text,
                bet_name_flag=model.bet_name_flag,
                league_name_flag=model.league_name_flag,
                home_name_flag=model.home_name_flag,
                away_name_flag=model.away_name_flag,
                match_date_flag=model.match_date_flag,
                table_total_flag=model.table_total_flag,
                is_playing_teams=model.is_playing_teams,
                table_home_flag=model.table_home_flag,
                is_playing_home=model.is_playing_home,
                table_away_flag=model.table_away_flag,
                is_playing_away=model.is_playing_away,
                home_matches_flag=model.home_matches_flag,
                count_home_matches=model.count_home_matches,
                away_matches_flag=model.away_matches_flag,
                count_away_matches=model.count_away_matches,
                h2h_matches_flag=model.h2h_matches_flag,
                count_h2h_matches=model.count_h2h_matches,
                home_team_players_flag=model.home_team_players_flag,
                home_team_substitutes_flag=model.home_team_substitutes_flag,
                away_team_players_flag=model.away_team_players_flag,
                away_team_substitutes_flag=model.away_team_substitutes_flag
            )
            if flag:
                self.central_widget.update_item(model)
            else:
                _logger.error(f"Model (id={model.id}) - failed to update")
                self.show_message(self.tr("Не удалось выполнить операцию"))
        except Exception as exception:
            _logger.exception(exception)

    @asyncSlot()
    async def update_table(self, batch_size: int = 10) -> None:
        self.started()

        prompts = await self.get_prompts(batch_size)

        self.central_widget.set_items(prompts)

        self.finished()

        self.show_message(self.tr("Данные обновлены"))

    @Slot()
    def edit_models(self) -> None:
        if models := self.central_widget.get_selected_models():
            self.started()

            for index, model in enumerate(models):
                self.add_tab(model)

                self.update_progress.emit(index, len(models))

            self.finished()

        else:
            self.show_message(self.tr("Нет выбранных объектов"))

    @Slot()
    def create_model(self) -> None:
        model = AIPromptDBModel(
            id=str(uuid.uuid4()),
            number=0,
            bet_code=BetCode.BOTH_TO_SCORE,
            match_code=MatchCode.FOOTBALL,
            signal_type_code=SignalTypeCode.PRE_MATCH,
            text=str()
        )

        self.add_tab(model)

    @asyncSlot()
    async def delete_models(self) -> None:
        if models := self.central_widget.get_selected_models():
            self.started()

            for index, model in enumerate(models, start=1):
                flag = await self.db_context.prompts.delete(id=model.id)
                if flag:
                    self.central_widget.remove_item(model)
                else:
                    _logger.error(f"Model (id={model.id}) - failed to delete")
                    self.show_message(self.tr("Не удалось выполнить операцию"))

                self.update_progress.emit(index, len(models))

            self.finished()
        else:
            self.show_message(self.tr("Нет выбранных объектов"))

    @asyncSlot()
    async def remove_models(self) -> None:
        if self.central_widget.rowCount():
            flag = await self.db_context.prompts.delete(True)
            if flag:
                self.central_widget.clear()
            else:
                _logger.error("Failed to remove models")
                self.show_message(self.tr("Не удалось выполнить операцию"))
        else:
            self.show_message(self.tr("Нет объектов"))

    @Slot()
    def show_context_menu(self, position: QPoint) -> None:
        """
        Показать контекстное меню.

        :param position: Позиция.
        """
        context_menu = QMenu(self)
        context_menu.addAction(self._create_action)

        if self.central_widget.get_selected_models():
            context_menu.addActions(
                [
                    self._edit_action,
                    self._delete_action
                ]
            )

        context_menu.addSeparator()

        context_menu.addActions(
            [
                self._remove_action,
                self._update_action
            ]
        )

        context_menu.exec(self.mapToGlobal(position))

    @Slot()
    def close_tab(self, index: int) -> None:
        self.tab_widget.removeTab(index)

        if not self.tab_widget.count():
            self.tab_widget.setVisible(False)
            self._search_input.setEnabled(True)
            self.central_widget.setEnabled(True)
            self.enabled_actions(True)

    @asyncSlot()
    async def _save_model(self, model: AIPromptDBModel) -> None:
        if self.central_widget.check_model(model):
            await self._update_model(model)
        else:
            await self._create_model(model)

    @Slot()
    def on_search(self, text: str) -> None:
        if text.strip():
            self.central_widget.filter_table_rows(text)
        else:
            self.central_widget.show_all_rows()

    def add_tab(self, model: AIPromptDBModel) -> None:
        widget = PromptEditorWidget(model)
        widget.save_model_signal.connect(self._save_model)

        self.tab_widget.addTab(widget, model.id)
        self.tab_widget.setVisible(True)
        self._search_input.setEnabled(False)
        self.central_widget.setEnabled(False)
        self.enabled_actions(False)
