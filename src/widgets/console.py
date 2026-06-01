import logging

from PySide6.QtCore import Qt, Signal as pysideSignal, QStandardPaths
from PySide6.QtGui import QAction, QIcon, QFont
from PySide6.QtGui import QTextCursor, QKeyEvent
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget, QFileDialog
from PySide6.QtWidgets import QToolBar

_logger = logging.getLogger(__name__)


class ConsolePlainText(QPlainTextEdit):
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
                # Вход в режим ввода команды
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
                # Выполнение команды
                command = self.get_command_text()
                if command:
                    self.setReadOnly(True)
                    self.command_mode = False
                    self.execute_command(command)
            return

        if self.command_mode:
            if event.key() == Qt.Key.Key_Backspace:
                cursor = self.textCursor()
                if cursor.position() <= self.command_start_pos:
                    return
            super().keyPressEvent(event)

    def get_command_text(self):
        text = self.toPlainText()
        return text[self.command_start_pos:].strip()

    def execute_command(self, command: str) -> None:
        if command == "clear":
            self.clear()
            return
        else:
            self.add_text(self.tr("Неизвестная команда: {}").format(command))
    
    def clear(self) -> None:
        self.command_mode = False
        self.setReadOnly(True)
        super().clear()


class ConsoleWidget(QWidget):
    """
    Виджет консоли.
    """
    show_message = pysideSignal(str)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        bar = QToolBar(self)

        self._text = ConsolePlainText(self)

        clear = QAction(
            icon=QIcon(":/resources/icons/delete.png"),
            toolTip=self.tr("Очистить"),
            parent=self
        )
        clear.triggered.connect(self._text.clear)

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

    def add_text(self, text: str) -> None:
        self._text.add_text(text)

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
