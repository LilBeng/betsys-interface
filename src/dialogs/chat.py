from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QLabel, QDialog, QScrollArea, QWidget, QHBoxLayout, \
    QLayout
from betsys import Message, get_role_name, RoleCode

from src.utils.lang import AppLang


class MessageBubble(QFrame):
    def __init__(self, message: Message, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        role_label = QLabel(get_role_name(message.role, AppLang.code))
        role_font = QFont()
        role_font.setPointSize(10)
        role_font.setBold(True)
        role_label.setFont(role_font)
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content_label = QLabel(message.content)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.TextFormat.PlainText)

        timestamp_label = QLabel(message.timestamp.strftime('%d.%m.%Y %H:%M:%S'))
        timestamp_font = QFont()
        timestamp_font.setPointSize(8)
        timestamp_label.setFont(timestamp_font)
        timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(role_label)
        layout.addWidget(content_label)
        layout.addWidget(timestamp_label)


class ChatDialog(QDialog):
    def __init__(self, messages: list[Message], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.messages = messages

        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle(self.tr("Чат"))
        self.setWindowIcon(QIcon(":/resources/icons/dialog.png"))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        messages_container = QWidget(self)
        messages_layout = QVBoxLayout(messages_container)
        messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        messages_layout.setSpacing(10)
        messages_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area.setWidget(messages_container)

        main_layout.addWidget(scroll_area)

        # Добавляем сообщения
        for message in self.messages:
            bubble = MessageBubble(message)

            layout = QHBoxLayout()
            layout.setContentsMargins(20, 0, 20, 0)

            if message.role == RoleCode.USER:
                layout.addStretch()
                layout.addWidget(bubble)
            elif message.role == RoleCode.ASSISTANT:
                layout.addWidget(bubble)
                layout.addStretch()
            else:
                layout.addStretch()
                layout.addWidget(bubble)
                layout.addStretch()

            messages_layout.addLayout(layout)

        messages_layout.addStretch()

        main_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
