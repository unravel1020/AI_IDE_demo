"""
查找/替换对话框
支持普通搜索和正则表达式搜索
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextDocument, QTextCursor


class FindDialog(QDialog):
    """查找/替换对话框"""

    # 信号
    find_next = pyqtSignal(str, bool, bool)      # 查找下一个 (文本, 区分大小写, 正则)
    find_prev = pyqtSignal(str, bool, bool)      # 查找上一个
    replace_one = pyqtSignal(str, str, bool, bool)  # 替换当前 (旧文本, 新文本, 区分大小写, 正则)
    replace_all = pyqtSignal(str, str, bool, bool)  # 替换全部

    def __init__(self, parent=None, replace_mode=False):
        super().__init__(parent)
        self.replace_mode = replace_mode
        self.setWindowTitle("替换" if replace_mode else "查找")
        self.resize(400, 200 if replace_mode else 150)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 查找输入
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("查找:"))
        self.find_input = QLineEdit()
        self.find_input.returnPressed.connect(self.on_find_next)
        find_layout.addWidget(self.find_input)
        layout.addLayout(find_layout)

        # 替换输入
        if self.replace_mode:
            replace_layout = QHBoxLayout()
            replace_layout.addWidget(QLabel("替换:"))
            self.replace_input = QLineEdit()
            self.replace_input.returnPressed.connect(self.on_replace_one)
            replace_layout.addWidget(self.replace_input)
            layout.addLayout(replace_layout)

        # 选项
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox("区分大小写")
        self.regex = QCheckBox("正则表达式")
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.regex)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # 按钮
        btn_layout = QHBoxLayout()

        self.btn_find_next = QPushButton("查找下一个")
        self.btn_find_next.clicked.connect(self.on_find_next)
        btn_layout.addWidget(self.btn_find_next)

        self.btn_find_prev = QPushButton("查找上一个")
        self.btn_find_prev.clicked.connect(self.on_find_prev)
        btn_layout.addWidget(self.btn_find_prev)

        if self.replace_mode:
            self.btn_replace = QPushButton("替换")
            self.btn_replace.clicked.connect(self.on_replace_one)
            btn_layout.addWidget(self.btn_replace)

            self.btn_replace_all = QPushButton("全部替换")
            self.btn_replace_all.clicked.connect(self.on_replace_all)
            btn_layout.addWidget(self.btn_replace_all)

        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # 焦点设置到查找输入框
        self.find_input.setFocus()

    def on_find_next(self):
        text = self.find_input.text()
        if text:
            self.find_next.emit(text, self.case_sensitive.isChecked(), self.regex.isChecked())

    def on_find_prev(self):
        text = self.find_input.text()
        if text:
            self.find_prev.emit(text, self.case_sensitive.isChecked(), self.regex.isChecked())

    def on_replace_one(self):
        old = self.find_input.text()
        new = self.replace_input.text() if self.replace_mode else ""
        if old:
            self.replace_one.emit(old, new, self.case_sensitive.isChecked(), self.regex.isChecked())

    def on_replace_all(self):
        old = self.find_input.text()
        new = self.replace_input.text() if self.replace_mode else ""
        if old:
            self.replace_all.emit(old, new, self.case_sensitive.isChecked(), self.regex.isChecked())

    def set_find_text(self, text: str):
        """设置查找文本"""
        self.find_input.setText(text)
        self.find_input.selectAll()


class SearchHighlighter:
    """搜索结果高亮器（非 QSyntaxHighlighter，直接操作 ExtraSelection）"""

    def __init__(self, editor):
        self.editor = editor
        self._search_results = []

    def highlight_all(self, text: str, case_sensitive: bool = False, use_regex: bool = False):
        """高亮所有匹配结果"""
        self.clear()

        if not text:
            return 0

        doc = self.editor.document()
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        selections = []
        cursor = doc.find(text, 0, flags)

        count = 0
        while not cursor.isNull():
            extra = QTextEdit.ExtraSelection()
            extra.cursor = cursor
            extra.format.setBackground(Qt.GlobalColor.yellow)
            extra.format.setForeground(Qt.GlobalColor.black)
            selections.append(extra)
            count += 1

            # 继续查找下一个
            pos = cursor.position()
            cursor = doc.find(text, pos, flags)

        self._search_results = selections
        # 合并现有的 extra selections（保留错误高亮）
        existing = self.editor.extraSelections()
        self.editor.setExtraSelections(existing + selections)
        return count

    def clear(self):
        """清除搜索高亮，但保留错误高亮"""
        # 只保留 error_map 相关的高亮（红色背景）
        existing = self.editor.extraSelections()
        error_selections = [
            s for s in existing
            if s.format.background().color().red() == 255
            and s.format.background().color().green() < 100
        ]
        self.editor.setExtraSelections(error_selections)
        self._search_results = []

    def find_next(self, text: str, case_sensitive: bool = False, use_regex: bool = False) -> bool:
        """查找下一个并选中"""
        if not text:
            return False

        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        cursor = self.editor.textCursor()
        pos = cursor.position()

        found = self.editor.document().find(text, pos, flags)
        if found.isNull():
            # 从头开始查找
            found = self.editor.document().find(text, 0, flags)

        if not found.isNull():
            self.editor.setTextCursor(found)
            return True
        return False

    def find_prev(self, text: str, case_sensitive: bool = False, use_regex: bool = False) -> bool:
        """查找上一个并选中"""
        if not text:
            return False

        flags = QTextDocument.FindFlag.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        cursor = self.editor.textCursor()
        pos = cursor.position()

        found = self.editor.document().find(text, pos, flags)
        if found.isNull():
            # 从末尾开始查找
            last_pos = self.editor.document().characterCount() - 1
            found = self.editor.document().find(text, last_pos, flags)

        if not found.isNull():
            self.editor.setTextCursor(found)
            return True
        return False
