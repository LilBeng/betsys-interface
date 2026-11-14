from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QPoint, Signal as pysideSignal, Slot
from PySide6.QtGui import QFont, QIcon, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QVBoxLayout,
    QLabel,
    QDialog,
    QScrollArea,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QMenu
)
from betsys import Message, get_role_name, RoleCode, SportEventDriver, Signal, DriverCode, MessageObjectCode, \
    MatchDetails

from src.utils.lang import AppLang
from src.utils.service import BetSysService


class MessageBubble(QFrame):
    delete = pysideSignal(QWidget, Message)

    def __init__(self, message: Message, parent, *args, **kwargs) -> None:

        super().__init__(parent=parent, *args, **kwargs)
        self.message = message

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        role_label = QLabel(get_role_name(message.role, AppLang.code))
        role_font = QFont()
        role_font.setPointSize(10)
        role_font.setBold(True)
        role_label.setFont(role_font)
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content_label = QLabel(message.content)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.TextFormat.PlainText)

        timestamp_label = QLabel(message.timestamp.strftime('%d.%m.%Y %H:%M:%S'))
        timestamp_font = QFont()
        timestamp_font.setPointSize(8)
        timestamp_label.setFont(timestamp_font)
        timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(role_label)

        if message.reasoning_content:
            reasoning_content_label = QLabel(self.tr("Рассуждение:\n{}\n").format(message.reasoning_content))
            reasoning_content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            reasoning_content_label.setWordWrap(True)
            reasoning_content_font = QFont()
            reasoning_content_font.setItalic(True)
            reasoning_content_label.setFont(reasoning_content_font)
            reasoning_content_label.setTextFormat(Qt.TextFormat.PlainText)
            layout.addWidget(reasoning_content_label)

        layout.addWidget(content_label)
        layout.addWidget(timestamp_label)

    def show_context_menu(self, position: QPoint) -> None:
        context_menu = QMenu(self)

        delete_action = context_menu.addAction(QIcon(":/resources/icons/delete.png"), self.tr("Удалить"))
        delete_action.triggered.connect(self.delete_message)

        context_menu.exec_(self.mapToGlobal(position))

    @Slot()
    def delete_message(self) -> None:
        self.delete.emit(self, self.message)


