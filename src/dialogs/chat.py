from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QVBoxLayout,
    QLabel,
    QDialog,
    QScrollArea,
    QWidget,
    QHBoxLayout
)
from betsys import Message, get_role_name, RoleCode

from src.utils.lang import AppLang


class MessageBubble(QFrame):
    def __init__(self, message: Message, parent, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
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


class ChatDialog(QDialog):
    message_sent = Signal(str)

    def __init__(self, messages: list[Message], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.messages = messages

        self.setWindowTitle(self.tr("Чат"))
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
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(40, 16, 40, 16)
        input_layout.setSpacing(10)

        main_layout.addWidget(self.scroll_area, 1)
        main_layout.addWidget(input_container, 0)

        # Load messages
        self.setUpdatesEnabled(False)
        for msg in self.messages:
            self.add_message_bubble(msg)
        self.setUpdatesEnabled(True)

    def add_message_bubble(self, message: Message):
        bubble = MessageBubble(message, self)
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
