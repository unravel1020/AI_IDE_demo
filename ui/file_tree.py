"""
文件树组件
基于 QTreeWidget 的项目目录浏览器
"""

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QFileDialog, QMenu, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
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

        # 应用主题
        self.apply_theme()

        # 允许右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # 点击事件
        self.itemClicked.connect(self._on_item_clicked)

        # 双击事件
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

        # 选择模式 - 支持多选
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def apply_theme(self):
        """应用当前主题"""
        from PyQt6ElaWidgetTools import ElaTheme, ElaThemeType
        is_dark = ElaTheme.getInstance().getThemeMode() == ElaThemeType.ThemeMode.Dark

        if is_dark:
            self.setStyleSheet("""
                QTreeWidget {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                }
                QTreeWidget::item {
                    padding: 4px 2px;
                }
                QTreeWidget::item:selected {
                    background-color: #094771;
                    color: #ffffff;
                }
                QTreeWidget::item:hover {
                    background-color: #2a2d2e;
                }
                QHeaderView::section {
                    background-color: #2d2d30;
                    color: #cccccc;
                    padding: 6px;
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("")

    def set_root_path(self, path: str):
        """设置根目录并刷新树"""
        if path and os.path.isdir(path):
            self.root_path = path
            # 使用延迟刷新避免 Qt 内部状态问题
            QTimer.singleShot(10, self._do_refresh)

    def _do_refresh(self):
        """实际执行刷新（在延迟后）"""
        # 安全清除：先 block 信号，再逐层删除
        self.blockSignals(True)
        try:
            # 手动删除顶层项，而不是 clear()
            while self.topLevelItemCount() > 0:
                item = self.takeTopLevelItem(0)
                del item
        finally:
            self.blockSignals(False)

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
        except (PermissionError, OSError):
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
        menu.addAction("🔄 刷新", self._do_refresh)
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