class MessageViewer(QDialog):
    def __init__(self, driver_code: DriverCode, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._driver_code = driver_code

        self.setWindowTitle(self.tr("Сообщения"))
        self.setWindowIcon(QIcon(":/resources/icons/dialog.png"))
        self.resize(900, 700)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(40, 30, 40, 30)

        self.scroll_area.setWidget(self.messages_container)

        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(40, 16, 40, 16)
        input_layout.setSpacing(10)

        self.input_text = QTextEdit(parent=self)
        self.input_text.setMaximumHeight(120)
        self.input_text.setPlaceholderText(self.tr("Введите ваше сообщение..."))
        self.input_text.setAcceptRichText(False)
        self.input_text.setStyleSheet("""
                    QTextEdit {
                        background-color: #252525;
                        border: 1px solid #333333;
                        border-radius: 12px;
                        padding: 10px;
                        color: #F0F0F0;
                        font-size: 14px;
                        selection-background-color: #444;
                    }
                    QTextEdit:focus {
                        border: 1px solid #555555;
                    }
                """)

        self.add_button = QPushButton(self.tr("Добавить"))
        self.add_button.setDefault(True)
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setFixedSize(100, 36)
        self.add_button.setStyleSheet("""
                    QPushButton {
                        background-color: #3B82F6;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 13px;
                    }
                    QPushButton:hover { background-color: #2563EB; }
                    QPushButton:pressed { background-color: #1D4ED8; }
                """)
        self.add_button.clicked.connect(self.add_message)

        self.clear_button = QPushButton(self.tr("Очистить"))
        self.clear_button.setDefault(True)
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.setFixedSize(100, 36)
        self.clear_button.setStyleSheet("""
                    QPushButton {
                        background-color: #F87171;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 13px;
                    }
                    QPushButton:hover { background-color: #EF4444; }
                    QPushButton:pressed { background-color: #DC2626; }
                """)
        self.clear_button.clicked.connect(self.clear_messages)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.clear_button)

        input_layout.addWidget(self.input_text)
        input_layout.addLayout(button_layout)

        main_layout.addWidget(self.scroll_area, 1)
        main_layout.addWidget(input_container, 0)

        QTimer.singleShot(0, self.scroll_to_bottom)

        QShortcut(QKeySequence("Ctrl+Return"), self.input_text).activated.connect(self.add_message)

    def scroll_to_bottom(self):
        QTimer.singleShot(50, self._perform_scroll)

    def _perform_scroll(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def add_message_bubble(self, message: Message) -> None:
        bubble = MessageBubble(message, self)
        bubble.delete.connect(self.remove_widget)
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if message.role == RoleCode.USER:
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            layout.addWidget(bubble)
            layout.addStretch()

        self.messages_layout.addWidget(container)

    def add_message(self) -> None:
        ...

    def clear_messages(self) -> None:
        ...

    def remove_widget(self, widget: QWidget, message: Message) -> None:
        ...


class SignalMessageViewer(MessageViewer):
    def __init__(self, signal: Signal, driver_code: DriverCode, parent: Optional[QWidget] = None):
        super().__init__(driver_code, parent)
        self._signal = signal

        self.setUpdatesEnabled(False)
        for msg in signal.messages:
            self.add_message_bubble(msg)
        self.setUpdatesEnabled(True)

    def add_message(self) -> None:
        content = self.input_text.toPlainText().strip()
        if not content:
            return

        msg = Message(role=RoleCode.USER, content=content, timestamp=datetime.now())
        self._signal.messages.append(msg)
        self.add_message_bubble(msg)
        self.input_text.clear()

        self.scroll_to_bottom()

        BetSysService.service.get_object(
            None,
            self._driver_code,
            SportEventDriver.__name__,
            SportEventDriver.add_message.__name__,
            MessageObjectCode.SIGNAL,
            self._signal.signal_id,
            msg
        )

    def clear_messages(self) -> None:
        self._signal.messages.clear()

        BetSysService.service.get_object(
            None,
            self._driver_code,
            SportEventDriver.__name__,
            SportEventDriver.clear_messages.__name__,
            MessageObjectCode.SIGNAL,
            self._signal.signal_id,
        )

        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

            del item

    def remove_widget(self, widget: QWidget, message: Message) -> None:
        if message in self._signal.messages:
            widget.hide()
            self.messages_layout.removeWidget(widget)
            widget.deleteLater()

            self._signal.messages.remove(message)

            BetSysService.service.get_object(
                None,
                self._driver_code,
                SportEventDriver.__name__,
                SportEventDriver.remove_message.__name__,
                MessageObjectCode.SIGNAL,
                self._signal.signal_id,
                message
            )


class MatchMessageViewer(MessageViewer):
    def __init__(self, details: MatchDetails, driver_code: DriverCode, parent: Optional[QWidget] = None):
        super().__init__(driver_code, parent)
        self._details = details

        self.setUpdatesEnabled(False)
        for msg in details.messages:
            self.add_message_bubble(msg)
        self.setUpdatesEnabled(True)

    def add_message(self) -> None:
        content = self.input_text.toPlainText().strip()
        if not content:
            return

        msg = Message(role=RoleCode.USER, content=content, timestamp=datetime.now())
        self._details.messages.append(msg)
        self.add_message_bubble(msg)
        self.input_text.clear()

        self.scroll_to_bottom()

        BetSysService.service.get_object(
            None,
            self._driver_code,
            SportEventDriver.__name__,
            SportEventDriver.add_message.__name__,
            MessageObjectCode.MATCH,
            self._details.match.match_id,
            msg
        )

    def clear_messages(self) -> None:
        self._details.messages.clear()

        BetSysService.service.get_object(
            None,
            self._driver_code,
            SportEventDriver.__name__,
            SportEventDriver.clear_messages.__name__,
            MessageObjectCode.MATCH,
            self._details.match.match_id,
        )

        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

            del item

    def remove_widget(self, widget: QWidget, message: Message) -> None:
        if message in self._details.messages:
            widget.hide()
            self.messages_layout.removeWidget(widget)
            widget.deleteLater()

            self._details.messages.remove(message)

            BetSysService.service.get_object(
                None,
                self._driver_code,
                SportEventDriver.__name__,
                SportEventDriver.remove_message.__name__,
                MessageObjectCode.MATCH,
                self._details.match.match_id,
                message
            )
