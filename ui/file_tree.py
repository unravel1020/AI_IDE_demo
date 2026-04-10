"""
文件树组件
基于 QTreeWidget 的项目目录浏览器
"""

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QFileDialog, QMenu, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import os


class FileTree(QTreeWidget):
    """文件树组件"""

    # 信号：文件被点击时发射
    file_clicked = pyqtSignal(str)

    # 代码文件扩展名
    CODE_EXTENSIONS = {'.cpp', '.c', '.h', '.hpp', '.cc', '.cxx', '.hxx', '.inl'}

    def __init__(self, parent=None):
        super().__init__(parent)

        self.root_path = None

        # 基本设置
        self.setHeaderLabel("📁 项目文件")
        self.setColumnCount(1)

        # 样式由全局 QSS 主题控制，此处不设置硬编码样式

        # 允许右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # 点击事件
        self.itemClicked.connect(self._on_item_clicked)

        # 双击事件
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

        # 选择模式 - 支持多选
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def set_root_path(self, path: str):
        """设置根目录并刷新树"""
        if path and os.path.isdir(path):
            self.root_path = path
            self.refresh()

    def open_folder_dialog(self):
        """打开文件夹选择对话框"""
        folder = QFileDialog.getExistingDirectory(
            None, "选择项目文件夹",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if folder:
            self.set_root_path(folder)
            return folder
        return None

    def refresh(self):
        """刷新文件树"""
        self.clear()
        if not self.root_path or not os.path.isdir(self.root_path):
            return

        # 创建根节点
        root_name = os.path.basename(self.root_path) or self.root_path
        root_item = QTreeWidgetItem(self)
        root_item.setText(0, f"📂 {root_name}")
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.root_path)
        root_item.setExpanded(True)

        # 递归构建树
        self._build_tree(self.root_path, root_item)

    def _build_tree(self, path: str, parent_item: QTreeWidgetItem):
        """递归构建目录树"""
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return

        # 先处理文件夹，再处理文件
        dirs = []
        files = []

        for entry in entries:
            # 跳过隐藏文件/目录和构建产物
            if entry.startswith('.') or entry in {'__pycache__', 'node_modules', 'build', 'dist', 'out'}:
                continue

            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                dirs.append((entry, full_path))
            elif os.path.isfile(full_path):
                # 只显示代码文件
                _, ext = os.path.splitext(entry)
                if ext.lower() in self.CODE_EXTENSIONS:
                    files.append((entry, full_path))

        # 添加文件夹
        for name, full_path in dirs:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, f"📁 {name}")
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            self._build_tree(full_path, item)

        # 添加文件
        for name, full_path in files:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, f"📄 {name}")
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            # 代码文件用主题强调色
            item.setForeground(0, QColor("#5B6BB8"))

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """单击处理"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isfile(path):
            self.file_clicked.emit(path)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击处理 - 展开/折叠文件夹"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isdir(path):
            item.setExpanded(not item.isExpanded())

    def _show_context_menu(self, position):
        """显示右键菜单"""
        menu = QMenu(self)

        # 获取当前点击的项
        item = self.itemAt(position)

        # 通用操作
        menu.addAction("🔄 刷新", self.refresh)
        menu.addAction("📂 打开文件夹...", self.open_folder_dialog)

        if item:
            menu.addSeparator()
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and os.path.isfile(path):
                menu.addAction("📝 在编辑器中打开", lambda: self.file_clicked.emit(path))

        menu.exec(self.viewport().mapToGlobal(position))

    def get_current_file(self) -> str:
        """获取当前选中的文件路径"""
        item = self.currentItem()
        if item:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and os.path.isfile(path):
                return path
        return ""
