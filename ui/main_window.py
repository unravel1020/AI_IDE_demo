from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QApplication,
    QFileDialog, QMenuBar, QTabWidget, QTextBrowser, QLabel,
    QSplitter, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, QUrl, Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QTextEdit

from PyQt6ElaWidgetTools import ElaWindow

from analyzer.cpp_analyzer import CppAnalyzer
from analyzer.code_fixer import CodeFixer
from analyzer.code_agent import CodeAgent
from analyzer.code_formatter import CodeFormatter
from analyzer.code_explainer import CodeExplainer

from ui.code_editor import CodeEditor
from ui.cpp_highlighter import CppHighlighter
from ui.diff_view import DiffView
from ui.settings_dialog import SettingsDialog
from ui.file_tree import FileTree
from ui.find_dialog import FindDialog, SearchHighlighter
from ui.snippet_panel import SnippetPanel
from ui.terminal_widget import TerminalWidget
from ui.plugin_panel import PluginPanel
from ui.chat_panel import ChatPanel
from plugins.plugin_manager import PluginManager

import qtawesome as qta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.config import get_config, reload_config
from utils.history import add_history, get_history_list, get_history_detail, delete_history, clear_history
from utils.report_exporter import ReportExporter


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


class FormatWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, formatter, code, style):
        super().__init__()
        self.formatter = formatter
        self.code = code
        self.style = style

    def run(self):
        try:
            result = self.formatter.format(self.code, self.style)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ExplainWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, explainer, code):
        super().__init__()
        self.explainer = explainer
        self.code = code

    def run(self):
        try:
            result = self.explainer.explain(self.code)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class BatchAnalyzeWorker(QThread):
    """批量分析工作线程"""
    file_started = pyqtSignal(str)   # 开始分析某个文件
    file_finished = pyqtSignal(str, dict)  # 某个文件分析完成
    all_finished = pyqtSignal(list)  # 全部完成
    error = pyqtSignal(str)

    def __init__(self, analyzer, file_list):
        super().__init__()
        self.analyzer = analyzer
        self.file_list = file_list
        self._running = True

    def run(self):
        results = []
        for file_path in self.file_list:
            if not self._running:
                break
            try:
                self.file_started.emit(file_path)
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                result = self.analyzer.analyze(code)
                result["_file_path"] = file_path
                result["_file_name"] = os.path.basename(file_path)
                self.file_finished.emit(file_path, result)
                results.append(result)
            except Exception as e:
                self.error.emit(f"{file_path}: {e}")
        self.all_finished.emit(results)

    def stop(self):
        self._running = False


