from typing import Any, Optional

from PySide6.QtCore import Signal, Slot, QSize, Qt
from PySide6.QtGui import QIcon, QScreen
from PySide6.QtWidgets import QDialog, QApplication, QStatusBar, QProgressBar, QVBoxLayout, QToolBar, QWidget, QSplitter
from betsys import DBContext, LeagueDBModel, ScriptDBModel, AIPromptDBModel, MatchDetailsDBModel, MatchFilterDBModel


class BaseDAODialog(QDialog):

    update_progress = Signal(int, int)
    start_update = Signal()

    def __init__(
            self,
            db_context: DBContext,
            central_widget: Any,
            title: str,
            icon: QIcon,
            parent: Optional[QWidget] = None,
            *args,
            **kwargs
    ) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self.db_context = db_context
        self.central_widget = central_widget(self)

        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle(title)
        self.setWindowIcon(icon)

        self.setGeometry(0, 0, 800, 600)

        geo = self.frameGeometry()
        geo.moveCenter(QScreen.availableGeometry(QApplication.primaryScreen()).center())
        self.move(geo.topLeft())

        self._status_bar = QStatusBar(self)

        self._progress = QProgressBar(self)

        self._status_bar.addPermanentWidget(self._progress)

        self.toolbar = QToolBar(iconSize=QSize(35, 35), parent=self)

        self.central_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)

        self.splitter.addWidget(self.central_widget)

        self.central_layout.addWidget(self.splitter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addLayout(self.central_layout)
        layout.addWidget(self._status_bar)

        self.update_progress.connect(self._update_progress)

    def started(self) -> None:
        self.enabled_actions(False)
        self.central_layout.setEnabled(False)
        self._progress.setVisible(True)

    def finished(self) -> None:
        self.enabled_actions(True)
        self.central_layout.setEnabled(True)
        self._progress.setVisible(False)

    def show_message(self, message: str, timeout: int = 2000) -> None:
        """
        Показать сообщение.

        :param message: Сообщение.
        :param timeout: Таймаут.
        """
        self._status_bar.showMessage(message, timeout)

    def enabled_actions(self, flag: bool) -> None:
        for action in self.toolbar.actions():
            action.setEnabled(flag)

    async def _get(self, db_table: Any, batch_size: int = 50) -> Any:
        total = await db_table.get_count()
        objects = []

        if total:
            async for batch in db_table.get_batch(batch_size):
                objects.extend(batch)
                self.update_progress.emit(len(objects), total)

        return objects

    async def get_leagues(self, batch_size: int = 50) -> list[LeagueDBModel]:
        return await self._get(self.db_context.leagues, batch_size)

    async def get_scripts(self, batch_size: int = 10) -> list[ScriptDBModel]:
        return await self._get(self.db_context.scripts, batch_size)

    async def get_prompts(self, batch_size: int = 10) -> list[AIPromptDBModel]:
        return await self._get(self.db_context.prompts, batch_size)

    async def get_filters(self, batch_size: int = 10) -> list[MatchFilterDBModel]:
        return await self._get(self.db_context.filters, batch_size)

    async def get_matches(self, batch_size: int = 50) -> list[MatchDetailsDBModel]:
        return await self._get(self.db_context.details, batch_size)

    @Slot()
    def _update_progress(self, value: int, max_value: int) -> None:
        self._progress.setMaximum(max_value)

        self._progress.setValue(value)
