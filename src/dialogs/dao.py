from typing import Any

from PySide6.QtCore import Signal, Slot, QSize, Qt
from PySide6.QtGui import QIcon, QScreen
from PySide6.QtWidgets import QDialog, QApplication, QStatusBar, QProgressBar, QVBoxLayout, QToolBar
from betsys import DBContext, LeagueDBModel, ScriptDBModel, AIPromptDBModel, MatchDetailsDBModel


class BaseDAODialog(QDialog):

    update_progress = Signal(int, int)
    start_update = Signal()

    def __init__(
            self,
            db_context: DBContext,
            central_widget: Any,
            title: str,
            icon: QIcon,
            *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
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
        self.central_layout.addWidget(self.central_widget)

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

    async def get_leagues(self, batch_size: int = 50) -> list[LeagueDBModel]:
        total = await self.db_context.leagues.get_count()
        leagues = []

        if total:
            async for batch in self.db_context.leagues.get_batch(batch_size):
                leagues.extend(batch)
                self.update_progress.emit(len(leagues), total)

        return leagues

    async def get_scripts(self, batch_size: int = 10) -> list[ScriptDBModel]:
        total = await self.db_context.scripts.get_count()
        scripts = []

        if total:
            async for batch in self.db_context.scripts.get_batch(batch_size):
                scripts.extend(batch)
                self.update_progress.emit(len(scripts), total)

        return scripts

    async def get_prompts(self, batch_size: int = 10) -> list[AIPromptDBModel]:
        total = await self.db_context.prompts.get_count()
        prompts = []

        if total:
            async for batch in self.db_context.prompts.get_batch(batch_size):
                prompts.extend(batch)
                self.update_progress.emit(len(prompts), total)

        return prompts

    async def get_matches(self, batch_size: int = 50) -> list[MatchDetailsDBModel]:
        total = await self.db_context.details.get_count()
        matches = []

        if total:
            async for batch in self.db_context.details.get_batch(batch_size):
                matches.extend(batch)
                self.update_progress.emit(len(matches), total)

        return matches

    @Slot()
    def _update_progress(self, value: int, max_value: int) -> None:
        self._progress.setMaximum(max_value)

        self._progress.setValue(value)
