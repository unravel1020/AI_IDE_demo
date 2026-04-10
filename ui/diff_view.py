from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
import difflib


class DiffSideEdit(QPlainTextEdit):
    """差异对比单侧编辑器（只读）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        # 样式由全局 QSS 主题控制
        # 关闭自动换行，保持行对齐
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)


class DiffView(QWidget):
    """
    代码差异对比视图
    左侧：原始代码（删除行为红色）
    右侧：修复代码（新增行为绿色）
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.highlighter_left = None
        self.highlighter_right = None

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：原始代码
        self.left_edit = DiffSideEdit()
        self.left_edit.setPlaceholderText("原始代码")

        # 右侧：修复代码
        self.right_edit = DiffSideEdit()
        self.right_edit.setPlaceholderText("修复后的代码")

        splitter.addWidget(self.left_edit)
        splitter.addWidget(self.right_edit)
        splitter.setSizes([650, 650])

        layout.addWidget(splitter)
        self.setLayout(layout)

        # 滚动同步
        self.left_edit.verticalScrollBar().valueChanged.connect(
            self.sync_scroll_left)
        self.right_edit.verticalScrollBar().valueChanged.connect(
            self.sync_scroll_right)

    def sync_scroll_left(self, value):
        self.right_edit.verticalScrollBar().setValue(value)

    def sync_scroll_right(self, value):
        self.left_edit.verticalScrollBar().setValue(value)

    def set_highlighter(self, highlighter_class, side="both"):
        """为指定侧设置语法高亮器"""
        if side in ("left", "both"):
            if self.highlighter_left:
                self.highlighter_left.setDocument(None)
            self.highlighter_left = highlighter_class(self.left_edit.document())
        if side in ("right", "both"):
            if self.highlighter_right:
                self.highlighter_right.setDocument(None)
            self.highlighter_right = highlighter_class(self.right_edit.document())

    def remove_highlighter(self, side="both"):
        """移除语法高亮器"""
        if side in ("left", "both") and self.highlighter_left:
            self.highlighter_left.setDocument(None)
            self.highlighter_left = None
        if side in ("right", "both") and self.highlighter_right:
            self.highlighter_right.setDocument(None)
            self.highlighter_right = None

    def clear(self):
        """清空对比内容"""
        self.left_edit.clear()
        self.right_edit.clear()

    def set_diff(self, original_code: str, fixed_code: str):
        """
        设置要对比的两段代码，使用颜色标注差异
        """
        self.clear()

        orig_lines = original_code.splitlines(keepends=True)
        fixed_lines = fixed_code.splitlines(keepends=True)

        # 规范化：确保每行以换行结尾
        orig_lines = [line if line.endswith('\n') else line + '\n' for line in orig_lines]
        fixed_lines = [line if line.endswith('\n') else line + '\n' for line in fixed_lines]

        # 使用 SequenceMatcher 计算差异
        sm = difflib.SequenceMatcher(None, orig_lines, fixed_lines)

        # 颜色格式
        delete_format = QTextCharFormat()
        delete_format.setBackground(QColor(80, 30, 30))
        delete_format.setForeground(QColor(255, 150, 150))

        insert_format = QTextCharFormat()
        insert_format.setBackground(QColor(30, 80, 30))
        insert_format.setForeground(QColor(150, 255, 150))

        left_text = []
        right_text = []
        left_formats = []  # (start, length, format)
        right_formats = []

        left_pos = 0
        right_pos = 0

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                # 相同行
                for line in orig_lines[i1:i2]:
                    left_text.append(line)
                    left_formats.append((left_pos, len(line), None))
                    left_pos += len(line)

                for line in fixed_lines[j1:j2]:
                    right_text.append(line)
                    right_formats.append((right_pos, len(line), None))
                    right_pos += len(line)

            elif tag == 'delete':
                # 仅在原始代码中存在（删除）
                for line in orig_lines[i1:i2]:
                    left_text.append(line)
                    left_formats.append((left_pos, len(line), delete_format))
                    left_pos += len(line)
                    # 右侧补空行保持对齐
                    right_text.append('\n')
                    right_formats.append((right_pos, 1, None))
                    right_pos += 1

            elif tag == 'insert':
                # 仅在修复代码中存在（新增）
                for line in fixed_lines[j1:j2]:
                    # 左侧补空行保持对齐
                    left_text.append('\n')
                    left_formats.append((left_pos, 1, None))
                    left_pos += 1

                    right_text.append(line)
                    right_formats.append((right_pos, len(line), insert_format))
                    right_pos += len(line)

            elif tag == 'replace':
                # 替换：同时显示删除和新增
                del_lines = orig_lines[i1:i2]
                ins_lines = fixed_lines[j1:j2]
                max_len = max(len(del_lines), len(ins_lines))

                for idx in range(max_len):
                    if idx < len(del_lines):
                        left_text.append(del_lines[idx])
                        left_formats.append((left_pos, len(del_lines[idx]), delete_format))
                        left_pos += len(del_lines[idx])
                    else:
                        left_text.append('\n')
                        left_formats.append((left_pos, 1, None))
                        left_pos += 1

                    if idx < len(ins_lines):
                        right_text.append(ins_lines[idx])
                        right_formats.append((right_pos, len(ins_lines[idx]), insert_format))
                        right_pos += len(ins_lines[idx])
                    else:
                        right_text.append('\n')
                        right_formats.append((right_pos, 1, None))
                        right_pos += 1

        # 设置文本
        left_content = ''.join(left_text)
        right_content = ''.join(right_text)

        self.left_edit.setPlainText(left_content.rstrip('\n'))
        self.right_edit.setPlainText(right_content.rstrip('\n'))

        # 应用格式
        self._apply_formats(self.left_edit, left_formats)
        self._apply_formats(self.right_edit, right_formats)

    def _apply_formats(self, editor, formats):
        """应用文本格式到编辑器"""
        cursor = editor.textCursor()
        for start, length, fmt in formats:
            if fmt is not None:
                cursor.setPosition(start)
                cursor.movePosition(
                    cursor.MoveOperation.Right,
                    cursor.MoveMode.KeepAnchor,
                    length
                )
                cursor.setCharFormat(fmt)


# =========================
# 简单的C++高亮器（用于自测）
# =========================
class SimpleCppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        keywords = ["int", "float", "double", "char", "void", "bool",
                    "class", "struct", "public", "private", "virtual",
                    "const", "return", "if", "else", "for", "while",
                    "new", "delete", "include", "using", "namespace"]
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#5B6BB8"))
        for word in keywords:
            self.rules.append((QRegularExpression(f"\\b{word}\\b"), keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#6B8E23"))
        self.rules.append((QRegularExpression(r'"[^"]*"'), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#8A9B8C"))
        self.rules.append((QRegularExpression(r"//[^\n]*"), comment_format))

        include_format = QTextCharFormat()
        include_format.setForeground(QColor("#5B6BB8"))
        self.rules.append((QRegularExpression(r"#include\s+<[^>]+>"), include_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


# =========================
# 自测入口
# =========================
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    original = '''#include <iostream>
using namespace std;

int main() {
    int* p = new int[10];
    // 忘记 delete
    return 0;
}
'''

    fixed = '''#include <iostream>
using namespace std;

int main() {
    int* p = new int[10];
    delete[] p;
    p = nullptr;
    return 0;
}
'''

    view = DiffView()
    view.set_diff(original, fixed)
    view.set_highlighter(SimpleCppHighlighter, "both")
    view.resize(1300, 600)
    view.show()

    sys.exit(app.exec())
