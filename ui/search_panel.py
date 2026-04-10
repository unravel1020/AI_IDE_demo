"""
项目内文件搜索面板
支持文件名搜索和文件内容搜索
快捷键: Ctrl+Shift+F
"""

import os
import re
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QLabel,
    QCheckBox, QComboBox, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class SearchWorker(QThread):
    """搜索工作线程"""
    result_found = pyqtSignal(str, int, str)  # 文件路径, 行号, 匹配行内容
    finished = pyqtSignal(int)  # 总结果数
    error = pyqtSignal(str)

    def __init__(self, root_path, pattern, options):
        super().__init__()
        self.root_path = root_path
        self.pattern = pattern
        self.options = options
        self._running = True

    def run(self):
        try:
            count = 0
            search_content = self.options.get("search_content", True)
            case_sensitive = self.options.get("case_sensitive", False)
            use_regex = self.options.get("use_regex", False)
            file_pattern = self.options.get("file_pattern", "")

            # 编译正则或转义字符串
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                try:
                    compiled = re.compile(self.pattern, flags)
                except re.error as e:
                    self.error.emit(f"正则表达式错误: {e}")
                    return
            else:
                escaped = re.escape(self.pattern)
                flags = 0 if case_sensitive else re.IGNORECASE
                compiled = re.compile(escaped, flags)

            # 遍历目录
            for root, dirs, files in os.walk(self.root_path):
                if not self._running:
                    break

                # 跳过隐藏目录和构建产物
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in
                          {"__pycache__", "node_modules", "build", "dist", "out", ".git", ".idea", ".vscode"}]

                for filename in files:
                    if not self._running:
                        break

                    # 文件类型过滤
                    if file_pattern and not self._match_file_pattern(filename, file_pattern):
                        continue

                    file_path = os.path.join(root, filename)

                    # 搜索文件名
                    if not search_content:
                        if compiled.search(filename):
                            self.result_found.emit(file_path, 0, f"[文件名匹配] {filename}")
                            count += 1
                        continue

                    # 搜索文件内容
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line_no, line in enumerate(f, start=1):
                                if compiled.search(line):
                                    # 截断过长行
                                    display_line = line.strip()
                                    if len(display_line) > 100:
                                        display_line = display_line[:100] + "..."
                                    self.result_found.emit(file_path, line_no, display_line)
                                    count += 1
                    except (IOError, OSError):
                        continue

            self.finished.emit(count)
        except Exception as e:
            self.error.emit(str(e))

    def _match_file_pattern(self, filename, pattern):
        """检查文件名是否匹配模式（如 *.cpp）"""
        if pattern.startswith("*."):
            ext = pattern[1:]  # .cpp
            return filename.endswith(ext)
        return pattern in filename

    def stop(self):
        self._running = False


