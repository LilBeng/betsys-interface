import uuid
from typing import Optional, Any

from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtGui import QIcon, QRegularExpressionValidator, QPalette, QColor
from PySide6.QtWidgets import QGroupBox, QLineEdit, QHBoxLayout, QFormLayout
from betsys.expr.base import BaseVar

from src.utils.button import create_icon_push_button
from src.utils.highlighter import TextKeywords


class BaseVariableWidget(QGroupBox):
    def __init__(self, title: str, variable: Optional[Any] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._variable = variable
        self._id = uuid.uuid4()

        self.setTitle(title)

        self._delete_button = create_icon_push_button(
            icon=QIcon(":/resources/icons/minus.png"),
            tooltip=self.tr("Удалить"),
            size=QSize(32, 32),
            parent=self
        )

        self._delete_button.clicked.connect(self.deleteLater)

        self._name = QLineEdit(self)
        self._name.setPlaceholderText(self.tr("Символы a-z, A-Z, 0-9 и _"))

        palette = self._name.palette()
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, QColor(95, 175, 255))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, QColor(95, 175, 255))
        self._name.setPalette(palette)

        validator = QRegularExpressionValidator("[a-zA-Z0-9_]{50}")
        self._name.setValidator(validator)

        if variable:
            self._name.setText(variable.name)

        self._setting = create_icon_push_button(
            icon=QIcon(":/resources/icons/config.png"),
            tooltip=self.tr("Настройка параметров"),
            parent=self
        )

        self._setting.clicked.connect(self.show_setting_dialog)

        title = QHBoxLayout()
        title.addWidget(self._name)
        title.addWidget(self._setting, alignment=Qt.AlignmentFlag.AlignRight)
        title.addWidget(self._delete_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.layout = QFormLayout(self)
        self.layout.setSpacing(10)
        self.layout.addRow(self.tr("Наименование:"), title)

        self._name.textChanged.connect(self.edit_name)

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def variable(self) -> Optional[BaseVar]:
        if self._variable:
            self._variable.name = self.name
        return self._variable

    @property
    def name(self) -> str:
        return self._name.text()

    @Slot()
    def edit_name(self) -> None:
        keywords = TextKeywords()
        if self.name:
            keywords.add_word(self._id, self.name)

    @Slot()
    def show_setting_dialog(self) -> None:
        ...

    @Slot()
    def deleteLater(self) -> None:
        keywords = TextKeywords()
        if self.name:
            keywords.remove_word(self._id)

        super().deleteLater()
