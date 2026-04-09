"""
代码片段管理面板
支持常用代码模板的快速插入
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
    QDialog, QFormLayout, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
import json
import os


SNIPPET_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "snippets.json")

DEFAULT_SNIPPETS = {
    "hello": {
        "name": "Hello World",
        "code": '#include <iostream>\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}'
    },
    "class": {
        "name": "Class Template",
        "code": 'class MyClass {\npublic:\n    MyClass();\n    ~MyClass();\n\nprivate:\n\n};'
    },
    "for": {
        "name": "For Loop",
        "code": 'for (int i = 0; i < n; ++i) {\n    // TODO\n}'
    },
    "vector": {
        "name": "Vector Include",
        "code": '#include <vector>\nstd::vector<int> vec;'
    },
    "try": {
        "name": "Try-Catch",
        "code": 'try {\n    // code\n} catch (const std::exception& e) {\n    // handle error\n}'
    }
}


def load_snippets():
    """加载代码片段"""
    if os.path.exists(SNIPPET_FILE):
        try:
            with open(SNIPPET_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return dict(DEFAULT_SNIPPETS)
    return dict(DEFAULT_SNIPPETS)


def save_snippets(snippets):
    """保存代码片段"""
    os.makedirs(os.path.dirname(SNIPPET_FILE), exist_ok=True)
    with open(SNIPPET_FILE, "w", encoding="utf-8") as f:
        json.dump(snippets, f, ensure_ascii=False, indent=2)


class SnippetPanel(QWidget):
    """代码片段面板"""

    snippet_selected = pyqtSignal(str)  # 选中的代码

    def __init__(self, parent=None):
        super().__init__(parent)
        self.snippets = load_snippets()
        self.init_ui()
        self.refresh_list()

    def init_ui(self):
        layout = QVBoxLayout()

        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 搜索片段...")
        self.search_box.textChanged.connect(self.on_search)
        layout.addWidget(self.search_box)

        # 片段列表
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_widget)

        # 按钮
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ 新建")
        self.btn_add.clicked.connect(self.on_add)
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.refresh_list)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_refresh)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def refresh_list(self):
        """刷新列表"""
        self.list_widget.clear()
        for key, data in self.snippets.items():
            item = QListWidgetItem(f"📄 {data['name']}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.list_widget.addItem(item)

    def on_search(self, text):
        """搜索过滤"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            key = item.data(Qt.ItemDataRole.UserRole)
            data = self.snippets.get(key, {})
            visible = text.lower() in data.get("name", "").lower() or text.lower() in key.lower()
            item.setHidden(not visible)

    def on_item_clicked(self, item):
        """点击插入"""
        key = item.data(Qt.ItemDataRole.UserRole)
        data = self.snippets.get(key, {})
        code = data.get("code", "")
        if code:
            self.snippet_selected.emit(code)

    def show_context_menu(self, position):
        """右键菜单"""
        item = self.list_widget.itemAt(position)
        if not item:
            return

        menu = QMenu(self)
        menu.addAction("📝 编辑", lambda: self.on_edit(item))
        menu.addAction("🗑 删除", lambda: self.on_delete(item))
        menu.exec(self.list_widget.viewport().mapToGlobal(position))

    def on_add(self):
        """新建片段"""
        dialog = SnippetEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            key = dialog.get_key()
            data = dialog.get_data()
            if key and data:
                self.snippets[key] = data
                save_snippets(self.snippets)
                self.refresh_list()

    def on_edit(self, item):
        """编辑片段"""
        key = item.data(Qt.ItemDataRole.UserRole)
        data = self.snippets.get(key, {})
        dialog = SnippetEditDialog(self, key, data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_key = dialog.get_key()
            new_data = dialog.get_data()
            if new_key and new_data:
                # 如果key变了，删除旧的
                if new_key != key:
                    del self.snippets[key]
                self.snippets[new_key] = new_data
                save_snippets(self.snippets)
                self.refresh_list()

    def on_delete(self, item):
        """删除片段"""
        key = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "确认删除", f"确定删除片段 '{key}' 吗？")
        if reply == QMessageBox.StandardButton.Yes:
            if key in self.snippets:
                del self.snippets[key]
                save_snippets(self.snippets)
                self.refresh_list()


class SnippetEditDialog(QDialog):
    """片段编辑对话框"""

    def __init__(self, parent=None, key="", data=None):
        super().__init__(parent)
        self.setWindowTitle("编辑片段" if data else "新建片段")
        self.resize(400, 300)
        self._key = key
        self.init_ui(data or {})

    def init_ui(self, data):
        layout = QFormLayout()

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("唯一标识(如: hello)")
        self.key_input.setText(self._key)
        layout.addRow("标识:", self.key_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("显示名称")
        self.name_input.setText(data.get("name", ""))
        layout.addRow("名称:", self.name_input)

        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText("代码内容...")
        self.code_input.setText(data.get("code", ""))
        self.code_input.setStyleSheet("background:#1e1e1e; color:white; font-family: Consolas;")
        layout.addRow("代码:", self.code_input)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

        self.setLayout(layout)

    def get_key(self):
        return self.key_input.text().strip()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "code": self.code_input.toPlainText()
        }