# =========================
# 主窗口
# =========================
class MainWindow(ElaWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI C++ IDE v2.2.0")
        self.resize(1400, 850)

        self.analyzer = CppAnalyzer()
        self.fixer = CodeFixer()
        self.agent = CodeAgent()
        self.formatter = CodeFormatter()
        self.explainer = CodeExplainer()

        # 插件管理器（必须在 init_ui 之前创建，因为 init_ui 中的菜单需要使用）
        self.plugin_manager = PluginManager()
        self.plugin_manager.set_main_window(self)
        self.plugin_manager.load_all_plugins()

        # 搜索高亮器
        self.search_highlighter = None
        self.find_dialog = None

        # 实时分析
        self.auto_analyze_enabled = False
        self.auto_analyze_timer = QTimer()
        self.auto_analyze_timer.setSingleShot(True)
        self.auto_analyze_timer.timeout.connect(self.on_auto_analyze)

        self.init_ui()  # 内部完成所有组件创建和初始化

    def init_ui(self):
        # ===== 菜单 =====
        menu_bar = QMenuBar()

        file_menu = menu_bar.addMenu("文件(&F)")
        file_menu.addAction("📂 打开文件夹", self.open_folder)
        file_menu.addAction("📄 打开文件", self.open_file)
        file_menu.addSeparator()
        file_menu.addAction("💾 导出 Markdown 报告", self.export_markdown)
        file_menu.addAction("🌐 导出 HTML 报告", self.export_html)
        file_menu.addSeparator()
        file_menu.addAction("💾 保存结果", self.save_result)

        format_menu = menu_bar.addMenu("格式化(&O)")
        format_menu.addAction("✨ 格式化代码 (默认风格)", lambda: self.format_code("default"))
        format_menu.addAction("✨ 格式化代码 (Google风格)", lambda: self.format_code("google"))
        format_menu.addAction("✨ 格式化代码 (LLVM风格)", lambda: self.format_code("llvm"))

        plugin_menu = menu_bar.addMenu("🔌 插件")
        plugin_menu.addAction("🔄 重载插件", self.reload_plugins)
        plugin_menu.addSeparator()
        for item in self.plugin_manager.get_all_menu_items():
            plugin_menu.addAction(item["name"], item["callback"])

        settings_menu = menu_bar.addMenu("设置")
        settings_menu.addAction("⚙️ 偏好设置", self.open_settings)
        settings_menu.addAction("🔄 重载配置", self.reload_settings)
        settings_menu.addSeparator()
        settings_menu.addAction("🔄 切换实时分析", self.toggle_auto_analyze)

        self.setMenuBar(menu_bar)

        # =========================
        # 页面1: 工作台
        # =========================
        workbench_widget = QWidget()
        workbench_layout = QVBoxLayout(workbench_widget)
        workbench_layout.setContentsMargins(8, 8, 8, 4)
        workbench_layout.setSpacing(8)

        # ---- 编辑器区域：文件树 + 代码编辑器 ----
        editor_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.file_tree = FileTree()
        self.file_tree.setMaximumWidth(240)
        self.file_tree.file_clicked.connect(self.load_file_from_tree)

        self.code_input = CodeEditor()
        self.code_input.setFont(QFont("JetBrains Mono", 12))
        self.highlighter = CppHighlighter(self.code_input.document(), theme="light")

        editor_splitter.addWidget(self.file_tree)
        editor_splitter.addWidget(self.code_input)
        editor_splitter.setSizes([200, 800])
        editor_splitter.setHandleWidth(3)

        # 工具栏：操作按钮
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(6)

        self.btn_analyze = QPushButton("分析")
        self.btn_analyze.setIcon(qta.icon('fa5s.play'))
        self.btn_fix = QPushButton("修复")
        self.btn_fix.setIcon(qta.icon('fa5s.wrench'))
        self.btn_agent = QPushButton("智能")
        self.btn_agent.setIcon(qta.icon('fa5s.magic'))
        self.btn_format = QPushButton("格式化")
        self.btn_format.setIcon(qta.icon('fa5s.align-left'))
        self.btn_batch = QPushButton("批量")
        self.btn_batch.setIcon(qta.icon('fa5s.layer-group'))
        self.btn_explain = QPushButton("解释")
        self.btn_explain.setIcon(qta.icon('fa5s.book'))

        self.btn_analyze.setToolTip("分析代码 (Ctrl+R)")
        self.btn_fix.setToolTip("修复代码 (Ctrl+Shift+H)")
        self.btn_agent.setToolTip("AI 智能分析")
        self.btn_explain.setToolTip("解释代码 (Ctrl+E)")
        self.btn_format.setToolTip("格式化代码 (Ctrl+Shift+G)")
        self.btn_batch.setToolTip("批量分析 (Ctrl+B)")

        self.btn_analyze.clicked.connect(self.on_analyze)
        self.btn_fix.clicked.connect(self.on_fix)
        self.btn_agent.clicked.connect(self.on_agent)
        self.btn_format.clicked.connect(lambda: self.format_code("default"))
        self.btn_batch.clicked.connect(self.on_batch_analyze)
        self.btn_explain.clicked.connect(self.on_explain)

        toolbar_layout.addWidget(self.btn_analyze)
        toolbar_layout.addWidget(self.btn_fix)
        toolbar_layout.addWidget(self.btn_agent)
        toolbar_layout.addWidget(self.btn_explain)
        toolbar_layout.addWidget(self.btn_format)
        toolbar_layout.addWidget(self.btn_batch)
        toolbar_layout.addStretch()

        editor_area = QVBoxLayout()
        editor_area.setContentsMargins(0, 0, 0, 0)
        editor_area.setSpacing(6)
        editor_area.addWidget(editor_splitter, 1)
        editor_area.addLayout(toolbar_layout)

        editor_widget = QWidget()
        editor_widget.setLayout(editor_area)

        # ---- 底部 TabWidget：4个核心tab ----
        self.tabs = QTabWidget()

        self.tab_analysis = QTextBrowser()
        self.tab_analysis.anchorClicked.connect(self.on_link_clicked)

        self.tab_fix = CodeEditor()
        self.tab_fix.setReadOnly(True)

        self.tab_agent = CodeEditor()
        self.tab_agent.setReadOnly(True)

        for tab in [self.tab_fix, self.tab_agent]:
            tab.setFont(QFont("JetBrains Mono", 11))

        self.highlighter_fix = CppHighlighter(self.tab_fix.document(), theme="light")
        self.highlighter_agent = CppHighlighter(self.tab_agent.document(), theme="light")

        self.tab_diff = DiffView()
        self.tab_diff.set_highlighter(CppHighlighter, "both")

        self.tabs.addTab(self.tab_analysis, "分析结果")
        self.tabs.addTab(self.tab_fix, "修复代码")
        self.tabs.addTab(self.tab_diff, "Diff对比")
        self.tabs.addTab(self.tab_agent, "Agent输出")

        # 工作台主分割器：编辑器区域 | 底部 tabs
        workbench_splitter = QSplitter(Qt.Orientation.Vertical)
        workbench_splitter.addWidget(editor_widget)
        workbench_splitter.addWidget(self.tabs)
        workbench_splitter.setSizes([520, 280])
        workbench_splitter.setHandleWidth(3)

        workbench_layout.addWidget(workbench_splitter, 1)

        # 进度标签
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("font-weight: 500; padding: 4px;")
        workbench_layout.addWidget(self.progress_label)

        self.addPageNode("工作台", workbench_widget, "Home")

        # =========================
        # 页面2: AI助手
        # =========================
        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)
        ai_layout.setContentsMargins(8, 8, 8, 8)
        self.chat_panel = ChatPanel()
        ai_layout.addWidget(self.chat_panel)
        self.addPageNode("AI助手", ai_widget, "Chat")

        # =========================
        # 页面3: 历史记录
        # =========================
        self.tab_history = QTextBrowser()
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(8, 8, 8, 8)
        history_layout.addWidget(self.tab_history)
        self.addPageNode("历史记录", history_widget, "History")

        # =========================
        # 页面4: 代码片段
        # =========================
        self.tab_snippets = SnippetPanel()
        self.tab_snippets.snippet_selected.connect(self.insert_snippet)
        snippets_widget = QWidget()
        snippets_layout = QVBoxLayout(snippets_widget)
        snippets_layout.setContentsMargins(8, 8, 8, 8)
        snippets_layout.addWidget(self.tab_snippets)
        self.addPageNode("代码片段", snippets_widget, "Box")

        # =========================
        # 页面5: 终端
        # =========================
        self.tab_terminal = TerminalWidget()
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout(terminal_widget)
        terminal_layout.setContentsMargins(8, 8, 8, 8)
        terminal_layout.addWidget(self.tab_terminal)
        self.addPageNode("终端", terminal_widget, "Terminal")

        # =========================
        # 页面6: 插件
        # =========================
        self.tab_plugins = PluginPanel(self.plugin_manager)
        plugins_widget = QWidget()
        plugins_layout = QVBoxLayout(plugins_widget)
        plugins_layout.setContentsMargins(8, 8, 8, 8)
        plugins_layout.addWidget(self.tab_plugins)
        self.addPageNode("插件", plugins_widget, "Plugin")

        # ---- 初始化需要在组件创建后设置的内容 ----
        self.search_highlighter = SearchHighlighter(self.code_input)
        self.init_shortcuts()
        self.init_status_bar()
        self.init_auto_analyze()

    # =========================
    # 按钮状态管理
    # =========================
    def set_buttons_enabled(self, enabled: bool):
        self.btn_analyze.setEnabled(enabled)
        self.btn_fix.setEnabled(enabled)
        self.btn_agent.setEnabled(enabled)
        self.btn_format.setEnabled(enabled)
        self.btn_batch.setEnabled(enabled)
        self.btn_explain.setEnabled(enabled)

    # =========================
    # 文件
    # =========================
    def open_folder(self):
        """打开项目文件夹"""
        folder = self.file_tree.open_folder_dialog()
        if folder:
            self.tab_analysis.setHtml(f"<p>📂 已打开文件夹: {folder}</p>")

    def load_file_from_tree(self, file_path: str):
        """从文件树加载文件到编辑器"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.code_input.setPlainText(f.read())
            self.tab_terminal.set_current_file(file_path)
        except Exception as e:
            self.tab_analysis.setHtml(f'<p style="color:red;">❌ 无法读取文件: {e}</p>')

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "打开C++文件", "", "C++ Files (*.cpp *.h *.hpp)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.code_input.setPlainText(f.read())
            self.tab_terminal.set_current_file(file_path)

    def save_result(self):
        text = self.tab_analysis.toPlainText()
        if not text:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            None, "保存结果", "", "Text Files (*.txt)",
            options=QFileDialog.Option.DontUseNativeDialog
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
            self.tab_analysis.setHtml("<p>请输入代码</p>")
            return

        self.set_buttons_enabled(False)
        self.progress_label.setText("🔄 分析中...")
        self.tab_analysis.setHtml("<p>🔍 分析中...</p>")

        self.worker = AnalyzeWorker(self.analyzer, code)
        self.worker.finished.connect(self.show_analysis)
        self.worker.error.connect(self.on_error)
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

                # 红色高亮（IDE风格）
                extra.format.setBackground(QColor(255, 80, 80, 100))

                selections.append(extra)

        self.code_input.setExtraSelections(selections)

    def show_analysis(self, result):
        # 调用插件 after_analyze 钩子
        code = self.code_input.toPlainText()
        result = self.plugin_manager.call_after_analyze(code, result)

        html = "<h3>📊 分析结果</h3>"

        # 插件消息
        if "_plugin_message" in result:
            html += f'<p>{result.pop("_plugin_message")}</p>'
        if "_plugin_hello" in result:
            html += f'<p>{result.pop("_plugin_hello")}</p>'
        if "_plugin_stats" in result:
            stats = result.pop("_plugin_stats")
            html += f'<p>📊 代码: {stats["total_lines"]}行 | 函数: {stats["functions"]} | 注释: {stats["comment_ratio"]}%</p>'

        # 总结
        summary = result.get("summary", "")
        complexity = result.get("complexity", "unknown")
        if summary:
            html += f'<p><b>📝 总结：</b>{summary}</p>'
            html += f'<p><b>📈 复杂度：</b>{complexity}</p>'
            html += '<hr>'

        lines_to_highlight = []
        error_map = {}

        # 遍历所有问题类别
        categories = [
            ("🐛 Bugs", "bugs"),
            ("🔒 安全问题", "security"),
            ("🧵 线程问题", "thread_issues"),
            ("💾 内存问题", "memory_issues"),
            ("📖 可读性", "readability"),
            ("🔧 可维护性", "maintainability"),
            ("⚡ 性能", "performance"),
            ("💡 优化建议", "suggestions")
        ]

        for title, key in categories:
            items = result.get(key, [])
            if items:
                html += f'<h4>{title}</h4>'
                for item in items:
                    line = item.get("line", -1)
                    desc = item.get("desc", "")
                    level = item.get("level", "medium")
                    level_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(level, "⚪")

                    if line > 0:
                        html += f'<p>{level_emoji} <a href="line:{line}">第{line}行</a> - {desc}</p>'
                        lines_to_highlight.append(line)
                        error_map[line] = desc
                    else:
                        html += f'<p>{level_emoji} {desc}</p>'

        self.tab_analysis.setHtml(html)
        self.tabs.setCurrentIndex(0)

        # 自动标红
        self.highlight_lines(lines_to_highlight)

        # 传给编辑器（hover用）
        self.code_input.error_map = error_map
        self.code_input.update()
        self.code_input.line_number_area.update()

        self.set_buttons_enabled(True)
        self.progress_label.setText("")

        # 保存到历史记录
        try:
            add_history(self.code_input.toPlainText(), result, operation="analyze")
            self._refresh_history_view()
        except Exception as e:
            print(f"[WARN] 保存历史记录失败: {e}")

    def _refresh_history_view(self):
        """刷新历史记录视图"""
        history = get_history_list()
        if not history:
            self.tab_history.setHtml("<p>暂无历史记录</p>")
            return

        html = "<h3>📜 分析历史</h3>"
        html += f'<p>共 {len(history)} 条记录</p><hr>'

        for h in history:
            h_id = h["id"]
            file_name = h.get("file_name", "未命名")
            operation = h.get("operation", "analyze")
            op_emoji = {"analyze": "🔍", "fix": "🛠", "agent": "🧠"}.get(operation, "📋")
            total = h.get("total_issues", 0)
            complexity = h.get("complexity", "unknown")
            summary = h.get("summary", "") or "无摘要"

            html += f'<div style="margin:8px 0; padding:8px; border-radius:4px;">'
            html += f'<b>{op_emoji} {file_name}</b> '
            html += f'<span>({total}个问题 | 复杂度:{complexity})</span><br>'
            html += f'<span style="font-size:12px;">{summary}</span><br>'
            html += f'<a href="history:{h_id}">查看详情</a>'
            html += '</div>'

        self.tab_history.setHtml(html)
        # 只连接一次历史链接点击
        if not hasattr(self, '_history_linked'):
            self.tab_history.anchorClicked.connect(self._on_history_link_clicked)
            self._history_linked = True

    def _on_history_link_clicked(self, url: QUrl):
        """处理历史记录链接点击"""
        if url.toString().startswith("history:"):
            record_id = url.toString().split(":", 1)[1]
            self._load_history_detail(record_id)

    def _load_history_detail(self, record_id: str):
        """加载历史记录详情"""
        detail = get_history_detail(record_id)
        if not detail:
            return

        # 加载代码到编辑器
        self.code_input.setPlainText(detail["full_code"])

        # 加载结果到分析面板
        self.show_analysis(detail["full_result"])

        # 切换到分析标签
        self.tabs.setCurrentIndex(0)

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
        if not code.strip():
            self.tab_fix.setPlainText("请输入代码")
            return

        self.set_buttons_enabled(False)
        self.progress_label.setText("🔄 修复中...")
        self.tab_fix.setPlainText("修复中...")

        self.worker = FixWorker(self.fixer, code)
        self.worker.finished.connect(self.show_fix)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def show_fix(self, result):
        self.tab_fix.setPlainText(result)
        self.tab_diff.set_diff(self.code_input.toPlainText(), result)
        self.tabs.setCurrentIndex(1)
        self.set_buttons_enabled(True)
        self.progress_label.setText("")

    # =========================
    # Agent
    # =========================
    def on_agent(self):
        code = self.code_input.toPlainText()
        if not code.strip():
            self.tab_agent.setPlainText("请输入代码")
            return

        self.set_buttons_enabled(False)
        self.progress_label.setText("🔄 AI思考中...")
        self.tab_agent.setPlainText("AI思考中...")

        self.worker = AgentWorker(self.agent, code)
        self.worker.finished.connect(self.show_agent)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def show_agent(self, result):
        self.tab_agent.setPlainText(result)
        self.tabs.setCurrentIndex(2)
        self.set_buttons_enabled(True)
        self.progress_label.setText("")

    # =========================
    # 代码解释
    # =========================
    def on_explain(self):
        """解释代码"""
        code = self.code_input.toPlainText()
        if not code.strip():
            self.tab_analysis.setHtml("<p>请输入代码</p>")
            return

        self.set_buttons_enabled(False)
        self.progress_label.setText("📖 解释中...")
        self.tab_analysis.setHtml("<p>📖 AI 正在解释代码...</p>")

        self.worker = ExplainWorker(self.explainer, code)
        self.worker.finished.connect(self.show_explain)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def show_explain(self, result: str):
        """显示代码解释"""
        # 将纯文本转换为 HTML
        html = "<h3>📖 代码解释</h3><pre style='white-space:pre-wrap;'>"
        html += result.replace('<', '&lt;').replace('>', '&gt;')
        html += "</pre>"
        self.tab_analysis.setHtml(html)
        self.tabs.setCurrentIndex(0)
        self.set_buttons_enabled(True)
        self.progress_label.setText("")

    # =========================
    # 批量分析
    # =========================
    def on_batch_analyze(self):
        """批量分析选中的文件"""
        # 获取文件树中选中的文件
        selected_items = self.file_tree.selectedItems()
        file_paths = []
        for item in selected_items:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and os.path.isfile(path):
                file_paths.append(path)

        if not file_paths:
            self.tab_analysis.setHtml("<p>请先在文件树中选择要分析的文件（支持Ctrl/Shift多选）</p>")
            return

        self.set_buttons_enabled(False)
        self.progress_label.setText(f"📑 批量分析 0/{len(file_paths)}...")
        self.tab_analysis.setHtml(f"<p>📑 开始批量分析 {len(file_paths)} 个文件...</p>")

        self.batch_results = []
        self.batch_worker = BatchAnalyzeWorker(self.analyzer, file_paths)
        self.batch_worker.file_started.connect(self._on_batch_file_started)
        self.batch_worker.file_finished.connect(self._on_batch_file_finished)
        self.batch_worker.all_finished.connect(self._on_batch_all_finished)
        self.batch_worker.error.connect(self.on_error)
        self.batch_worker.start()

    def _on_batch_file_started(self, file_path: str):
        self.progress_label.setText(f"📑 分析: {os.path.basename(file_path)}...")

    def _on_batch_file_finished(self, file_path: str, result: dict):
        self.batch_results.append(result)
        self.progress_label.setText(f"📑 已完成 {len(self.batch_results)} 个文件")

    def _on_batch_all_finished(self, results: list):
        self.set_buttons_enabled(True)
        self.progress_label.setText("")
        self._show_batch_results(results)

    def _show_batch_results(self, results: list):
        """显示批量分析结果汇总"""
        if not results:
            self.tab_analysis.setHtml("<p>批量分析完成，无结果</p>")
            return

        html = "<h3>📑 批量分析结果汇总</h3>"
        html += f'<p>共分析 {len(results)} 个文件</p><hr>'

        for r in results:
            file_name = r.get("_file_name", "未知")
            complexity = r.get("complexity", "unknown")

            # 统计问题数
            total = 0
            for key in ["bugs", "security", "thread_issues", "memory_issues",
                        "readability", "maintainability", "performance", "suggestions"]:
                total += len(r.get(key, []))

            html += f'<div style="margin:6px 0; padding:8px; border-radius:4px;">'
            html += f'<b>{file_name}</b> '
            html += f'<span>({total}个问题 | 复杂度:{complexity})</span>'
            html += '</div>'

        self.tab_analysis.setHtml(html)
        self.tabs.setCurrentIndex(0)

    # =========================
    # 格式化
    # =========================
    def format_code(self, style: str = "default"):
        """格式化代码"""
        code = self.code_input.toPlainText()
        if not code.strip():
            self.tab_analysis.setHtml("<p>请输入代码</p>")
            return

        self.set_buttons_enabled(False)
        self.progress_label.setText("✨ 格式化中...")
        self.tab_analysis.setHtml("<p>✨ 格式化中...</p>")

        self.worker = FormatWorker(self.formatter, code, style)
        self.worker.finished.connect(self.show_formatted)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def show_formatted(self, result):
        """显示格式化结果"""
        self.code_input.setPlainText(result)
        self.tab_analysis.setHtml("<p>✅ 代码已格式化</p>")
        self.set_buttons_enabled(True)
        self.progress_label.setText("")

    # =========================
    # 导出报告
    # =========================
    def export_markdown(self):
        """导出 Markdown 报告"""
        try:
            result = self._get_last_analysis_result()
            if not result:
                self.tab_analysis.setHtml("<p>请先进行分析，再导出报告</p>")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                None, "导出 Markdown 报告", "report.md", "Markdown (*.md)",
                options=QFileDialog.Option.DontUseNativeDialog
            )
            if file_path:
                path = ReportExporter.export_markdown(
                    self.code_input.toPlainText(),
                    result,
                    file_path=file_path
                )
                self.tab_analysis.setHtml(f"<p>✅ 报告已导出:<br>{path}</p>")
        except Exception as e:
            self.tab_analysis.setHtml(f'<p style="color:red;">❌ 导出失败: {e}</p>')

    def export_html(self):
        """导出 HTML 报告"""
        try:
            result = self._get_last_analysis_result()
            if not result:
                self.tab_analysis.setHtml("<p>请先进行分析，再导出报告</p>")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                None, "导出 HTML 报告", "report.html", "HTML (*.html)",
                options=QFileDialog.Option.DontUseNativeDialog
            )
            if file_path:
                path = ReportExporter.export_html(
                    self.code_input.toPlainText(),
                    result,
                    file_path=file_path
                )
                self.tab_analysis.setHtml(f"<p>✅ 报告已导出:<br>{path}</p>")
        except Exception as e:
            self.tab_analysis.setHtml(f'<p style="color:red;">❌ 导出失败: {e}</p>')

    def _get_last_analysis_result(self):
        """获取最后一次分析结果（从历史记录中）"""
        history = get_history_list()
        if history:
            detail = get_history_detail(history[0]["id"])
            if detail:
                return detail.get("full_result", {})
        return {}

    # =========================
    # 设置
    # =========================
    def insert_snippet(self, code: str):
        """插入代码片段到编辑器"""
        cursor = self.code_input.textCursor()
        cursor.insertText(code + "\n")
        self.code_input.setTextCursor(cursor)
        self.tabs.setCurrentIndex(0)  # 切换到编辑器

    def open_find_dialog(self):
        """打开查找对话框"""
        if self.find_dialog is not None:
            self.find_dialog.close()
        self.find_dialog = FindDialog(self, replace_mode=False)
        # 如果有选中文本，预填充
        selected = self.code_input.textCursor().selectedText()
        if selected:
            self.find_dialog.set_find_text(selected)
        self.find_dialog.find_next.connect(self.on_find_next)
        self.find_dialog.find_prev.connect(self.on_find_prev)
        self.find_dialog.finished.connect(self.on_find_dialog_closed)
        self.find_dialog.show()

    def open_replace_dialog(self):
        """打开替换对话框"""
        if self.find_dialog is not None:
            self.find_dialog.close()
        self.find_dialog = FindDialog(self, replace_mode=True)
        selected = self.code_input.textCursor().selectedText()
        if selected:
            self.find_dialog.set_find_text(selected)
        self.find_dialog.find_next.connect(self.on_find_next)
        self.find_dialog.find_prev.connect(self.on_find_prev)
        self.find_dialog.replace_one.connect(self.on_replace_one)
        self.find_dialog.replace_all.connect(self.on_replace_all)
        self.find_dialog.finished.connect(self.on_find_dialog_closed)
        self.find_dialog.show()

    def on_find_next(self, text: str, case_sensitive: bool, use_regex: bool):
        """查找下一个"""
        self.search_highlighter.highlight_all(text, case_sensitive, use_regex)
        found = self.search_highlighter.find_next(text, case_sensitive, use_regex)
        if not found and self.find_dialog:
            self.find_dialog.setWindowTitle(f"未找到: {text}")
        elif self.find_dialog:
            self.find_dialog.setWindowTitle("替换" if self.find_dialog.replace_mode else "查找")

    def on_find_prev(self, text: str, case_sensitive: bool, use_regex: bool):
        """查找上一个"""
        self.search_highlighter.highlight_all(text, case_sensitive, use_regex)
        found = self.search_highlighter.find_prev(text, case_sensitive, use_regex)
        if not found and self.find_dialog:
            self.find_dialog.setWindowTitle(f"未找到: {text}")
        elif self.find_dialog:
            self.find_dialog.setWindowTitle("替换" if self.find_dialog.replace_mode else "查找")

    def on_replace_one(self, old: str, new: str, case_sensitive: bool, use_regex: bool):
        """替换当前匹配"""
        cursor = self.code_input.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == old:
            cursor.insertText(new)
        else:
            self.on_find_next(old, case_sensitive, use_regex)
            cursor = self.code_input.textCursor()
            if cursor.hasSelection():
                cursor.insertText(new)
        self.on_find_next(old, case_sensitive, use_regex)

    def on_replace_all(self, old: str, new: str, case_sensitive: bool, use_regex: bool):
        """替换全部匹配"""
        content = self.code_input.toPlainText()
        flags = 0 if case_sensitive else 2  # re.IGNORECASE
        import re
        pattern = re.escape(old) if not use_regex else old
        count = len(re.findall(pattern, content, flags))
        new_content = re.sub(pattern, new, content, flags=flags)
        self.code_input.setPlainText(new_content)
        self.search_highlighter.clear()
        if self.find_dialog:
            self.find_dialog.setWindowTitle(f"已替换 {count} 处")

    def on_find_dialog_closed(self):
        """查找对话框关闭时清除高亮"""
        self.search_highlighter.clear()
        self.find_dialog = None

    def init_auto_analyze(self):
        """初始化实时分析：监听文本变化"""
        self.code_input.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        """文本变化时触发自动分析（防抖）"""
        if self.auto_analyze_enabled:
            self.auto_analyze_timer.stop()
            self.auto_analyze_timer.start(2000)  # 2秒防抖

    def on_auto_analyze(self):
        """执行自动分析"""
        code = self.code_input.toPlainText()
        if code.strip() and len(code) > 50:  # 至少50个字符才分析
            self.on_analyze()

    def toggle_auto_analyze(self):
        """切换自动分析开关"""
        self.auto_analyze_enabled = not self.auto_analyze_enabled
        status = "已开启" if self.auto_analyze_enabled else "已关闭"
        self.tab_analysis.setHtml(f"<p>🔄 实时分析 {status} (修改代码2秒后自动触发)</p>")

    def reload_plugins(self):
        """重新加载所有插件"""
        self.plugin_manager.unload_all()
        self.plugin_manager.load_all_plugins()
        self.tab_analysis.setHtml(f"<p>✅ 插件已重载，共 {len(self.plugin_manager.plugins)} 个</p>")

    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            # 重新加载配置
            reload_config()
            self.tab_analysis.setHtml("<p>✅ 设置已保存，下次分析生效</p>")

    def reload_settings(self):
        """重新加载配置"""
        reload_config()
        config = get_config()
        self.tab_analysis.setHtml(f"<p>🔄 配置已重载<br>模型: {config.get('model')}<br>温度: {config.get('temperature')}</p>")

    # =========================
    # 错误处理
    # =========================
    def on_error(self, error_msg):
        self.tab_analysis.setHtml(f'<p style="color:red;">❌ 错误：{error_msg}</p>')
        self.set_buttons_enabled(True)
        self.progress_label.setText("")


    # =========================
    # 快捷键
    # =========================
    def init_shortcuts(self):
        """初始化快捷键"""
        from PyQt6.QtGui import QShortcut, QKeySequence

        # Ctrl+O: 打开文件
        shortcut_open = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_open.activated.connect(self.open_file)

        # Ctrl+S: 保存结果
        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(self.save_result)

        # Ctrl+R: 分析
        shortcut_analyze = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_analyze.activated.connect(self.on_analyze)

        # Ctrl+Shift+F: 修复 (Ctrl+F 用于查找)
        shortcut_fix = QShortcut(QKeySequence("Ctrl+Shift+H"), self)
        shortcut_fix.activated.connect(self.on_fix)

        # Ctrl+Shift+F: 格式化
        shortcut_format = QShortcut(QKeySequence("Ctrl+Shift+G"), self)
        shortcut_format.activated.connect(lambda: self.format_code("default"))

        # Ctrl+E: 解释代码
        shortcut_explain = QShortcut(QKeySequence("Ctrl+E"), self)
        shortcut_explain.activated.connect(self.on_explain)

        # Ctrl+B: 批量分析
        shortcut_batch = QShortcut(QKeySequence("Ctrl+B"), self)
        shortcut_batch.activated.connect(self.on_batch_analyze)

        # Ctrl+F: 查找
        shortcut_find = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_find.activated.connect(self.open_find_dialog)

        # Ctrl+H: 替换
        shortcut_replace = QShortcut(QKeySequence("Ctrl+H"), self)
        shortcut_replace.activated.connect(self.open_replace_dialog)

    # =========================
    # 状态栏
    # =========================
    def init_status_bar(self):
        """初始化状态栏"""
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("padding: 4px 8px;")
        self.statusBar().addWidget(self.status_label)

    def update_status(self, message: str):
        """更新状态栏消息"""
        self.status_label.setText(message)


# =========================
# 启动
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
