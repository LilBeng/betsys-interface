import logging
import uuid
from typing import Optional

from PySide6.QtCore import QPoint, Slot, Qt
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QWidget, QTabWidget, QLineEdit, QMenu
from betsys import DBContext, LeagueFilter, MatchDetailsFilter, MatchFilterDBModel, MatchCode
from qasync import asyncSlot

from src.dialogs.dao import BaseDAODialog
from src.widgets.editor import MatchFilterEditorWidget
from src.widgets.table import MatchFilterTableWidget

_logger = logging.getLogger(__name__)


class MatchFilterDAODialog(BaseDAODialog):
    def __init__(self, db_context: DBContext, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(
            db_context,
            MatchFilterTableWidget,
            self.tr("БД Фильтры"),
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
        self.splitter.addWidget(self.tab_widget)

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

    @Slot()
    def close_tab(self, index: int) -> None:
        self.tab_widget.removeTab(index)

        if not self.tab_widget.count():
            self.tab_widget.setVisible(False)
            self._search_input.setEnabled(True)
            self.central_widget.setEnabled(True)
            self.enabled_actions(True)

    @Slot()
    def on_search(self, text: str) -> None:
        if text.strip():
            self.central_widget.filter_table_rows(text)
        else:
            self.central_widget.show_all_rows()

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
    def edit_models(self) -> None:
        if models := self.central_widget.get_selected_models():
            self.started()

            for index, model in enumerate(models):
                self.add_tab(model)

                self.update_progress.emit(index, len(models))

            self.finished()

        else:
            self.show_message(self.tr("Нет выбранных объектов"))

    @asyncSlot()
    async def delete_models(self) -> None:
        if models := self.central_widget.get_selected_models():
            self.started()

            for index, model in enumerate(models, start=1):
                flag = await self.db_context.filters.delete(id=model.id)
                if flag:
                    self.central_widget.delete_item(model)
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
            flag = await self.db_context.filters.delete(True)
            if flag:
                self.central_widget.clear()
            else:
                _logger.error("Failed to remove models")
                self.show_message(self.tr("Не удалось выполнить операцию"))
        else:
            self.show_message(self.tr("Нет объектов"))

    @Slot()
    def create_model(self) -> None:
        league_filter = LeagueFilter()
        match_details_filter = MatchDetailsFilter()

        model = MatchFilterDBModel(
            id=str(uuid.uuid4()),
            description=str(),
            match_code=MatchCode.FOOTBALL,
            league_filter=league_filter.compress(),
            match_details_filter=match_details_filter.compress()
        )

        self.add_tab(model)

    @asyncSlot()
    async def _update_model(self, model: MatchFilterDBModel) -> None:
        try:
            flag = await self.db_context.filters.update(
                {"id": model.id},
                match_code=model.match_code,
                description=model.description,
                league_filter=model.league_filter,
                match_details_filter=model.match_details_filter
            )
            if flag:
                self.central_widget.update_item(model)
            else:
                _logger.error(f"Model (id={model.id}) - failed to update")
                self.show_message(self.tr("Не удалось выполнить операцию"))
        except Exception as exception:
            _logger.exception(exception)

    @asyncSlot()
    async def _save_model(self, model: MatchFilterDBModel) -> None:
        if self.central_widget.check_model(model):
            await self._update_model(model)
        else:
            flag = await self.db_context.filters.add(
                id=model.id,
                description=model.description,
                match_code=model.match_code,
                league_filter=model.league_filter,
                match_details_filter=model.match_details_filter
            )

            if flag:
                self.central_widget.add_item(model)
            else:
                _logger.error(f"Model (id={model.id}) - failed to update")
                self.show_message(self.tr("Не удалось выполнить операцию"))

    @asyncSlot()
    async def update_table(self, batch_size: int = 10) -> None:
        self.started()

        filters = await self.get_filters(batch_size)

        self.central_widget.set_items(filters)

        self.finished()

        self.show_message(self.tr("Данные обновлены"))

    def add_tab(self, model: MatchFilterDBModel) -> None:
        widget = MatchFilterEditorWidget(model)
        widget.save_model_signal.connect(self._save_model)

        self.tab_widget.addTab(widget, model.id)
        self.tab_widget.setVisible(True)
        self._search_input.setEnabled(False)
        self.central_widget.setEnabled(False)
        self.enabled_actions(False)
