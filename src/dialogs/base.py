from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QFormLayout, QLayout, QWidget, QDialogButtonBox
from betsys import Script, VARIABLE_TYPE, get_variable_name

from src.utils.blocker import WheelBlocker
from src.utils.lang import AppLang


class BaseDialog(QDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        self.wheel_blocker = WheelBlocker()
        self.installEventFilter(self.wheel_blocker)

    def setup_wheel_filter(self, widget: QWidget) -> None:
        """
        Рекурсивно устанавливаем фильтр на все дочерние виджеты
        """
        widget.installEventFilter(self.wheel_blocker)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self.wheel_blocker)


class BaseButtonDialog(BaseDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QIcon(":/resources/icons/config.png"))

        self.central_layout = QFormLayout()

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        self.main_layout = QFormLayout(self)
        self.main_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.main_layout.setSpacing(10)
        self.main_layout.addRow(self.central_layout)
        self.main_layout.addRow(self._buttons)


class BaseScriptDialog(BaseButtonDialog):
    def __init__(self, script: Script, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._script = script


class BaseVarDialog(BaseButtonDialog):
    def __init__(self, variable: VARIABLE_TYPE,  *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._variable = variable

        self.setFixedWidth(425)
        self.setWindowTitle(get_variable_name(variable.var_code, AppLang.code))
