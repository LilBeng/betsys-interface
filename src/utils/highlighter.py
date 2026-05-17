import re
from uuid import UUID

from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QSyntaxHighlighter, QColor, QTextCharFormat, Qt, QKeyEvent, QRegularExpressionValidator
from PySide6.QtWidgets import QTextEdit

from src.utils.decorators import singleton


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self._patterns = []

        self._symbols = ["+", "-", "*", "/", "**", ">", ">=", "<", "<=", "==", "!=", "(", ")"]
        self._names = ["and", "or", "not", "is", "None", "False", "True"]

    def set_keywords(self, keywords: list[str], color: QColor = QColor(95, 175, 255), case_sensitive: bool = False):
        self._patterns.clear()
        flags = 0 if case_sensitive else re.IGNORECASE

        for word in keywords:
            if not word:
                continue

            pattern = re.compile(r"\b" + re.escape(word) + r"\b", flags)
            self._patterns.append((pattern, QColor(color)))

        for word in self._symbols:
            pattern = re.compile(re.escape(word))
            self._patterns.append((pattern, QColor(255, 145, 50)))

        for word in self._names:
            pattern = re.compile(r"\b" + re.escape(word) + r"\b")
            self._patterns.append((pattern, QColor(255, 145, 50)))

        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        if not self._patterns:
            return

        for pattern, color in self._patterns:
            for iterator in pattern.finditer(text):
                start = iterator.start()
                length = iterator.end() - iterator.start()
                fmt = QTextCharFormat()
                fmt.setForeground(color)
                self.setFormat(start, length, fmt)


@singleton
class TextKeywords(object):
    def __init__(self) -> None:
        self._words = {}
        self._highlighters = []

    @property
    def words(self) -> dict[UUID, str]:
        return self._words

    @property
    def highlighters(self) -> list[Highlighter]:
        return self._highlighters

    def add_highlighter(self, highlighter: Highlighter) -> None:
        self._highlighters.append(highlighter)

        self.update_highlighters()

    def remove_highlighter(self, highlighter: Highlighter) -> None:
        if highlighter in self._highlighters:
            self._highlighters.remove(highlighter)

        self.update_highlighters()

    def add_word(self, idx: UUID, keyword: str) -> None:
        self._words[idx] = keyword

        self.update_highlighters()

    def remove_word(self, idx: UUID) -> None:
        del self._words[idx]

        self.update_highlighters()

    def update_highlighters(self) -> None:
        for highlighter in self._highlighters:
            highlighter.set_keywords(list(self.words.values()))

    def clear(self) -> None:
        self._words.clear()
        self.highlighters.clear()


class OneLineTextEdit(QTextEdit):
    returnPressed = Signal()

    def __init__(self, validator: QRegularExpressionValidator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = validator

        keywords = TextKeywords()

        self.highlighter = Highlighter(self.document())
        self.highlighter.set_keywords(list(keywords.words.values()))

        keywords.add_highlighter(self.highlighter)

        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Сделать высоту по шрифту
        self.setFixedHeight(self.fontMetrics().height() + 15)

        self.setTabChangesFocus(True)
        self.setAcceptRichText(False)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Игнорируем события только модификаторов
        if event.key() in (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            event.accept()
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.returnPressed.emit()
            event.accept()
            return

        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            super().keyPressEvent(event)
            return

        # Обработка Ctrl+V
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_V:
            super().keyPressEvent(event)
            return

        char = event.text()
        if char:
            cursor = self.textCursor()
            pos = cursor.position()
            new_text = self.toPlainText()[:pos] + char + self.toPlainText()[pos:]
            state, _, _ = self.validator.validate(new_text, 0)
            if state == self.validator.State.Invalid:
                event.accept()
                return

        super().keyPressEvent(event)

    def text(self) -> str:
        return self.toPlainText()

    def set_keywords(self, words: list[str]) -> None:
        self.highlighter.set_keywords(words)
