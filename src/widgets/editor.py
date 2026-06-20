from typing import Optional

from PySide6.QtCore import Signal, QSize, Slot, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QToolBar,
    QHBoxLayout,
    QPlainTextEdit,
    QComboBox,
    QFormLayout,
    QSpinBox,
    QGroupBox
)
from betsys import (
    ScriptDBModel,
    Script,
    SignalProperty,
    BothToScoreBet,
    FEventStatusCode,
    BetCode,
    OneXTwoBet,
    OverUnderBet,
    DoubleChanceBet,
    OddOrEvenBet,
    AIPromptDBModel,
    MatchCode,
    get_match_name,
    SignalTypeCode,
    get_signal_type_name, get_total_bet_name
)

from src.dialogs.property import PromptDialog
from src.utils.blocker import WheelBlocker
from src.utils.button import create_icon_push_button
from src.utils.lang import AppLang
from src.widgets.box import DataGroupBox, PropertyGroupBox, FilterGroupBox, DescriptionGroupBox


class ScriptEditorWidget(QWidget):
    save_model_signal = Signal(ScriptDBModel)

    def __init__(self, model: Optional[ScriptDBModel], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.model = model

        if self.model.obj:
            self._script = Script.decompress(model.obj)
        else:
            if model.bet_code == BetCode.BOTH_TO_SCORE:
                bet = BothToScoreBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_both_to_score=True
                )
            elif model.bet_code == BetCode.ONE_X_TWO:
                bet = OneXTwoBet(
                    event_status_code=FEventStatusCode.FULL_TIME
                )
            elif model.bet_code == BetCode.OVER_UNDER:
                bet = OverUnderBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_over=True,
                    value=0.5
                )
            elif model.bet_code == BetCode.DOUBLE_CHANCE:
                bet = DoubleChanceBet(
                    event_status_code=FEventStatusCode.FULL_TIME
                )
            else:
                bet = OddOrEvenBet(
                    event_status_code=FEventStatusCode.FULL_TIME,
                    is_even=True
                )
            self._script = Script(
                script_id=self.model.id,
                description=self.model.description,
                match_code=self.model.match_code,
                is_active=self.model.is_active,
                signal_property=SignalProperty(
                    bet=bet
                )
            )

        self._toolbar = QToolBar(iconSize=QSize(35, 35), parent=self)

        self._save_button = QAction(
            QIcon(":/resources/icons/save.png"),
            self.tr("Сохранить изменения"),
            self
        )
        self._save_button.triggered.connect(self.save_model)

        self._toolbar.addAction(self._save_button)

        self._data = DataGroupBox(self._script)
        self._data.setMaximumWidth(450)
        self._property = PropertyGroupBox(self._script)
        self._filter = FilterGroupBox(self._script)
        self._description = DescriptionGroupBox(self._script)
        self._description.setFixedHeight(165)

        box_layout = QHBoxLayout()
        box_layout.addWidget(self._data)
        box_layout.addWidget(self._property)
        box_layout.addWidget(self._filter)
        box_layout.addWidget(self._description)

        layout = QVBoxLayout(self)
        layout.addWidget(self._toolbar, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(box_layout)

    @Slot()
    def save_model(self) -> None:
        self.model.match_code = self._script.match_code
        self.model.description = self._script.description
        self.model.is_active = self._script.is_active
        self.model.signal_type_code = self._script.signal_property.signal_type_code
        self.model.obj = self._script.compress()

        self.save_model_signal.emit(self.model)


class PromptEditorWidget(QWidget):
    save_model_signal = Signal(AIPromptDBModel)

    def __init__(self, model: AIPromptDBModel, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.model = model

        self._toolbar = QToolBar(iconSize=QSize(35, 35), parent=self)

        self._save_button = QAction(
            QIcon(":/resources/icons/save.png"),
            self.tr("Сохранить изменения"),
            self
        )
        self._save_button.triggered.connect(self.save_model)

        self._toolbar.addAction(self._save_button)

        icons = [
            QIcon(":/resources/icons/football.png"),
            QIcon(":/resources/icons/hockey.png"),
            QIcon(":/resources/icons/volleyball.png"),
        ]

        self.wheel_blocker = WheelBlocker()

        self._bet_code = QComboBox(self)
        self._bet_code.installEventFilter(self.wheel_blocker)
        for bet_code in BetCode:
            self._bet_code.addItem(get_total_bet_name(bet_code, AppLang.code), bet_code)

        self._match_code = QComboBox(self)
        self._match_code.installEventFilter(self.wheel_blocker)
        for match_code, icon in zip(MatchCode, icons):
            self._match_code.addItem(icon, get_match_name(match_code, AppLang.code), match_code)

        self._signal_type_codes = QComboBox(self)
        self._signal_type_codes.installEventFilter(self.wheel_blocker)
        for signal_type_code in SignalTypeCode:
            self._signal_type_codes.addItem(get_signal_type_name(signal_type_code, AppLang.code), signal_type_code)

        self._bet_code.setCurrentText(get_total_bet_name(model.bet_code, AppLang.code))
        self._match_code.setCurrentText(get_match_name(model.match_code, AppLang.code))
        self._signal_type_codes.setCurrentText(get_signal_type_name(model.signal_type_code, AppLang.code))

        self._number = QSpinBox(minimum=0, maximum=100, singleStep=1, value=model.number)
        self._number.installEventFilter(self.wheel_blocker)

        self._text = QPlainTextEdit(self)
        self._text.setPlaceholderText(self.tr("Введите промт для ИИ модели ..."))
        self._text.setPlainText(model.text)

        self._config = create_icon_push_button(
            icon=QIcon(":/resources/icons/config.png"),
            tooltip=self.tr("Выбрать параметры матча"),
            parent=self
        )
        self._config.clicked.connect(self.show_dialog)

        param_layout = QFormLayout()
        param_layout.setVerticalSpacing(15)
        param_layout.setHorizontalSpacing(15)
        param_layout.addRow(self.tr("Тип матча:"), self._match_code)
        param_layout.addRow(self.tr("Тип ставки:"), self._bet_code)
        param_layout.addRow(self.tr("Тип сигнала:"), self._signal_type_codes)
        param_layout.addRow(self.tr("Номер:"), self._number)
        param_layout.addRow(self.tr("Параметры матча:"), self._config)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        text_layout.addWidget(self._text)

        param = QGroupBox(self.tr("Параметры"), self)
        param.setLayout(param_layout)

        text = QGroupBox(self.tr("Текст"), self)
        text.setLayout(text_layout)

        central_layout = QHBoxLayout()
        central_layout.addWidget(param)
        central_layout.addWidget(text)

        layout = QVBoxLayout(self)
        layout.addWidget(self._toolbar, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(central_layout)

    def setup_wheel_filter(self, widget: QWidget) -> None:
        """
        Рекурсивно устанавливаем фильтр на все дочерние виджеты
        """
        widget.installEventFilter(self.wheel_blocker)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self.wheel_blocker)

    @Slot()
    def save_model(self) -> None:
        self.model.number = self._number.value()
        self.model.bet_code = self._bet_code.currentData()
        self.model.match_code = self._match_code.currentData()
        self.model.signal_type_code = self._signal_type_codes.currentData()
        self.model.text = self._text.toPlainText()

        self.save_model_signal.emit(self.model)

    @Slot()
    def show_dialog(self) -> None:
        dialog = PromptDialog(self.model, self)
        dialog.exec()
