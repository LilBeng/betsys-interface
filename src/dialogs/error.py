from typing import Optional

from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QWidget


class ErrorDialog(QDialog):
    def __init__(self, path: str, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, *kwargs)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle(self.tr("Ошибки"))
        self.setWindowIcon(QIcon(":/resources/icons/console.png"))
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)

        file = QFile(path)
        if file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
            text_edit.setPlainText(file.readAll().data().decode('utf-8'))
            file.close()

        layout.addWidget(text_edit)
