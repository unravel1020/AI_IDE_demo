"""
示例插件：代码统计插件
统计代码的各种指标
"""

from plugins.plugin_base import PluginBase
import re


class StatsPlugin(PluginBase):
    """代码统计插件 - 统计代码复杂度指标"""

    name = "Code Stats"
    version = "1.0.0"
    description = "统计代码行数、函数数量、注释覆盖率等指标"
    author = "AI IDE Team"

    def after_analyze(self, code: str, result: dict) -> dict:
        """添加代码统计信息"""
        stats = self._analyze_code(code)
        result["_plugin_stats"] = stats
        return result

    def _analyze_code(self, code: str) -> dict:
        """分析代码统计信息"""
        lines = code.splitlines()
        total_lines = len(lines)

        # 空行
        empty_lines = sum(1 for line in lines if not line.strip())

        # 注释行
        comment_lines = sum(1 for line in lines if line.strip().startswith("//"))

        # 函数数量
        functions = len(re.findall(r'\b\w+\s+\w+\s*\([^)]*\)\s*\{', code))

        # 类数量
        classes = len(re.findall(r'\bclass\s+\w+', code))

        # 注释覆盖率
        code_lines = total_lines - empty_lines
        comment_ratio = (comment_lines / code_lines * 100) if code_lines > 0 else 0

        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "empty_lines": empty_lines,
            "comment_lines": comment_lines,
            "functions": functions,
            "classes": classes,
            "comment_ratio": round(comment_ratio, 1)
        }

    def get_menu_items(self):
        """添加菜单项"""
        return [
            {
                "name": "📊 代码统计 - 显示详细统计",
                "callback": self.show_stats,
            }
        ]

    def show_stats(self):
        """显示统计信息"""
        code = self.get_editor_text()
        if not code.strip():
            self.show_message("<p>请先打开一个代码文件</p>")
            return

        stats = self._analyze_code(code)

        html = "<h3>📊 代码统计</h3>"
        html += f'<p><b>总行数:</b> {stats["total_lines"]}</p>'
        html += f'<p><b>代码行:</b> {stats["code_lines"]}</p>'
        html += f'<p><b>空行:</b> {stats["empty_lines"]}</p>'
        html += f'<p><b>注释行:</b> {stats["comment_lines"]}</p>'
        html += f'<p><b>函数数:</b> {stats["functions"]}</p>'
        html += f'<p><b>类数:</b> {stats["classes"]}</p>'
        html += f'<p><b>注释覆盖率:</b> {stats["comment_ratio"]}%</p>'

        self.show_message(html)
