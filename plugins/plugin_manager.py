"""
插件管理器
负责加载、管理和调用插件
"""

import os
import sys
import importlib
import importlib.util
from typing import List, Dict, Optional
from plugins.plugin_base import PluginBase


class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.plugins: List[PluginBase] = []
        self.plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
        self._main_window = None

    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self._main_window = main_window

    # 系统文件，不应作为插件加载
    SYSTEM_FILES = {"plugin_base.py", "plugin_manager.py", "__init__.py"}

    def load_all_plugins(self):
        """加载所有插件"""
        self.plugins.clear()

        if not os.path.exists(self.plugin_dir):
            return

        # 遍历插件目录
        for item in os.listdir(self.plugin_dir):
            # 跳过系统文件、__pycache__ 和 examples
            if item.startswith("_") or item == "examples" or item in self.SYSTEM_FILES:
                continue

            plugin_path = os.path.join(self.plugin_dir, item)

            # 处理文件夹形式的插件
            if os.path.isdir(plugin_path):
                init_file = os.path.join(plugin_path, "__init__.py")
                if os.path.exists(init_file):
                    self._load_from_path(plugin_path, item)

            # 处理单文件插件
            elif item.endswith(".py"):
                self._load_from_file(plugin_path, item[:-3])

    def _load_from_path(self, path: str, name: str):
        """从文件夹加载插件"""
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.{name}",
                os.path.join(path, "__init__.py")
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugins.{name}"] = module
            spec.loader.exec_module(module)
            self._register_plugin(module)
        except Exception as e:
            print(f"[PluginManager] 加载插件 {name} 失败: {e}")

    def _load_from_file(self, path: str, name: str):
        """从文件加载插件"""
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.{name}",
                path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugins.{name}"] = module
            spec.loader.exec_module(module)
            self._register_plugin(module)
        except Exception as e:
            print(f"[PluginManager] 加载插件 {name} 失败: {e}")

    def _register_plugin(self, module):
        """注册模块中的插件类"""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, PluginBase) and
                attr is not PluginBase):
                plugin = attr()
                plugin.on_load(self._main_window)
                self.plugins.append(plugin)
                print(f"[PluginManager] 已加载插件: {plugin.name} v{plugin.version}")

    def unload_all(self):
        """卸载所有插件"""
        for plugin in self.plugins:
            plugin.on_unload()
        self.plugins.clear()

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """根据名称获取插件"""
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        return None

    def enable_plugin(self, name: str):
        """启用插件"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = True

    def disable_plugin(self, name: str):
        """禁用插件"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = False

    # =========================
    # 钩子调用
    # =========================

    def call_before_analyze(self, code: str) -> str:
        """调用分析前钩子"""
        for plugin in self.plugins:
            if plugin.enabled:
                try:
                    code = plugin.before_analyze(code)
                except Exception as e:
                    print(f"[PluginManager] 插件 {plugin.name} before_analyze 错误: {e}")
        return code

    def call_after_analyze(self, code: str, result: Dict) -> Dict:
        """调用分析后钩子"""
        for plugin in self.plugins:
            if plugin.enabled:
                try:
                    result = plugin.after_analyze(code, result)
                except Exception as e:
                    print(f"[PluginManager] 插件 {plugin.name} after_analyze 错误: {e}")
        return result

    def get_all_menu_items(self) -> List[Dict]:
        """获取所有插件的菜单项"""
        items = []
        for plugin in self.plugins:
            if plugin.enabled:
                items.extend(plugin.get_menu_items())
        return items

    def get_plugin_info(self) -> List[Dict]:
        """获取所有插件信息"""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "author": p.author,
                "enabled": p.enabled
            }
            for p in self.plugins
        ]
