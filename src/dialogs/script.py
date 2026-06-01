import logging
import uuid

from PySide6.QtCore import Qt, Slot, QPoint
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMenu, QTabWidget, QLineEdit
from betsys import (
    DBContext,
    ScriptDBModel,
    Script,
    MatchCode,
    BetCode,
    SignalTypeCode
)
from qasync import asyncSlot

from src.dialogs.dao import BaseDAODialog
from src.utils.cache import DataCache
from src.widgets.editor import ScriptEditorWidget
from src.widgets.table import ScriptTableWidget

_logger = logging.getLogger(__name__)


class ScriptDAODialog(BaseDAODialog):
    def __init__(self, db_context: DBContext, *args, **kwargs) -> None:
        super().__init__(
            db_context,
            ScriptTableWidget,
            self.tr("БД Сценарии"),
            QIcon(":/resources/icons/dao.png"),
            *args,
            **kwargs
        )

        self._create_action = QAction(
            QIcon(":/resources/icons/create.png"),
            self.tr("Создать"),
            self
        )

        self._copy_action = QAction(
            QIcon(":/resources/icons/copy.png"),
            self.tr("Копировать"),
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
        self.toolbar.addAction(self._copy_action)
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
        self._copy_action.triggered.connect(self.copy_models)
        self._delete_action.triggered.connect(self.delete_models)
        self._remove_action.triggered.connect(self.remove_models)
        self._update_action.triggered.connect(self.start_update.emit)

        self.start_update.emit()

    @asyncSlot()
    async def _create_model(self, model: ScriptDBModel) -> None:
        try:
            flag = await self.db_context.scripts.add(
                id=model.id,
                description=model.description,
                match_code=model.match_code,
                signal_type_code=model.signal_type_code,
                bet_code=model.bet_code,
                is_active=model.is_active,
                obj=model.obj
            )
            if flag:
                self.central_widget.add_item(model)
            else:
                _logger.error(f"Model (id={model.id}) - failed to create")
                self.show_message(self.tr("Не удалось выполнить операцию"))
        except Exception as exception:
            _logger.exception(exception)

    @asyncSlot()
    async def _update_model(self, model: ScriptDBModel) -> None:
        try:
            flag = await self.db_context.scripts.update(
                {"id": model.id},
                description=model.description,
                match_code=model.match_code,
                signal_type_code=model.signal_type_code,
                bet_code=model.bet_code,
                is_active=model.is_active,
                obj=model.obj
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

        scripts = await self.get_scripts(batch_size)

        self.central_widget.set_items(scripts)

        if not DataCache.leagues:
            DataCache.leagues = await self.get_leagues(batch_size)

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
        model = ScriptDBModel(
            id=str(uuid.uuid4()),
            description=str(),
            match_code=MatchCode.FOOTBALL,
            signal_type_code=SignalTypeCode.PRE_MATCH,
            bet_code=BetCode.BOTH_TO_SCORE,
            is_active=True,
            obj=None
        )

        self.add_tab(model)

    @asyncSlot()
    async def copy_models(self) -> None:
        if models := self.central_widget.get_selected_models():
            self.started()

            for index, model in enumerate(models, start=1):
                script = Script.decompress(model.obj)
                script.script_id = str(uuid.uuid4())

                flag = await self.db_context.scripts.add_script(script)
                if flag:
                    new_model = ScriptDBModel(
                        id=script.script_id,
                        description=script.description,
                        match_code=script.match_code,
                        signal_type_code=script.signal_property.signal_type_code,
                        bet_code=script.signal_property.bet.bet_code,
                        is_active=script.is_active,
                        obj=script.compress()
                    )

                    self.central_widget.add_item(new_model)
                else:
                    _logger.error(f"Model (id={model.id}) - failed to copy")
                    self.show_message(self.tr("Не удалось выполнить операцию"))

                self.update_progress.emit(index, len(models))

            self.finished()
        else:
            self.show_message(self.tr("Нет выбранных объектов"))

    @asyncSlot()
    async def delete_models(self) -> None:
        if models := self.central_widget.get_selected_models():
            self.started()

            for index, model in enumerate(models, start=1):
                flag = await self.db_context.scripts.delete(id=model.id)
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
            flag = await self.db_context.scripts.delete(True)
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
                    self._copy_action,
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

    @Slot()
    def _save_model(self, model: ScriptDBModel) -> None:
        if self.central_widget.check_model(model):
            self._update_model(model)
        else:
            self._create_model(model)

    @Slot()
    def on_search(self, text: str) -> None:
        if text.strip():
            self.central_widget.filter_table_rows(text)
        else:
            self.central_widget.show_all_rows()

    def add_tab(self, model: ScriptDBModel) -> None:
        widget = ScriptEditorWidget(model)
        widget.save_model_signal.connect(self._save_model)

        self.tab_widget.addTab(widget, model.id)
        self.tab_widget.setVisible(True)
        self._search_input.setEnabled(False)
        self.central_widget.setEnabled(False)
        self.enabled_actions(False)
