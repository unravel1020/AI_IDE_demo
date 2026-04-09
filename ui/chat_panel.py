"""
AI 对话侧边栏
类似 Cursor 的 AI 对话功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLineEdit, QScrollArea, QFrame, QLabel,
    QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.API_Call_SDK_v1 import AIClient


class ChatWorker(QThread):
    """AI 对话工作线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, client, messages):
        super().__init__()
        self.client = client
        self.messages = messages

    def run(self):
        try:
            response = self.client.chat_with_history(self.messages)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class ChatMessage(QFrame):
    """单条聊天消息组件"""

    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # 角色标签
        role_label = QLabel("🧑 你" if self.role == "user" else "🤖 AI")
        role_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 12px;
            color: {'#BB86FC' if self.role == 'user' else '#03DAC6'};
        """)
        layout.addWidget(role_label)

        # 内容
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.content_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                font-size: 13px;
                line-height: 1.6;
            }
        """)

        # 解析内容，高亮代码块
        formatted = self._format_content(self.content)
        self.content_label.setText(formatted)
        layout.addWidget(self.content_label)

        # 代码块操作按钮（如果有代码）
        code_blocks = self._extract_code_blocks(self.content)
        if code_blocks:
            for i, code in enumerate(code_blocks):
                btn_layout = QHBoxLayout()
                btn_insert = QPushButton(f"📥 插入代码块 {i+1}")
                btn_insert.setStyleSheet("""
                    QPushButton {
                        background-color: #03DAC6;
                        color: #000000;
                        border: none;
                        border-radius: 12px;
                        padding: 4px 12px;
                        font-size: 11px;
                    }
                """)
                btn_insert.clicked.connect(lambda checked, c=code: self.on_insert_code(c))
                btn_layout.addWidget(btn_insert)
                btn_layout.addStretch()
                layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 根据角色设置背景色
        if self.role == "user":
            self.setStyleSheet("""
                QFrame {
                    background-color: #2D2D2D;
                    border-radius: 12px;
                    margin: 4px 20px 4px 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1E3A3A;
                    border-radius: 12px;
                    margin: 4px 4px 4px 20px;
                    border-left: 3px solid #03DAC6;
                }
            """)

    def _format_content(self, text: str) -> str:
        """格式化内容，处理代码块"""
        # 简单处理：将 ``` 代码块标记为 [代码]
        text = re.sub(r'```(\w+)?\n', '\n[代码]\n', text)
        text = text.replace('```', '\n[/代码]\n')
        # 将换行符转换为 HTML 换行
        text = text.replace('\n', '<br>')
        return text

    def _extract_code_blocks(self, text: str) -> list:
        """提取代码块"""
        pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        return matches

    def on_insert_code(self, code: str):
        """插入代码到编辑器"""
        main_window = self.window()
        if hasattr(main_window, 'code_input'):
            cursor = main_window.code_input.textCursor()
            cursor.insertText(code + "\n")


