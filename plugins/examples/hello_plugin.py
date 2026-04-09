"""
示例插件：Hello Plugin
展示插件系统的基本用法
"""

from plugins.plugin_base import PluginBase


class HelloPlugin(PluginBase):
    """示例插件 - 在分析结果中添加问候语"""

    name = "Hello Plugin"
    version = "1.0.0"
    description = "在分析结果中添加问候语和统计信息"
    author = "AI IDE Team"

    def after_analyze(self, code: str, result: dict) -> dict:
        """分析后添加额外信息"""
        # 添加代码行数统计
        lines = len(code.splitlines())
        result["_plugin_hello"] = f"📊 代码共 {lines} 行"

        # 添加问候语
        issues = sum(len(result.get(k, [])) for k in [
            "bugs", "security", "thread_issues", "memory_issues",
            "readability", "maintainability", "performance", "suggestions"
        ])

        if issues == 0:
            result["_plugin_message"] = "🎉 恭喜！未发现任何问题！"
        elif issues < 3:
            result["_plugin_message"] = "👍 代码质量良好，仅有少量建议"
        else:
            result["_plugin_message"] = f"📋 发现 {issues} 个问题，建议逐一修复"

        return result

    def get_menu_items(self):
        """添加菜单项"""
        return [
            {
                "name": "🙋 Hello Plugin - 显示问候",
                "callback": self.say_hello,
            }
        ]

    def say_hello(self):
        """菜单回调"""
        self.show_message("<p>🙋 Hello from HelloPlugin!</p><p>这是插件系统的一个示例。</p>")
