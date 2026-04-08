from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QApplication,
    QFileDialog, QMenuBar, QTabWidget
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont

from analyzer.cpp_analyzer import CppAnalyzer
from analyzer.code_fixer import CodeFixer
from analyzer.code_agent import CodeAgent

# 🔥 新增：IDE组件
from ui.code_editor import CodeEditor
from ui.cpp_highlighter import CppHighlighter

import sys


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
# 主窗口（IDE版）
# =========================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI C++ IDE（Agent版）")
        self.resize(1300, 750)

        # 核心模块
        self.analyzer = CppAnalyzer()
        self.fixer = CodeFixer()
        self.agent = CodeAgent()

        self.init_ui()

    # =========================
    # UI初始化
    # =========================
    def init_ui(self):
        layout = QVBoxLayout()

        # ===== 菜单栏 =====
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("文件")

        file_menu.addAction("打开.cpp文件", self.open_file)
        file_menu.addAction("保存分析结果", self.save_result)

        layout.setMenuBar(menu_bar)

        # ===== 主布局 =====
        main_layout = QHBoxLayout()

        # =========================
        # 左：代码编辑器（🔥 行号 + 高亮）
        # =========================
        self.code_input = CodeEditor()
        self.code_input.setFont(QFont("Consolas", 11))
        self.code_input.setStyleSheet("""
            background-color: #1e1e1e;
            color: #ffffff;
        """)

        # 🔥 启用语法高亮
        self.highlighter = CppHighlighter(self.code_input.document())

        # =========================
        # 右：Tab结果区（IDE核心）
        # =========================
        self.tabs = QTabWidget()

        # 分析结果
        self.tab_analysis = CodeEditor()
        self.tab_analysis.setReadOnly(True)

        # 修复代码
        self.tab_fix = CodeEditor()
        self.tab_fix.setReadOnly(True)

        # Agent输出
        self.tab_agent = CodeEditor()
        self.tab_agent.setReadOnly(True)

        # 设置字体
        for tab in [self.tab_analysis, self.tab_fix, self.tab_agent]:
            tab.setFont(QFont("Consolas", 10))
            tab.setStyleSheet("""
                background-color: #1e1e1e;
                color: #ffffff;
            """)

        self.tabs.addTab(self.tab_analysis, "分析结果")
        self.tabs.addTab(self.tab_fix, "修复代码")
        self.tabs.addTab(self.tab_agent, "Agent输出")

        main_layout.addWidget(self.code_input)
        main_layout.addWidget(self.tabs)

        # =========================
        # 按钮区
        # =========================
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
    # 文件操作
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

        if not code.strip():
            self.tab_analysis.setPlainText("请输入代码")
            return

        self.tab_analysis.setPlainText("🔍 分析中...")
        self.btn_analyze.setEnabled(False)

        self.worker = AnalyzeWorker(self.analyzer, code)
        self.worker.finished.connect(self.show_analysis)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def show_analysis(self, result):
        self.btn_analyze.setEnabled(True)
        self.tab_analysis.setPlainText(str(result))
        self.tabs.setCurrentIndex(0)

    # =========================
    # 修复
    # =========================
    def on_fix(self):
        code = self.code_input.toPlainText()

        if not code.strip():
            self.tab_fix.setPlainText("请输入代码")
            return

        self.tab_fix.setPlainText("🛠 修复中...")
        self.btn_fix.setEnabled(False)

        self.worker = FixWorker(self.fixer, code)
        self.worker.finished.connect(self.show_fix)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def show_fix(self, result):
        self.btn_fix.setEnabled(True)
        self.tab_fix.setPlainText(result)
        self.tabs.setCurrentIndex(1)

    # =========================
    # Agent
    # =========================
    def on_agent(self):
        code = self.code_input.toPlainText()

        if not code.strip():
            self.tab_agent.setPlainText("请输入代码")
            return

        self.tab_agent.setPlainText("🧠 AI思考中...")
        self.btn_agent.setEnabled(False)

        self.worker = AgentWorker(self.agent, code)
        self.worker.finished.connect(self.show_agent)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def show_agent(self, result):
        self.btn_agent.setEnabled(True)
        self.tab_agent.setPlainText(result)
        self.tabs.setCurrentIndex(2)

    # =========================
    # 错误处理
    # =========================
    def on_error(self, error_msg):
        self.btn_analyze.setEnabled(True)
        self.btn_fix.setEnabled(True)
        self.btn_agent.setEnabled(True)

        self.tab_analysis.setPlainText(f"❌ 错误：{error_msg}")


# =========================
# 启动
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())