class ChatPanel(QWidget):
    """AI 对话侧边栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ai = AIClient()
        self.messages = [
            {"role": "system", "content": "你是一个专业的 C++ 编程助手。你可以帮助用户解释代码、重构代码、生成代码、回答编程问题。请使用中文回答。"}
        ]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 标题
        title = QLabel("💬 AI 助手")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #BB86FC;")
        layout.addWidget(title)

        # 快捷指令
        shortcuts_layout = QHBoxLayout()
        shortcuts = [
            ("📖 解释", "explain"),
            ("🔧 重构", "refactor"),
            ("🧪 测试", "test"),
            ("💡 优化", "optimize"),
        ]
        for label, action in shortcuts:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4A4458;
                    color: #BB86FC;
                    border: none;
                    border-radius: 12px;
                    padding: 4px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #BB86FC;
                    color: #000000;
                }
            """)
            btn.clicked.connect(lambda checked, a=action: self.on_shortcut(a))
            shortcuts_layout.addWidget(btn)
        layout.addLayout(shortcuts_layout)

        # 聊天记录区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(8)
        self.chat_container.setLayout(self.chat_layout)

        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)

        # 输入区
        input_layout = QHBoxLayout()

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("输入消息... 使用 @ 引用当前文件")
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #494949;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #BB86FC;
            }
        """)
        input_layout.addWidget(self.input_box)

        self.btn_send = QPushButton("📤")
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #BB86FC;
                color: #000000;
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
            }
        """)
        self.btn_send.clicked.connect(self.send_message)
        input_layout.addWidget(self.btn_send)

        layout.addLayout(input_layout)

        # 按钮栏
        btn_layout = QHBoxLayout()

        self.btn_clear = QPushButton("🧹 清空")
        self.btn_clear.clicked.connect(self.clear_chat)
        btn_layout.addWidget(self.btn_clear)

        self.btn_context = QPushButton("📄 附带代码")
        self.btn_context.setCheckable(True)
        self.btn_context.setChecked(True)
        self.btn_context.setStyleSheet("""
            QPushButton:checked {
                background-color: #03DAC6;
                color: #000000;
            }
        """)
        btn_layout.addWidget(self.btn_context)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 欢迎消息
        self.add_message("assistant", "你好！我是你的 C++ 编程助手。\n\n我可以帮你：\n- 📖 解释代码逻辑\n- 🔧 重构和优化代码\n- 🧪 生成单元测试\n- 💡 回答编程问题\n\n点击上方快捷指令或直接在下方输入消息。")

    def add_message(self, role: str, content: str):
        """添加消息到聊天区"""
        msg_widget = ChatMessage(role, content)
        self.chat_layout.addWidget(msg_widget)

        # 滚动到底部
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_editor_code(self) -> str:
        """获取编辑器代码"""
        main_window = self.window()
        if hasattr(main_window, 'code_input'):
            return main_window.code_input.toPlainText()
        return ""

    def send_message(self):
        """发送消息"""
        text = self.input_box.text().strip()
        if not text:
            return

        self.input_box.clear()

        # 处理 @ 引用
        include_code = self.btn_context.isChecked()
        code = self.get_editor_code()

        if "@" in text and code:
            text = text.replace("@", "") + f"\n\n当前代码：\n```cpp\n{code}\n```"
        elif include_code and code:
            text = text + f"\n\n当前代码：\n```cpp\n{code}\n```"

        # 显示用户消息
        self.add_message("user", text)

        # 添加到历史
        self.messages.append({"role": "user", "content": text})

        # 显示思考中
        self.thinking_label = QLabel("🤔 AI 思考中...")
        self.thinking_label.setStyleSheet("color: #A0A0A0; padding: 10px;")
        self.chat_layout.addWidget(self.thinking_label)

        # 禁用输入
        self.input_box.setEnabled(False)
        self.btn_send.setEnabled(False)

        # 启动 AI 请求
        self.worker = ChatWorker(self.ai, self.messages)
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_response(self, response: str):
        """收到 AI 响应"""
        # 移除思考标签
        if hasattr(self, 'thinking_label'):
            self.thinking_label.deleteLater()

        # 显示 AI 消息
        self.add_message("assistant", response)

        # 添加到历史
        self.messages.append({"role": "assistant", "content": response})

        # 限制历史长度
        if len(self.messages) > 20:
            self.messages = [self.messages[0]] + self.messages[-19:]

        # 启用输入
        self.input_box.setEnabled(True)
        self.btn_send.setEnabled(True)
        self.input_box.setFocus()

    def on_error(self, error_msg: str):
        """错误处理"""
        if hasattr(self, 'thinking_label'):
            self.thinking_label.deleteLater()

        self.add_message("assistant", f"❌ 出错了：{error_msg}")

        self.input_box.setEnabled(True)
        self.btn_send.setEnabled(True)

    def on_shortcut(self, action: str):
        """快捷指令"""
        code = self.get_editor_code()
        if not code.strip():
            self.add_message("assistant", "❌ 请先打开或输入代码")
            return

        prompts = {
            "explain": f"请详细解释以下 C++ 代码的功能和逻辑：\n\n```cpp\n{code}\n```",
            "refactor": f"请重构以下 C++ 代码，使其更清晰、更易维护，保持原有功能不变：\n\n```cpp\n{code}\n```",
            "test": f"请为以下 C++ 代码生成单元测试（使用 Google Test 风格）：\n\n```cpp\n{code}\n```",
            "optimize": f"请优化以下 C++ 代码的性能，解释优化原因：\n\n```cpp\n{code}\n```",
        }

        self.input_box.setText(prompts.get(action, ""))
        self.send_message()

    def clear_chat(self):
        """清空聊天记录"""
        while self.chat_layout.count():
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.messages = [self.messages[0]]  # 保留 system 消息
        self.add_message("assistant", "聊天记录已清空。有什么可以帮你的吗？")
