"""
插件管理面板
管理插件的启用、禁用和配置
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QCheckBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal


class PluginPanel(QWidget):
    """插件管理面板"""

    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.init_ui()
        self.refresh_list()

    def init_ui(self):
        layout = QVBoxLayout()

        # 标题
        title = QLabel("🔌 插件管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # 说明
        desc = QLabel("启用/禁用插件，点击插件查看详情")
        desc.setStyleSheet("font-size: 12px;")
        layout.addWidget(desc)

        # 插件列表
        self.list_widget = QListWidget()
        # 样式由全局 QSS 主题控制
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

        # 按钮
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.refresh_list)
        self.btn_reload = QPushButton("🔃 重载所有")
        self.btn_reload.clicked.connect(self.reload_plugins)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_reload)
        layout.addLayout(btn_layout)

        # 详情区域
        self.detail_label = QLabel("点击插件查看详情")
        self.detail_label.setStyleSheet("padding: 10px;")
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)

        self.setLayout(layout)

    def refresh_list(self):
        """刷新插件列表"""
        self.list_widget.clear()
        info_list = self.plugin_manager.get_plugin_info()

        for info in info_list:
            status = "✅" if info["enabled"] else "⛔"
            item = QListWidgetItem(f"{status} {info['name']} v{info['version']}")
            item.setData(Qt.ItemDataRole.UserRole, info)
            self.list_widget.addItem(item)

    def reload_plugins(self):
        """重新加载所有插件"""
        self.plugin_manager.unload_all()
        self.plugin_manager.load_all_plugins()
        self.refresh_list()

    def on_item_clicked(self, item):
        """点击插件项"""
        info = item.data(Qt.ItemDataRole.UserRole)
        if not info:
            return

        # 显示详情
        html = f"<b>{info['name']}</b><br>"
        html += f"<span>版本: {info['version']}</span><br>"
        html += f"<span>作者: {info['author']}</span><br>"
        html += f"<span>状态: {'已启用' if info['enabled'] else '已禁用'}</span><br><br>"
        html += f"{info['description']}"
        self.detail_label.setText(html)

        # 切换启用状态
        if info["enabled"]:
            self.plugin_manager.disable_plugin(info["name"])
        else:
            self.plugin_manager.enable_plugin(info["name"])

        self.refresh_list()
