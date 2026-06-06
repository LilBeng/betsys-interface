import json
import logging
from typing import Any

from PySide6.QtCore import Qt, Signal as pysideSignal, QStandardPaths, Slot
from PySide6.QtGui import QAction, QIcon, QFont
from PySide6.QtGui import QTextCursor, QKeyEvent
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget, QFileDialog
from PySide6.QtWidgets import QToolBar
from betsys import DriverCode, CheckPoint, BetSysModel

from src.utils.service import SportEventService

_logger = logging.getLogger(__name__)


class ConsolePlainText(QPlainTextEdit):
    execute_command = pysideSignal(str)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setFont(QFont("Consolas", 12))
        self.setReadOnly(True)
        self.command_mode = False
        self.command_start_pos = 0
        self.setPlaceholderText(self.tr("Для ввода команды нажмите Enter ..."))

    def add_text(self, text: str) -> None:
        self.setReadOnly(False)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)

        if self.toPlainText():
            self.insertPlainText("\n\n" + text)
        else:
            self.insertPlainText(text)

        self.setReadOnly(True)
        self.ensureCursorVisible()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if not self.command_mode:
                self.setReadOnly(False)
                self.command_mode = True
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.setTextCursor(cursor)
                if self.toPlainText():
                    self.insertPlainText("\n\n> ")
                else:
                    self.insertPlainText("> ")
                self.command_start_pos = self.textCursor().position()
                self.ensureCursorVisible()
            else:
                command = self.get_command_text()
                if command:
                    self.setReadOnly(True)
                    self.command_mode = False
                    self.execute_command.emit(command)

            return None

        if self.command_mode:
            cursor = self.textCursor()

            if event.key() in (
                    Qt.Key.Key_Up,
                    Qt.Key.Key_Down,
                    Qt.Key.Key_Left,
                    Qt.Key.Key_PageUp,
                    Qt.Key.Key_PageDown,
                    Qt.Key.Key_Home
            ):
                return None

            if event.key() == Qt.Key.Key_Backspace:
                if cursor.position() <= self.command_start_pos:
                    return None
            if event.key() == Qt.Key.Key_Delete:
                if cursor.position() < self.command_start_pos:
                    return None

            if cursor.position() < self.command_start_pos:
                cursor.setPosition(self.command_start_pos)
                self.setTextCursor(cursor)

            super().keyPressEvent(event)

    def get_command_text(self):
        text = self.toPlainText()
        return text[self.command_start_pos:].strip()
    
    def clear(self) -> None:
        self.command_mode = False
        self.setReadOnly(True)
        super().clear()


class ConsoleWidget(QWidget):
    """
    Виджет консоли.
    """
    show_message = pysideSignal(str)

    _add_text = pysideSignal(str)
    _get_checkpoint_object = pysideSignal(DriverCode, str, str)

    def __init__(self, service: SportEventService, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._service = service

        self._commands = [
            "clear",
            "<football, hockey, volleyball>/get_match_ids",
            "<football, hockey, volleyball>/get_script_ids",
            "<football, hockey, volleyball>/get_signal_ids",
            "<football, hockey, volleyball>/get_match_details/<match_id>",
            "<football, hockey, volleyball>/get_script/<script_id>",
            "<football, hockey, volleyball>/get_signal/<signal_id>",
        ]

        self._driver_codes = {
            "football": DriverCode.FOOTBALL,
            "hockey": DriverCode.HOCKEY,
            "volleyball": DriverCode.VOLLEYBALL
        }

        bar = QToolBar(self)

        self._text = ConsolePlainText(self)
        self._text.execute_command.connect(self.execute_command)

        clear = QAction(
            icon=QIcon(":/resources/icons/delete.png"),
            toolTip=self.tr("Очистить"),
            parent=self
        )
        clear.triggered.connect(self.clear)

        write = QAction(
            icon=QIcon(":/resources/icons/save.png"),
            toolTip=self.tr("Сохранить в файл"),
            parent=self
        )
        write.triggered.connect(self.write)

        bar.addAction(clear)
        bar.addAction(write)

        layout = QVBoxLayout(self)
        layout.addWidget(bar)
        layout.addWidget(self._text)

        self._add_text.connect(self.add_text)
        self._get_checkpoint_object.connect(self._get_checkpoint_obj)

    def add_text(self, text: str) -> None:
        self._text.add_text(text)

    def clear(self) -> None:
        self._text.clear()

    @Slot()
    def _get_checkpoint_obj(self, driver_code: DriverCode, command: str, arg: str) -> None:
        def _print_text(obj: Any) -> None:
            if isinstance(obj, BetSysModel):
                self._add_text.emit(json.dumps(obj.model_dump(mode='json'), indent=2, ensure_ascii=False))
            elif isinstance(obj, (list, set, dict)):
                self._add_text.emit("\n".join(f"{i}. {item}" for i, item in enumerate(obj, start=1)))
            else:
                self._add_text.emit(self.tr("Объект не найден"))
        if arg:
            self._service.get_object(
                _print_text,
                driver_code,
                CheckPoint.__name__,
                command,
                arg
            )
        else:
            self._service.get_object(
                _print_text,
                driver_code,
                CheckPoint.__name__,
                command
            )

    def write(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent(),
            self.tr("Сохранить файл"),
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            self.tr("Текстовые файлы (*.txt);")
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self._text.toPlainText())

                self.show_message.emit(self.tr("Файл сохранен"))
            except Exception as exception:
                _logger.exception(exception)

                self.show_message.emit(self.tr("Не удалось сохранить файл"))

    def execute_command(self, command: str) -> None:
        commands = iter(command.split("/"))

        command = next(commands, None)
        if command == "help":
            information = "\n".join(f"{i}. {item}" for i, item in enumerate(self._commands, start=1))
            self.add_text(self.tr("Команды:\n{}").format(information))
        elif command == "clear":
            self.clear()
        elif command in ["football", "hockey", "volleyball"]:
            _command = next(commands, None)
            if _command in [
                "get_match_details",
                "get_script",
                "get_signal",
                "get_match_ids",
                "get_script_ids",
                "get_signal_ids"
            ]:
                arg = next(commands, None)
                self._get_checkpoint_object.emit(self._driver_codes.get(command), _command, arg)
            else:
                self.add_text(self.tr("Неизвестная команда: {}. Используйте команду help").format(command))
        else:
            self.add_text(self.tr("Неизвестная команда: {}. Используйте команду help").format(command))
