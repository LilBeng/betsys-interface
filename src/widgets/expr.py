from typing import Optional

from PySide6.QtCore import QSize, Slot, Qt
from PySide6.QtGui import QRegularExpressionValidator, QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QMessageBox
from betsys import Expression

from src.utils.button import create_icon_push_button
from src.utils.highlighter import OneLineTextEdit, TextKeywords
from src.widgets.switch import Switch


class ExpressionWidget(QWidget):
    def __init__(self, expression: Optional[Expression] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._expression = expression

        if self._expression:
            checked = self._expression.is_active
        else:
            checked = True

        self._is_active = Switch(size=QSize(50, 25), checked=checked, parent=self)

        self._edit = OneLineTextEdit(
            validator=QRegularExpressionValidator("[a-zA-Z0-9_!\\-+*<>=/(). ]{5000}"),
            parent=self
        )
        self._edit.setPlaceholderText(self.tr("Введите выражение ..."))

        if self._expression:
            self._edit.setText(self._expression.expression)

        self._delete_button = create_icon_push_button(
            icon=QIcon(":/resources/icons/minus.png"),
            tooltip=self.tr("Удалить"),
            size=QSize(32, 32),
            parent=self
        )
        self._delete_button.clicked.connect(self.deleteLater)

        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.addWidget(self._edit)
        layout.addWidget(self._is_active, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._delete_button, alignment=Qt.AlignmentFlag.AlignRight)

    @Slot()
    def deleteLater(self) -> None:
        keywords = TextKeywords()
        keywords.remove_highlighter(self._edit.highlighter)

        super().deleteLater()

    @property
    def expression(self) -> Expression:
        if self._expression:
            self._expression.expression = self._edit.text()
            self._expression.is_active = self._is_active.is_checked()
        else:
            self._expression = Expression(
                expression=self._edit.text(),
                is_active=self._is_active.is_checked()
            )

        return self._expression


class ExpressionStackWidget(QWidget):
    def __init__(self, expressions: list[Expression], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.setSpacing(5)

        for expression in expressions:
            self.add_expression(expression)

    @Slot()
    def add_expression(self, expression: Optional[Expression] = None) -> None:
        self._layout.insertWidget(0, ExpressionWidget(expression, parent=self), alignment=Qt.AlignmentFlag.AlignTop)

    @Slot()
    def clear_expressions(self) -> None:
        widgets = []
        for index in range(self._layout.count()):
            if item := self._layout.itemAt(index):
                if widget := item.widget():
                    widgets.append(widget)

        for widget in widgets:
            widget.deleteLater()
            self._layout.removeWidget(widget)

        self._layout.update()
        self._layout.invalidate()
        self._layout.activate()

    @Slot()
    def show_info(self) -> None:
        text = (
            "<html>"
            "<head>"
            "<style>"
            "body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt; "
            "background-color: #1e1e1e; color: #e6e6e6; margin: 12px; white-space: nowrap; }"
            "table.main { border-collapse: collapse; width: 100%; }"
            "td.main-cell { vertical-align: top; padding: 6px; }"
            "table.inner { border-collapse: collapse; width: 100%; table-layout: fixed; }"
            "th, td { border: 0px solid #2f2f2f; padding: 4px 8px; }"
            "th { background-color: #252525; color: #4EC9B0; text-align: left; font-weight: 600; }"
            "td.op { font-family: 'Consolas', monospace; color: #FEA658; width: 70px; }"
            "td.desc { color: #c8c8c8; padding-left: 12px; }"
            "</style>"
            "</head>"
            "<body>"

            # Основная таблица 2 ряда × 3 колонки
            "<table class='main'>"

            # ────────────── Первый ряд ──────────────
            "<tr>"
            "<td class='main-cell'>"
            "<table class='inner'>"
            "<tr><th colspan='2'>Арифметические</th></tr>"
            "<tr><td class='op'>+</td><td class='desc'>сложение</td></tr>"
            "<tr><td class='op'>-</td><td class='desc'>вычитание</td></tr>"
            "<tr><td class='op'>*</td><td class='desc'>умножение</td></tr>"
            "<tr><td class='op'>/</td><td class='desc'>деление</td></tr>"
            "<tr><td class='op'>//</td><td class='desc'>целочисленное деление</td></tr>"
            "<tr><td class='op'>%</td><td class='desc'>остаток от деления</td></tr>"
            "<tr><td class='op'>**</td><td class='desc'>возведение в степень</td></tr>"
            "</table>"
            "</td>"

            "<td class='main-cell'>"
            "<table class='inner'>"
            "<tr><th colspan='2'>Сравнение</th></tr>"
            "<tr><td class='op'>&gt;</td><td class='desc'>больше</td></tr>"
            "<tr><td class='op'>&gt;=</td><td class='desc'>больше или равно</td></tr>"
            "<tr><td class='op'>&lt;</td><td class='desc'>меньше</td></tr>"
            "<tr><td class='op'>&lt;=</td><td class='desc'>меньше или равно</td></tr>"
            "<tr><td class='op'>==</td><td class='desc'>равно</td></tr>"
            "<tr><td class='op'>!=</td><td class='desc'>не равно</td></tr>"
            "</table>"
            "</td>"

            "<td class='main-cell'>"
            "<table class='inner'>"
            "<tr><th colspan='2'>Логические</th></tr>"
            "<tr><td class='op'>and</td><td class='desc'>логическое И</td></tr>"
            "<tr><td class='op'>or</td><td class='desc'>логическое ИЛИ</td></tr>"
            "<tr><td class='op'>not</td><td class='desc'>логическое НЕ</td></tr>"
            "</table>"
            "</td>"
            "</tr>"

            # ────────────── Второй ряд ──────────────
            "<tr>"
            "<td class='main-cell'>"
            "<table class='inner'>"
            "<tr><th colspan='2'>Идентичность</th></tr>"
            "<tr><td class='op'>is</td><td class='desc'>один объект</td></tr>"
            "<tr><td class='op'>is not</td><td class='desc'>разные объекты</td></tr>"
            "</table>"
            "</td>"

            "<td class='main-cell'>"
            "<table class='inner'>"
            "<tr><th colspan='2'>Прочее</th></tr>"
            "<tr><td class='op'>None</td><td class='desc'>отсутствие значения</td></tr>"
            "<tr><td class='op'>True</td><td class='desc'>истина</td></tr>"
            "<tr><td class='op'>False</td><td class='desc'>ложь</td></tr>"
            "<tr><td class='op'>( )</td><td class='desc'>группировка выражений</td></tr>"
            "</table>"
            "</td>"

            "<td class='main-cell'></td>"  # пустая ячейка для выравнивания
            "</tr>"

            "</table>"
            "</body></html>"
        )

        QMessageBox.information(
            self,
            self.tr("Доступные операторы"),
            text,
            QMessageBox.StandardButton.Ok
        )

    @property
    def expressions(self) -> list[Expression]:
        values = []
        for index in range(self._layout.count()):
            if item := self._layout.itemAt(index):
                values.append(item.widget().expression) # noqa
        return values
