import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QIcon, QTextCursor, QTextCharFormat, QColor, QAction
from PySide6.QtWidgets import QWidget, QComboBox, QVBoxLayout, QPlainTextEdit, QToolBar

from src.dialogs.error import ErrorDialog
from src.utils.colors import LEVEL_COLORS

_logger = logging.getLogger(__name__)


class Emitter(QObject):
    signal = Signal(str, int)


class QHandler(logging.Handler):
    def __init__(self, emitter: Emitter) -> None:
        super().__init__()
        self.emitter = emitter
        self.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        """
        Отправить сигнал.

        :param record: Запись лога.
        """
        msg = self.format(record)
        self.emitter.signal.emit(msg, record.levelno)


class LogWidget(QWidget):
    """
    Виджет логирования.
    """
    def __init__(self, max_lines: int, error_log_file: str, base_level: str = "INFO", *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._max_lines = max_lines
        self._error_log_file = Path(error_log_file)

        main_layout = QVBoxLayout(self)

        # Панель управления
        bar = QToolBar(self)
        self._level = QComboBox(self)

        level_names = {
            "DEBUG": self.tr("Отладка"),
            "INFO": self.tr("Информация"),
            "WARNING": self.tr("Внимание"),
            "ERROR": self.tr("Ошибка"),
            "CRITICAL":  self.tr("Критическая ошибка")
        }

        current_index = 0
        for index, [level_name, text] in enumerate(level_names.items()):
            self._level.addItem(text, level_name)
            if level_name == base_level:
                current_index = index

        self._level.currentIndexChanged.connect(self._change_log_level)
        self._level.setCurrentIndex(current_index)

        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setMaximumBlockCount(self._max_lines)

        bar.addWidget(self._level)

        clear = QAction(
            icon=QIcon(":/resources/icons/delete.png"),
            toolTip=self.tr("Очистить"),
            parent=self
        )
        clear.triggered.connect(self._text.clear)

        open_error = QAction(
            icon=QIcon(":/resources/icons/export.png"),
            toolTip=self.tr("Открыть файл с ошибками"),
            parent=self
        )
        open_error.triggered.connect(self._open_error_file)

        bar.addAction(open_error)
        bar.addAction(clear)

        main_layout.addWidget(bar)

        main_layout.addWidget(self._text)

        self._emitter = Emitter()
        self._emitter.signal.connect(self._append)

        handler = QHandler(self._emitter)

        root_logger = logging.getLogger()
        root_logger.setLevel(self._level.currentData())
        root_logger.addHandler(handler)

    @Slot()
    def _change_log_level(self, index: int) -> None:
        """
        Изменить уровень логирования.

        :param index: Индекс.
        """
        level_name = self._level.itemData(index)
        level = getattr(logging, level_name)
        logging.getLogger().setLevel(level)

    @Slot()
    def _open_error_file(self) -> None:
        dialog = ErrorDialog(str(self._error_log_file), self)
        dialog.exec()

    @Slot()
    def _append(self, message: str, level: int) -> None:
        """
        Добавить запись.

        :param message: Сообщение.
        :param level: Уровень.
        """
        if level >= logging.ERROR:
            try:
                with open(self._error_log_file, "a", encoding="utf-8") as file:
                    file.write(f"{message}\n")
            except Exception as exception:
                _logger.exception(exception)

        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        color_format = QTextCharFormat()
        color_format.setForeground(LEVEL_COLORS.get(level, QColor(0, 0, 0)))

        cursor.insertText(message + "\n", color_format)
        self._text.setTextCursor(cursor)
        self._text.ensureCursorVisible()
