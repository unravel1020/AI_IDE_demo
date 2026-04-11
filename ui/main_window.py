from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QApplication,
    QFileDialog, QMenuBar, QTabWidget, QTextBrowser, QLabel,
    QSplitter, QWidget, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import QThread, pyqtSignal, QUrl, Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QTextEdit

from PyQt6ElaWidgetTools import ElaWindow, ElaTheme, ElaThemeType

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
from ui.search_panel import SearchPanel
from plugins.plugin_manager import PluginManager

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.config import get_config, reload_config
from utils.history import add_history, get_history_list, get_history_detail, delete_history, clear_history
from utils.report_exporter import ReportExporter

import qtawesome as qta


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
    file_started = pyqtSignal(str)
    file_finished = pyqtSignal(str, dict)
    all_finished = pyqtSignal(list)
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

        self._nav_buttons = []
        self._page_stack = None

        self.init_ui()

    def init_ui(self):
        # ===== 菜单 =====
        menu_bar = QMenuBar()

        file_menu = menu_bar.addMenu("文件(&F)")
        a_open_folder = file_menu.addAction("打开文件夹")
        a_open_folder.triggered.connect(self.open_folder)
        a_open_file = file_menu.addAction("打开文件")
        a_open_file.triggered.connect(self.open_file)
        file_menu.addSeparator()
        a_search = file_menu.addAction("项目内搜索")
        a_search.triggered.connect(self.open_search_panel)
        file_menu.addSeparator()
        a_export_md = file_menu.addAction("导出 Markdown 报告")
        a_export_md.triggered.connect(self.export_markdown)
        a_export_html = file_menu.addAction("导出 HTML 报告")
        a_export_html.triggered.connect(self.export_html)
        file_menu.addSeparator()
        a_save = file_menu.addAction("保存结果")
        a_save.triggered.connect(self.save_result)

        format_menu = menu_bar.addMenu("格式化(&O)")
        a_fmt_default = format_menu.addAction("格式化代码 (默认风格)")
        a_fmt_default.triggered.connect(lambda: self.format_code("default"))
        a_fmt_google = format_menu.addAction("格式化代码 (Google风格)")
        a_fmt_google.triggered.connect(lambda: self.format_code("google"))
        a_fmt_llvm = format_menu.addAction("格式化代码 (LLVM风格)")
        a_fmt_llvm.triggered.connect(lambda: self.format_code("llvm"))

        plugin_menu = menu_bar.addMenu("插件")
        a_reload_plugins = plugin_menu.addAction("重载插件")
        a_reload_plugins.triggered.connect(self.reload_plugins)
        plugin_menu.addSeparator()
        for item in self.plugin_manager.get_all_menu_items():
            a = plugin_menu.addAction(item["name"])
            a.triggered.connect(item["callback"])

        settings_menu = menu_bar.addMenu("设置")
        a_settings = settings_menu.addAction("偏好设置")
        a_settings.triggered.connect(self.open_settings)
        a_reload_cfg = settings_menu.addAction("重载配置")
        a_reload_cfg.triggered.connect(self.reload_settings)
        settings_menu.addSeparator()
        a_toggle_auto = settings_menu.addAction("切换实时分析")
        a_toggle_auto.triggered.connect(self.toggle_auto_analyze)

        self.setMenuBar(menu_bar)

        # =========================
        # 创建所有子组件（先创建，后布局）
        # =========================
        # 文件树
        self.file_tree = FileTree()
        self.file_tree.setMaximumWidth(240)
        self.file_tree.file_clicked.connect(self.load_file_from_tree)

        # 代码编辑器
        self.code_input = CodeEditor()
        self.code_input.setFont(QFont("JetBrains Mono", 12))
        self.highlighter = CppHighlighter(self.code_input.document(), theme="light")

        # Tab 组件
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

        # 其他页面组件
        self.chat_panel = ChatPanel()
        self.tab_history = QTextBrowser()
        self.tab_snippets = SnippetPanel()
        self.tab_snippets.snippet_selected.connect(self.insert_snippet)
        self.tab_terminal = TerminalWidget()
        self.tab_plugins = PluginPanel(self.plugin_manager)

        # =========================
        # 组装各页面
        # =========================

        # ---- 页面1: 工作台 ----
        workbench_widget = QWidget()
        workbench_layout = QVBoxLayout(workbench_widget)
        workbench_layout.setContentsMargins(8, 8, 8, 4)
        workbench_layout.setSpacing(8)

        # 编辑器区域：文件树 + 代码编辑器
        editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        editor_splitter.addWidget(self.file_tree)
        editor_splitter.addWidget(self.code_input)
        editor_splitter.setSizes([200, 800])
        editor_splitter.setHandleWidth(3)

        # 工具栏
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

        for btn, tooltip in [
            (self.btn_analyze, "分析代码 (Ctrl+R)"),
            (self.btn_fix, "修复代码 (Ctrl+Shift+H)"),
            (self.btn_agent, "AI 智能分析"),
            (self.btn_explain, "解释代码 (Ctrl+E)"),
            (self.btn_format, "格式化代码 (Ctrl+Shift+G)"),
            (self.btn_batch, "批量分析 (Ctrl+B)"),
        ]:
            btn.setToolTip(tooltip)

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

        # ---- 页面2: AI助手 ----
        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)
        ai_layout.setContentsMargins(8, 8, 8, 8)
        ai_layout.addWidget(self.chat_panel)

        # ---- 页面3: 历史记录 ----
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(8, 8, 8, 8)
        history_layout.addWidget(self.tab_history)

        # ---- 页面4: 代码片段 ----
        snippets_widget = QWidget()
        snippets_layout = QVBoxLayout(snippets_widget)
        snippets_layout.setContentsMargins(8, 8, 8, 8)
        snippets_layout.addWidget(self.tab_snippets)

        # ---- 页面5: 终端 ----
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout(terminal_widget)
        terminal_layout.setContentsMargins(8, 8, 8, 8)
        terminal_layout.addWidget(self.tab_terminal)

        # ---- 页面6: 插件 ----
        plugins_widget = QWidget()
        plugins_layout = QVBoxLayout(plugins_widget)
        plugins_layout.setContentsMargins(8, 8, 8, 8)
        plugins_layout.addWidget(self.tab_plugins)

        # =========================
        # 左侧导航栏 + 页面栈
        # =========================
        nav_widget = QWidget()
        nav_widget.setFixedWidth(180)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(4, 12, 4, 12)
        nav_layout.setSpacing(4)

        # 导航标题
        nav_title = QLabel("AI C++ IDE")
        nav_title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
        nav_layout.addWidget(nav_title)
        nav_layout.addSpacing(12)

        # 导航按钮
        nav_items = [
            ("工作台", qta.icon('fa5s.home')),
            ("AI助手", qta.icon('fa5s.comments')),
            ("历史记录", qta.icon('fa5s.history')),
            ("代码片段", qta.icon('fa5s.cube')),
            ("终端", qta.icon('fa5s.terminal')),
            ("插件", qta.icon('fa5s.puzzle-piece')),
        ]

        for name, icon in nav_items:
            btn = QPushButton(name)
            btn.setIcon(icon)
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, n=name: self._switch_page(n))
            nav_layout.addWidget(btn)
            self._nav_buttons.append((name, btn))

        nav_layout.addStretch()

        # 页面栈
        self._page_stack = QStackedWidget()
        self._page_stack.addWidget(workbench_widget)
        self._page_stack.addWidget(ai_widget)
        self._page_stack.addWidget(history_widget)
        self._page_stack.addWidget(snippets_widget)
        self._page_stack.addWidget(terminal_widget)
        self._page_stack.addWidget(plugins_widget)

        # 主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(nav_widget)
        main_layout.addWidget(self._page_stack)

        self.setCentralWidget(main_widget)

        # 默认选中工作台
        self._switch_page("工作台")

        # 初始化需要在组件创建后设置的内容
        self.search_highlighter = SearchHighlighter(self.code_input)
        self.init_shortcuts()
        self.init_status_bar()
        self.init_auto_analyze()

        # 连接主题变化信号
        ElaTheme.getInstance().themeModeChanged.connect(self.apply_theme)
        ElaTheme.getInstance().themeModeChanged.connect(self._save_theme_config)

        # 应用当前主题
        self.apply_theme()

    def _save_theme_config(self):
        """主题变化时自动保存到配置文件"""
        from utils.config import load_config, save_config
        is_dark = ElaTheme.getInstance().getThemeMode() == ElaThemeType.ThemeMode.Dark
        theme_name = "dark" if is_dark else "light"
        config = load_config()
        if config.get("theme") != theme_name:
            config["theme"] = theme_name
            save_config(config)

    def apply_theme(self):
        """应用当前主题到所有自定义组件"""
        from PyQt6ElaWidgetTools import ElaTheme, ElaThemeType
        is_dark = ElaTheme.getInstance().getThemeMode() == ElaThemeType.ThemeMode.Dark

        if is_dark:
            # 深色主题样式
            tab_style = """
                QTabWidget::pane { border: none; background: #1e1e1e; }
                QTabBar::tab {
                    background: #2d2d30;
                    color: #cccccc;
                    padding: 6px 16px;
                    border: none;
                    margin-right: 2px;
                }
                QTabBar::tab:selected { background: #1e1e1e; color: #ffffff; }
                QTabBar::tab:hover { background: #3e3e42; }
            """
            browser_style = """
                QTextBrowser {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                }
            """
            nav_btn_style = """
                QPushButton {
                    background: transparent;
                    color: #cccccc;
                    border: none;
                    padding: 8px 12px;
                    text-align: left;
                }
                QPushButton:hover { background: #3c3c3c; }
                QPushButton:checked { background: #094771; color: #ffffff; }
            """
            splitter_handle = """
                QSplitter::handle { background: #3c3c3c; }
            """
        else:
            # 浅色主题样式
            tab_style = """
                QTabWidget::pane { border: none; background: #ffffff; }
                QTabBar::tab {
                    background: #f0f0f0;
                    color: #333333;
                    padding: 6px 16px;
                    border: none;
                    margin-right: 2px;
                }
                QTabBar::tab:selected { background: #ffffff; color: #000000; border-bottom: 2px solid #0078d4; }
                QTabBar::tab:hover { background: #e5e5e5; }
            """
            browser_style = """
                QTextBrowser {
                    background-color: #ffffff;
                    color: #1e1e1e;
                    border: none;
                }
            """
            nav_btn_style = """
                QPushButton {
                    background: transparent;
                    color: #333333;
                    border: none;
                    padding: 8px 12px;
                    text-align: left;
                }
                QPushButton:hover { background: #e5e5e5; }
                QPushButton:checked { background: #0078d4; color: #ffffff; }
            """
            splitter_handle = """
                QSplitter::handle { background: #d4d4d4; }
            """

        # 应用到各组件
        self.tabs.setStyleSheet(tab_style)
        self.tab_analysis.setStyleSheet(browser_style)
        self.tab_history.setStyleSheet(browser_style)

        # 编辑器主题
        for editor in [self.code_input, self.tab_fix, self.tab_agent]:
            if hasattr(editor, 'apply_theme'):
                editor.apply_theme()

        # 文件树
        if hasattr(self, 'file_tree') and self.file_tree:
            self.file_tree.apply_theme()

        # 导航按钮
        for _, btn in self._nav_buttons:
            btn.setStyleSheet(nav_btn_style)

        # 工具栏按钮
        toolbar_btn_style = nav_btn_style if is_dark else nav_btn_style
        for btn in [self.btn_analyze, self.btn_fix, self.btn_agent,
                    self.btn_format, self.btn_batch, self.btn_explain]:
            btn.setStyleSheet(nav_btn_style)

    def _switch_page(self, name: str):
        """切换页面"""
        page_map = {
            "工作台": 0,
            "AI助手": 1,
            "历史记录": 2,
            "代码片段": 3,
            "终端": 4,
            "插件": 5,
        }
        if name in page_map:
            self._page_stack.setCurrentIndex(page_map[name])
            # 更新按钮状态
            for btn_name, btn in self._nav_buttons:
                btn.setChecked(btn_name == name)

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
        try:
            folder = self.file_tree.open_folder_dialog()
            if folder:
                self.tab_analysis.setHtml(f"<p>已打开文件夹: {folder}</p>")
        except Exception as e:
            print(f"[ERROR] open_folder: {e}")
            import traceback
            traceback.print_exc()

    def load_file_from_tree(self, file_path: str):
        """从文件树加载文件到编辑器"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.code_input.setPlainText(f.read())
            self.tab_terminal.set_current_file(file_path)
            self._update_file_info(file_path)
            self.update_status(f"已打开: {os.path.basename(file_path)}")
        except Exception as e:
            self.tab_analysis.setHtml(f'<p style="color:red;">无法读取文件: {e}</p>')

    def open_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "打开C++文件", "", "C++ Files (*.cpp *.h *.hpp)",
                options=QFileDialog.Option.DontUseNativeDialog
            )
            if file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.code_input.setPlainText(f.read())
                self.tab_terminal.set_current_file(file_path)
                self._update_file_info(file_path)
                self.update_status(f"已打开: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"[ERROR] open_file: {e}")
            import traceback
            traceback.print_exc()

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
        self.progress_label.setText("分析中...")
        self.tab_analysis.setHtml("<p>分析中...</p>")

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

        html = "<h3>分析结果</h3>"

        # 插件消息
        if "_plugin_message" in result:
            html += f'<p>{result.pop("_plugin_message")}</p>'
        if "_plugin_hello" in result:
            html += f'<p>{result.pop("_plugin_hello")}</p>'
        if "_plugin_stats" in result:
            stats = result.pop("_plugin_stats")
            html += f'<p>代码: {stats["total_lines"]}行 | 函数: {stats["functions"]} | 注释: {stats["comment_ratio"]}%</p>'

        # 总结
        summary = result.get("summary", "")
        complexity = result.get("complexity", "unknown")
        if summary:
            html += f'<p><b>总结：</b>{summary}</p>'
            html += f'<p><b>复杂度：</b>{complexity}</p>'
            html += '<hr>'

        lines_to_highlight = []
        error_map = {}

        # 遍历所有问题类别
        categories = [
            ("Bugs", "bugs"),
            ("安全问题", "security"),
            ("线程问题", "thread_issues"),
            ("内存问题", "memory_issues"),
            ("可读性", "readability"),
            ("可维护性", "maintainability"),
            ("性能", "performance"),
            ("优化建议", "suggestions")
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

        html = "<h3>分析历史</h3>"
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
        self.progress_label.setText("修复中...")
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
        self.progress_label.setText("AI思考中...")
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
        self.progress_label.setText("解释中...")
        self.tab_analysis.setHtml("<p>AI 正在解释代码...</p>")

        self.worker = ExplainWorker(self.explainer, code)
        self.worker.finished.connect(self.show_explain)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def show_explain(self, result: str):
        """显示代码解释"""
        # 将纯文本转换为 HTML
        html = "<h3>代码解释</h3><pre style='white-space:pre-wrap;'>"
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
        self.progress_label.setText(f"批量分析 0/{len(file_paths)}...")
        self.tab_analysis.setHtml(f"<p>开始批量分析 {len(file_paths)} 个文件...</p>")

        self.batch_results = []
        self.batch_worker = BatchAnalyzeWorker(self.analyzer, file_paths)
        self.batch_worker.file_started.connect(self._on_batch_file_started)
        self.batch_worker.file_finished.connect(self._on_batch_file_finished)
        self.batch_worker.all_finished.connect(self._on_batch_all_finished)
        self.batch_worker.error.connect(self.on_error)
        self.batch_worker.start()

    def _on_batch_file_started(self, file_path: str):
        self.progress_label.setText(f"分析: {os.path.basename(file_path)}...")

    def _on_batch_file_finished(self, file_path: str, result: dict):
        self.batch_results.append(result)
        self.progress_label.setText(f"已完成 {len(self.batch_results)} 个文件")

    def _on_batch_all_finished(self, results: list):
        self.set_buttons_enabled(True)
        self.progress_label.setText("")
        self._show_batch_results(results)

    def _show_batch_results(self, results: list):
        """显示批量分析结果汇总"""
        if not results:
            self.tab_analysis.setHtml("<p>批量分析完成，无结果</p>")
            return

        html = "<h3>批量分析结果汇总</h3>"
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
        self.progress_label.setText("格式化中...")
        self.tab_analysis.setHtml("<p>格式化中...</p>")

        self.worker = FormatWorker(self.formatter, code, style)
        self.worker.finished.connect(self.show_formatted)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def show_formatted(self, result):
        """显示格式化结果"""
        self.code_input.setPlainText(result)
        self.tab_analysis.setHtml("<p>代码已格式化</p>")
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
                self.tab_analysis.setHtml(f"<p>报告已导出:<br>{path}</p>")
        except Exception as e:
            self.tab_analysis.setHtml(f'<p style="color:red;">导出失败: {e}</p>')

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
                self.tab_analysis.setHtml(f"<p>报告已导出:<br>{path}</p>")
        except Exception as e:
            self.tab_analysis.setHtml(f'<p style="color:red;">导出失败: {e}</p>')

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
        self.tab_analysis.setHtml(f"<p>实时分析 {status} (修改代码2秒后自动触发)</p>")

    def reload_plugins(self):
        """重新加载所有插件"""
        self.plugin_manager.unload_all()
        self.plugin_manager.load_all_plugins()
        self.tab_analysis.setHtml(f"<p>插件已重载，共 {len(self.plugin_manager.plugins)} 个</p>")

    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        old_theme = get_config().get("theme", "light")

        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            # 重新加载配置
            reload_config()
            config = get_config()
            new_theme = config.get("theme", "light")

            # 应用主题变更（配置已保存，只需应用）
            if new_theme != old_theme:
                theme_mode = ElaThemeType.ThemeMode.Dark if new_theme == "dark" else ElaThemeType.ThemeMode.Light
                ElaTheme.getInstance().setThemeMode(theme_mode)
                self.apply_theme()

            self.tab_analysis.setHtml("<p>设置已保存</p>")

    def reload_settings(self):
        """重新加载配置"""
        reload_config()
        config = get_config()
        self.tab_analysis.setHtml(f"<p>配置已重载<br>模型: {config.get('model')}<br>温度: {config.get('temperature')}</p>")

    # =========================
    # 项目内搜索
    # =========================
    def open_search_panel(self):
        """打开项目内搜索面板"""
        try:
            # 获取当前项目路径（从文件树）
            root_path = self.file_tree.root_path

            if not root_path:
                self.tab_analysis.setHtml("<p>⚠️ 请先打开一个项目文件夹（文件 → 打开文件夹）</p>")
                return

            # 使用非模态窗口，避免 exec() 可能的问题
            self._search_panel = SearchPanel(self, root_path)
            self._search_panel.goto_line.connect(self._on_search_goto)
            self._search_panel.show()
        except Exception as e:
            import traceback
            print(f"[ERROR] open_search_panel: {e}")
            traceback.print_exc()
            self.tab_analysis.setHtml(f'<p style="color:red;">搜索面板错误: {e}</p>')

    def _on_search_goto(self, file_path: str, line_no: int):
        """从搜索结果跳转到文件行"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.code_input.setPlainText(f.read())
            self._update_file_info(file_path)
            self.update_status(f"已打开: {os.path.basename(file_path)}")

            # 跳转到指定行
            if line_no > 0:
                self.goto_line(line_no)
        except Exception as e:
            self.tab_analysis.setHtml(f'<p style="color:red;">无法打开文件: {e}</p>')

    # =========================
    # 错误处理
    # =========================
    def on_error(self, error_msg):
        self.tab_analysis.setHtml(f'<p style="color:red;">错误：{error_msg}</p>')
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

        # Ctrl+Shift+R: 项目内搜索（避免与输入法繁体切换冲突）
        shortcut_search = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        shortcut_search.activated.connect(self.open_search_panel)

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
        """初始化状态栏 - 多部分信息展示"""
        # 左侧：动态消息
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label)

        # 右侧：固定信息（永久显示）
        self.status_position = QLabel("Ln 1, Col 1")
        self.status_file_type = QLabel("Plain Text")
        self.status_encoding = QLabel("UTF-8")
        self.status_file_path = QLabel("")

        for widget in [self.status_position, self.status_file_type,
                       self.status_encoding, self.status_file_path]:
            widget.setStyleSheet("padding: 0 8px;")
            self.statusBar().addPermanentWidget(widget)

        # 连接编辑器光标变化信号
        self.code_input.cursorPositionChanged.connect(self._update_cursor_position)

    def _update_cursor_position(self):
        """更新光标位置显示"""
        cursor = self.code_input.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.status_position.setText(f"Ln {line}, Col {col}")

    def _update_file_info(self, file_path: str = ""):
        """更新文件相关信息"""
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            type_map = {
                ".cpp": "C++",
                ".c": "C",
                ".h": "C/C++ Header",
                ".hpp": "C++ Header",
                ".cc": "C++",
                ".cxx": "C++",
                ".hxx": "C++ Header",
            }
            self.status_file_type.setText(type_map.get(ext, ext.upper()[1:] if ext else "Plain Text"))
            self.status_file_path.setText(os.path.basename(file_path))
        else:
            self.status_file_type.setText("Plain Text")
            self.status_file_path.setText("")

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
