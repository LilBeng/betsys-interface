from PySide6.QtCore import QFile, QIODevice
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit


class ErrorDialog(QDialog):
    def __init__(self, path: str, *args, **kwargs) -> None:
        super().__init__(*args, *kwargs)
        self.setWindowTitle(self.tr("Ошибки"))
        self.setWindowIcon(QIcon(":/resources/icons/console.png"))
        self.setMinimumSize(600, 300)

        layout = QVBoxLayout(self)

        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)

        file = QFile(path)
        if file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
            text_edit.setPlainText(file.readAll().data().decode('utf-8'))
            file.close()

        layout.addWidget(text_edit)
