"""
插件基类
所有插件必须继承此类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Optional


class PluginBase(ABC):
    """插件基类"""

    # 插件元数据
    name: str = "Unnamed Plugin"
    version: str = "0.0.1"
    description: str = "No description"
    author: str = "Unknown"
    enabled: bool = True

    def __init__(self):
        self._main_window = None

    # =========================
    # 生命周期钩子
    # =========================

    def on_load(self, main_window=None):
        """
        插件加载时调用

        Args:
            main_window: 主窗口实例，可用于操作UI
        """
        self._main_window = main_window

    def on_unload(self):
        """插件卸载时调用"""
        pass

    # =========================
    # 分析钩子
    # =========================

    def before_analyze(self, code: str) -> str:
        """
        分析前钩子，可修改代码

        Args:
            code: 原始代码

        Returns:
            修改后的代码（如不修改，直接返回code）
        """
        return code

    def after_analyze(self, code: str, result: Dict) -> Dict:
        """
        分析后钩子，可修改结果

        Args:
            code: 原始代码
            result: 分析结果字典

        Returns:
            修改后的结果
        """
        return result

    # =========================
    # UI 扩展
    # =========================

    def get_menu_items(self) -> List[Dict]:
        """
        返回菜单项列表

        Returns:
            [{"name": "菜单名", "callback": callable, "shortcut": "Ctrl+X"}]
        """
        return []

    def get_toolbar_buttons(self) -> List[Dict]:
        """
        返回工具栏按钮列表

        Returns:
            [{"name": "按钮名", "callback": callable, "icon": "emoji"}]
        """
        return []

    def get_sidebar_widget(self):
        """
        返回侧边栏自定义Widget（可选）

        Returns:
            QWidget 或 None
        """
        return None

    # =========================
    # 工具方法
    # =========================

    def get_main_window(self):
        """获取主窗口实例"""
        return self._main_window

    def get_editor_text(self) -> str:
        """获取编辑器当前文本"""
        if self._main_window:
            return self._main_window.code_input.toPlainText()
        return ""

    def set_editor_text(self, text: str):
        """设置编辑器文本"""
        if self._main_window:
            self._main_window.code_input.setPlainText(text)

    def show_message(self, message: str):
        """在主窗口显示消息"""
        if self._main_window:
            self._main_window.tab_analysis.setHtml(f"<p>{message}</p>")