class SearchPanel(QWidget):
    """项目内搜索面板"""

    goto_line = pyqtSignal(str, int)  # 文件路径, 行号

    def __init__(self, parent=None, root_path=None):
        super().__init__(parent)
        self.root_path = root_path or ""
        self.worker = None
        self.result_items = []  # 缓存结果项

        self.setWindowTitle("项目内搜索")
        self.resize(700, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ===== 搜索输入区 =====
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索内容...")
        self.search_input.returnPressed.connect(self.start_search)
        search_layout.addWidget(self.search_input, 1)

        self.btn_search = QPushButton("🔍 搜索")
        self.btn_search.clicked.connect(self.start_search)
        search_layout.addWidget(self.btn_search)

        self.btn_stop = QPushButton("⏹️ 停止")
        self.btn_stop.clicked.connect(self.stop_search)
        self.btn_stop.setEnabled(False)
        search_layout.addWidget(self.btn_stop)

        layout.addLayout(search_layout)

        # ===== 选项区 =====
        options_group = QGroupBox("搜索选项")
        options_layout = QHBoxLayout()

        self.chk_case = QCheckBox("区分大小写")
        options_layout.addWidget(self.chk_case)

        self.chk_regex = QCheckBox("正则表达式")
        options_layout.addWidget(self.chk_regex)

        self.chk_content = QCheckBox("搜索内容")
        self.chk_content.setChecked(True)
        options_layout.addWidget(self.chk_content)

        options_layout.addStretch()

        # 文件类型过滤
        options_layout.addWidget(QLabel("文件类型:"))
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["所有文件", "*.cpp", "*.h", "*.hpp", "*.c", "*.py"])
        self.file_type_combo.setEditable(True)
        options_layout.addWidget(self.file_type_combo)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # ===== 进度条 =====
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 无限循环样式
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # ===== 结果统计 =====
        self.status_label = QLabel("准备搜索")
        layout.addWidget(self.status_label)

        # ===== 搜索结果树 =====
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["文件", "行号", "内容"])
        self.result_tree.setColumnWidth(0, 250)
        self.result_tree.setColumnWidth(1, 60)
        self.result_tree.itemClicked.connect(self.on_item_clicked)
        self.result_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.result_tree)

        # ===== 按钮栏 =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_clear = QPushButton("🧹 清空结果")
        self.btn_clear.clicked.connect(self.clear_results)
        btn_layout.addWidget(self.btn_clear)

        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 聚焦到搜索框
        self.search_input.setFocus()

    def set_root_path(self, path: str):
        """设置搜索根目录"""
        self.root_path = path

    def start_search(self):
        """开始搜索"""
        pattern = self.search_input.text().strip()
        if not pattern:
            self.status_label.setText("请输入搜索内容")
            return

        if not self.root_path or not os.path.isdir(self.root_path):
            self.status_label.setText("❌ 请先打开一个项目文件夹")
            return

        # 清空之前的结果
        self.clear_results()

        # 获取选项
        file_pattern = self.file_type_combo.currentText()
        if file_pattern == "所有文件":
            file_pattern = ""

        options = {
            "search_content": self.chk_content.isChecked(),
            "case_sensitive": self.chk_case.isChecked(),
            "use_regex": self.chk_regex.isChecked(),
            "file_pattern": file_pattern,
        }

        # 更新 UI 状态
        self.btn_search.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.status_label.setText("搜索中...")

        # 启动搜索线程
        self.worker = SearchWorker(self.root_path, pattern, options)
        self.worker.result_found.connect(self.on_result_found)
        self.worker.finished.connect(self.on_search_finished)
        self.worker.error.connect(self.on_search_error)
        self.worker.start()

    def stop_search(self):
        """停止搜索"""
        if self.worker:
            self.worker.stop()
        self.btn_search.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)

    def on_result_found(self, file_path: str, line_no: int, content: str):
        """收到搜索结果"""
        # 显示相对路径
        rel_path = os.path.relpath(file_path, self.root_path)

        item = QTreeWidgetItem()
        item.setText(0, rel_path)
        item.setText(1, str(line_no) if line_no > 0 else "-")
        item.setText(2, content)
        item.setData(0, Qt.ItemDataRole.UserRole, (file_path, line_no))

        # 设置等宽字体
        item.setFont(2, QFont("JetBrains Mono", 10))

        self.result_tree.addTopLevelItem(item)
        self.result_items.append(item)

    def on_search_finished(self, count: int):
        """搜索完成"""
        self.btn_search.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)

        if count == 0:
            self.status_label.setText("未找到匹配结果")
        else:
            self.status_label.setText(f"找到 {count} 个结果")

    def on_search_error(self, error_msg: str):
        """搜索错误"""
        self.btn_search.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"❌ {error_msg}")

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """单击预览"""
        pass  # 可以在这里添加预览功能

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击跳转"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            file_path, line_no = data
            self.goto_line.emit(file_path, line_no)
            self.close()

    def clear_results(self):
        """清空搜索结果"""
        self.result_tree.clear()
        self.result_items.clear()
        self.status_label.setText("准备搜索")

    def keyPressEvent(self, event):
        """处理按键事件"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
