from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
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

        # --- Input Area ---
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #1E1E1E; border-top: 1px solid #2A2A2A;")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(40, 16, 40, 16)
        input_layout.setSpacing(10)

        # Text Field
        # self.input_text = QTextEdit()
        # self.input_text.setMaximumHeight(120)
        # self.input_text.setPlaceholderText(self.tr("Введите ваше сообщение..."))
        # self.input_text.setAcceptRichText(False)
        # self.input_text.setStyleSheet("""
        #     QTextEdit {
        #         background-color: #252525;
        #         border: 1px solid #333333;
        #         border-radius: 12px;
        #         padding: 10px;
        #         color: #F0F0F0;
        #         font-size: 14px;
        #         selection-background-color: #444;
        #     }
        #     QTextEdit:focus {
        #         border: 1px solid #555555;
        #     }
        # """)
        #
        # # Buttons layout
        # btn_layout = QHBoxLayout()
        # btn_layout.addStretch()
        #
        # self.clear_button = QPushButton(self.tr("Очистить"))
        # self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        # self.clear_button.setStyleSheet("""
        #     QPushButton {
        #         background: transparent;
        #         color: #888888;
        #         border: none;
        #         padding: 6px 12px;
        #         font-size: 13px;
        #     }
        #     QPushButton:hover { color: #FFFFFF; }
        # """)
        # self.clear_button.clicked.connect(self.clear_input)
        #
        # self.send_button = QPushButton(self.tr("Отправить"))
        # self.send_button.setDefault(True)
        # self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        # self.send_button.setFixedSize(100, 36)
        # self.send_button.setStyleSheet("""
        #     QPushButton {
        #         background-color: #3B82F6;
        #         color: #FFFFFF;
        #         border: none;
        #         border-radius: 8px;
        #         font-weight: bold;
        #         font-size: 13px;
        #     }
        #     QPushButton:hover { background-color: #2563EB; }
        #     QPushButton:pressed { background-color: #1D4ED8; }
        # """)
        # self.send_button.clicked.connect(self.send_message)
        #
        # btn_layout.addWidget(self.clear_button)
        # btn_layout.addWidget(self.send_button)
        #
        # input_layout.addWidget(self.input_text)
        # input_layout.addLayout(btn_layout)

        # Layout Assembly
        main_layout.addWidget(self.scroll_area, 1)
        main_layout.addWidget(input_container, 0)

        # Load messages
        self.setUpdatesEnabled(False)
        for msg in self.messages:
            self.add_message_bubble(msg)
        self.setUpdatesEnabled(True)

        QTimer.singleShot(0, self.scroll_to_bottom)

        # Shortcuts
        # QShortcut(QKeySequence("Ctrl+Return"), self.input_text).activated.connect(self.send_message)
        # QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)

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

    def send_message(self):
        content = self.input_text.toPlainText().strip()
        if not content:
            return

        msg = Message(role=RoleCode.USER, content=content, timestamp=datetime.now())
        self.messages.append(msg)
        self.add_message_bubble(msg)
        self.clear_input()
        self.message_sent.emit(content)
        self.scroll_to_bottom()

    def add_assistant_message(self, content: str, reasoning_content: Optional[str] = None):
        msg = Message(
            role=RoleCode.ASSISTANT,
            content=content,
            reasoning_content=reasoning_content,
            timestamp=datetime.now()
        )
        self.messages.append(msg)
        self.add_message_bubble(msg)
        self.scroll_to_bottom()

    def clear_input(self):
        self.input_text.clear()
        self.input_text.setFocus()

    def scroll_to_bottom(self):
        QTimer.singleShot(50, self._perform_scroll)

    def _perform_scroll(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())
