from functools import partial
from typing import Optional

from PySide6.QtCore import QSize, Slot
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QStackedLayout, QComboBox, QFormLayout, QToolBar, QStatusBar, QProgressBar, QGroupBox, \
    QHBoxLayout, QWidget
from betsys import DBContext, BaseDAO
from betsys.db.database import check_tables_exist, create_tables
from qasync import asyncSlot

from src.dialogs.base import BaseDialog
from src.dialogs.config import LiteDBConfigBox, PostgresDBConfigBox
from src.widgets.switch import Switch


class TransferDialog(BaseDialog):
    update_progress = Signal(int, int)

    def __init__(self, db_context: DBContext, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self._db_context = db_context

        self.setWindowTitle(self.tr("Обмен данными"))
        self.setWindowIcon(QIcon(":/resources/icons/update.png"))

        self._stacked_layout = QStackedLayout()
        self._lite_config = LiteDBConfigBox(parent=self)
        self._postgres_config = PostgresDBConfigBox(parent=self)
        for widget in [self._lite_config, self._postgres_config]:
            self._stacked_layout.addWidget(widget)
        self._stacked_layout.setCurrentWidget(self._lite_config)

        self._db = QComboBox(self)
        for text in ["SQLite", "PostgreSQL"]:
            self._db.addItem(QIcon(":/resources/icons/dao.png"), text)
        self._db.setCurrentIndex(self._stacked_layout.currentIndex())
        self._db.currentIndexChanged.connect(self.change_index)

        self._conflict = QComboBox(self)
        for name, value in {self.tr("Пропустить"): False, self.tr("Заменить"): True}.items():
            self._conflict.addItem(name, value)

        self._scripts = Switch(size=QSize(50, 25), checked=True, parent=self)
        self._leagues = Switch(size=QSize(50, 25), checked=True, parent=self)
        self._matches = Switch(size=QSize(50, 25), checked=True, parent=self)
        self._signals = Switch(size=QSize(50, 25), checked=True, parent=self)
        self._prompts = Switch(size=QSize(50, 25), checked=True, parent=self)

        self._status_bar = QStatusBar(self)

        self._progress = QProgressBar(self)
        self._progress.setVisible(False)

        self._status_bar.addPermanentWidget(self._progress)

        self._toolbar = QToolBar(iconSize=QSize(35, 35), parent=self)

        self._import = QAction(
            QIcon(":/resources/icons/import.png"),
            self.tr("Импортировать"),
            self
        )
        self._export = QAction(
            QIcon(":/resources/icons/export.png"),
            self.tr("Экспортировать"),
            self
        )

        self._toolbar.addAction(self._import)
        self._toolbar.addAction(self._export)

        self._import.triggered.connect(partial(self._transfer_data, True))
        self._export.triggered.connect(partial(self._transfer_data, False))

        config_layout = QFormLayout()
        config_layout.setSpacing(10)
        config_layout.addRow(self.tr("База данных:"), self._db)
        config_layout.addRow(self.tr("Конфликт:"), self._conflict)

        data_layout = QFormLayout()
        data_layout.setSpacing(10)
        data_layout.addRow(self.tr("Сценарии:"), self._scripts)
        data_layout.addRow(self.tr("Лиги:"), self._leagues)
        data_layout.addRow(self.tr("Матчи:"), self._matches)
        data_layout.addRow(self.tr("Сигналы:"), self._signals)
        data_layout.addRow(self.tr("Промты:"), self._prompts)

        config = QGroupBox(self.tr("Конфигурация"), self)
        config.setLayout(config_layout)

        data = QGroupBox(self.tr("Данные"), self)
        data.setLayout(data_layout)

        layout = QHBoxLayout()
        layout.addLayout(self._stacked_layout)
        layout.addWidget(data)

        self._layout = QFormLayout(self)
        self._layout.setSizeConstraint(QFormLayout.SizeConstraint.SetFixedSize)
        self._layout.setSpacing(15)
        self._layout.addRow(self._toolbar)
        self._layout.addRow(config)
        self._layout.addRow(layout)
        self._layout.addRow(self._status_bar)

        self.update_progress.connect(self._update_progress)

    @property
    def context(self) -> Optional[DBContext]:
        widget = self._stacked_layout.currentWidget()
        if config := widget.config: # noqa
            return DBContext(config)

    @Slot()
    def change_index(self, index: int) -> None:
        self._stacked_layout.setCurrentIndex(index)

    @Slot()
    def _update_progress(self, value: int, max_value: int) -> None:
        self._progress.setMaximum(max_value)

        self._progress.setValue(value)

    def enabled_actions(self, flag: bool) -> None:
        for action in self._toolbar.actions():
            action.setEnabled(flag)

    def started(self) -> None:
        self.enabled_actions(False)
        self._progress.setVisible(True)

    def finished(self) -> None:
        self.enabled_actions(True)
        self._progress.setVisible(False)

    async def _transfer(self, source_dao: BaseDAO, target_dao, batch_size: int = 100) -> None:
        offset = 0
        total = await source_dao.get_count()

        async with source_dao.async_session_maker() as source_session:
            async with source_session.begin():
                async for batch in source_dao.get_batch(batch_size):

                    async with target_dao.async_session_maker() as target_session:
                        async with target_session.begin():
                            existing = await target_dao.check_existing(batch)
                            existing_ids = {model.id for model in existing}
                            models_to_insert = [model for model in batch if model.id not in existing_ids]
                            if models_to_insert:
                                await target_dao.add_all(models_to_insert)

                            if self._conflict.currentData():
                                await target_dao.update_all(existing)

                    offset += batch_size

                    self.update_progress.emit(offset, total)

    @asyncSlot()
    async def _transfer_data(self, import_data: bool, batch_size: int = 100) -> None:
        self.started()

        context = self.context
        if context:
            if await context.check_connection():
                if import_data:
                    if not await check_tables_exist(context.async_engine):
                        self.finished()
                        self._status_bar.showMessage(self.tr("БД не содержит выбранные таблицы"), 5000)
                        return None
                else:
                    await create_tables(context.async_engine)

                if import_data:
                    source = context
                    target = self._db_context
                else:
                    source = self._db_context
                    target = context

                if self._scripts.is_checked():
                    await self._transfer(source.scripts, target.scripts, batch_size)

                if self._leagues.is_checked():
                    await self._transfer(source.leagues, target.leagues, batch_size)

                if self._matches.is_checked():
                    await self._transfer(source.details, target.details, batch_size)

                if self._signals.is_checked():
                    await self._transfer(source.signals, target.signals, batch_size)

                if self._prompts.is_checked():
                    await self._transfer(source.prompts, target.prompts, batch_size)

                self._status_bar.showMessage(self.tr("Обмен данными завершен"), 5000)

                await context.async_engine.dispose()

            else:
                self._status_bar.showMessage(self.tr("Не удалось подключиться к БД"), 5000)
        else:
            self._status_bar.showMessage(self.tr("БД не выбрана"), 5000)

        self.finished()

