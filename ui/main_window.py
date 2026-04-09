from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QApplication,
    QFileDialog, QMenuBar, QTabWidget, QTextBrowser
)
from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QTextEdit

from analyzer.cpp_analyzer import CppAnalyzer
from analyzer.code_fixer import CodeFixer
from analyzer.code_agent import CodeAgent

from ui.code_editor import CodeEditor
from ui.cpp_highlighter import CppHighlighter

import sys


def highlight_lines(self, lines):
    selections = []

    for line_number in lines:
        block = self.code_input.document().findBlockByLineNumber(line_number - 1)

        if block.isValid():
            cursor = self.code_input.textCursor()
            cursor.setPosition(block.position())

            extra = QTextEdit.ExtraSelection()
            extra.cursor = cursor

            # 🔥 红色高亮
            extra.format.setBackground(QColor(255, 80, 80, 100))

            selections.append(extra)

    self.code_input.setExtraSelections(selections)
# =========================
# Worker线程
# =========================
class AnalyzeWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, analyzer, code):
        super().__init__()
        self.analyzer = analyzer
        self.code = code

    def run(self):
        try:
            result = self.analyzer.analyze(self.code)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class FixWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, fixer, code):
        super().__init__()
        self.fixer = fixer
        self.code = code

    def run(self):
        try:
            result = self.fixer.fix(self.code)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AgentWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, agent, code):
        super().__init__()
        self.agent = agent
        self.code = code

    def run(self):
        try:
            result = self.agent.run(self.code)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# =========================
# 主窗口
# =========================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI C++ IDE（增强版）")
        self.resize(1300, 750)

        self.analyzer = CppAnalyzer()
        self.fixer = CodeFixer()
        self.agent = CodeAgent()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ===== 菜单 =====
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("文件")
        file_menu.addAction("打开.cpp文件", self.open_file)
        file_menu.addAction("保存结果", self.save_result)
        layout.setMenuBar(menu_bar)

        # ===== 主布局 =====
        main_layout = QHBoxLayout()

        # 左：代码编辑器
        self.code_input = CodeEditor()
        self.code_input.setFont(QFont("Consolas", 11))
        self.code_input.setStyleSheet("background:#1e1e1e; color:white;")

        self.highlighter = CppHighlighter(self.code_input.document())

        # ===== 右：Tab =====
        self.tabs = QTabWidget()

        # 🔥 分析结果（支持点击）
        self.tab_analysis = QTextBrowser()
        self.tab_analysis.setStyleSheet("background:#1e1e1e; color:white;")
        self.tab_analysis.anchorClicked.connect(self.on_link_clicked)

        # 修复代码
        self.tab_fix = CodeEditor()
        self.tab_fix.setReadOnly(True)

        # Agent输出
        self.tab_agent = CodeEditor()
        self.tab_agent.setReadOnly(True)

        for tab in [self.tab_fix, self.tab_agent]:
            tab.setFont(QFont("Consolas", 10))
            tab.setStyleSheet("background:#1e1e1e; color:white;")

        # 🔥 给所有代码窗口加高亮
        self.highlighter_fix = CppHighlighter(self.tab_fix.document())
        self.highlighter_agent = CppHighlighter(self.tab_agent.document())

        self.tabs.addTab(self.tab_analysis, "分析结果")
        self.tabs.addTab(self.tab_fix, "修复代码")
        self.tabs.addTab(self.tab_agent, "Agent输出")

        main_layout.addWidget(self.code_input)
        main_layout.addWidget(self.tabs)

        # ===== 按钮 =====
        btn_layout = QHBoxLayout()

        self.btn_analyze = QPushButton("分析")
        self.btn_fix = QPushButton("修复")
        self.btn_agent = QPushButton("🧠 智能")

        self.btn_analyze.clicked.connect(self.on_analyze)
        self.btn_fix.clicked.connect(self.on_fix)
        self.btn_agent.clicked.connect(self.on_agent)

        btn_layout.addWidget(self.btn_analyze)
        btn_layout.addWidget(self.btn_fix)
        btn_layout.addWidget(self.btn_agent)

        layout.addLayout(main_layout)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    # =========================
    # 文件
    # =========================
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开C++文件", "", "C++ Files (*.cpp *.h)"
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.code_input.setPlainText(f.read())

    def save_result(self):
        text = self.tab_analysis.toPlainText()
        if not text:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", "", "Text Files (*.txt)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)

    # =========================
    # 分析
    # =========================
    def on_analyze(self):
        code = self.code_input.toPlainText()
        self.tab_analysis.setHtml("<p>🔍 分析中...</p>")

        self.worker = AnalyzeWorker(self.analyzer, code)
        self.worker.finished.connect(self.show_analysis)
        self.worker.start()

    def highlight_lines(self, lines):
        selections = []

        for line_number in lines:
            block = self.code_input.document().findBlockByLineNumber(line_number - 1)

            if block.isValid():
                cursor = self.code_input.textCursor()
                cursor.setPosition(block.position())

                extra = QTextEdit.ExtraSelection()
                extra.cursor = cursor

                # 🔥 红色高亮（IDE风格）
                extra.format.setBackground(QColor(255, 80, 80, 100))

                selections.append(extra)

        self.code_input.setExtraSelections(selections)

    def show_analysis(self, result):
        html = "<h3>分析结果</h3>"

        lines_to_highlight = []
        error_map = {}

        for bug in result.get("bugs", []):
            line = bug.get("line", -1)
            desc = bug.get("desc", "")

            if line > 0:
                html += f'<p><a href="line:{line}">第{line}行</a> - {desc}</p>'
                lines_to_highlight.append(line)

                # 🔥 hover用
                error_map[line] = desc
            else:
                html += f"<p>{desc}</p>"

        self.tab_analysis.setHtml(html)
        self.tabs.setCurrentIndex(0)

        # 🔥 自动标红
        self.highlight_lines(lines_to_highlight)

        # 🔥 传给编辑器（hover用）
        self.code_input.error_map = error_map
        self.code_input.update()
        self.code_input.line_number_area.update()

    # =========================
    # 点击跳转
    # =========================
    def on_link_clicked(self, url: QUrl):
        if url.toString().startswith("line:"):
            line = int(url.toString().split(":")[1])
            self.goto_line(line)

    def goto_line(self, line_number):
        cursor = self.code_input.textCursor()
        block = self.code_input.document().findBlockByLineNumber(line_number - 1)

        if not block.isValid():
            return

        cursor.setPosition(block.position())
        self.code_input.setTextCursor(cursor)

        selections = self.code_input.extraSelections()

        current = QTextEdit.ExtraSelection()
        current.cursor = cursor
        current.format.setBackground(QColor(255, 255, 0, 120))

        selections.append(current)

        self.code_input.setExtraSelections(selections)

    # =========================
    # 修复
    # =========================
    def on_fix(self):
        code = self.code_input.toPlainText()
        self.tab_fix.setPlainText("修复中...")

        self.worker = FixWorker(self.fixer, code)
        self.worker.finished.connect(self.tab_fix.setPlainText)
        self.worker.start()

    # =========================
    # Agent
    # =========================
    def on_agent(self):
        code = self.code_input.toPlainText()
        self.tab_agent.setPlainText("AI思考中...")

        self.worker = AgentWorker(self.agent, code)
        self.worker.finished.connect(self.tab_agent.setPlainText)
        self.worker.start()


# =========================
# 启动
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())