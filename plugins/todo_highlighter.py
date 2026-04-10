"""
官方插件：TODO 高亮器
扫描代码中的 TODO / FIXME / HACK / XXX 等标记，
在分析结果中汇总展示，支持点击跳转。

演示能力：
- after_analyze 钩子：向分析结果注入自定义数据
- get_menu_items：添加菜单项
- get_toolbar_buttons：添加工具栏按钮
- 与主窗口编辑器交互（获取文本、显示消息）
"""

from plugins.plugin_base import PluginBase
import re
from typing import List, Dict


class TodoHighlighter(PluginBase):
    """TODO 高亮器 - 扫描代码中的待办标记"""

    name = "TODO Highlighter"
    version = "1.0.0"
    description = "扫描代码中的 TODO/FIXME/HACK/XXX 标记，在分析结果中汇总展示"
    author = "AI IDE Team"

    # 默认扫描的标记（支持配置扩展）
    DEFAULT_TAGS = ["TODO", "FIXME", "HACK", "XXX", "NOTE", "WARNING"]

    def __init__(self):
        super().__init__()
        self.tags = list(self.DEFAULT_TAGS)
        self._last_todos: List[Dict] = []

    # =========================
    # 分析钩子
    # =========================

    def after_analyze(self, code: str, result: Dict) -> Dict:
        """分析后钩子：扫描 TODO 标记并注入分析结果"""
        todos = self._scan_todos(code)
        self._last_todos = todos

        if todos:
            # 注入到分析结果的 suggestions 中
            # 使用特殊前缀让主窗口识别为插件数据
            result["_plugin_todos"] = todos

            # 同时在建议列表中添加（便于统一展示）
            for todo in todos:
                result.setdefault("suggestions", []).append({
                    "line": todo["line"],
                    "desc": f"[{todo['tag']}] {todo['text']}",
                    "level": "low"
                })

        return result

    def _scan_todos(self, code: str) -> List[Dict]:
        """扫描代码中的 TODO 标记

        支持格式：
        - // TODO: 描述
        - /* FIXME: 描述 */
        - # TODO 描述
        - /** NOTE: 描述 */

        Returns:
            [{"line": 行号, "tag": 标记名, "text": 描述文本}]
        """
        todos = []
        lines = code.splitlines()

        # 构建正则：匹配注释中的标记
        # 支持 // /* /** # 等注释前缀
        tag_pattern = "|".join(re.escape(tag) for tag in self.tags)
        pattern = re.compile(
            r"(?:^\s*(?://|/\*|/\*\*|#)\s*)(" + tag_pattern + r")[:\s]\s*(.+)$",
            re.IGNORECASE
        )

        for line_no, line in enumerate(lines, start=1):
            # 移除行尾注释结束符（如 */）
            clean_line = line.rstrip().rstrip("*/").strip()

            match = pattern.search(clean_line)
            if match:
                tag = match.group(1).upper()
                text = match.group(2).strip()
                todos.append({
                    "line": line_no,
                    "tag": tag,
                    "text": text
                })

        return todos

    # =========================
    # UI 扩展
    # =========================

    def get_menu_items(self) -> List[Dict]:
        """添加菜单项"""
        return [
            {
                "name": "🔍 TODO 扫描 - 扫描当前文件",
                "callback": self.scan_current_file,
                "shortcut": "Ctrl+Shift+T",
            },
            {
                "name": "📋 TODO 列表 - 显示上次扫描结果",
                "callback": self.show_last_results,
            }
        ]

    def get_toolbar_buttons(self) -> List[Dict]:
        """添加工具栏按钮"""
        return [
            {
                "name": "TODO",
                "callback": self.scan_current_file,
                "icon": "🔍",
            }
        ]

    # =========================
    # 功能实现
    # =========================

    def scan_current_file(self):
        """扫描当前文件并在分析面板显示结果"""
        code = self.get_editor_text()
        if not code.strip():
            self.show_message("<p>⚠️ 编辑器为空，请先打开或输入代码</p>")
            return

        todos = self._scan_todos(code)
        self._last_todos = todos
        self._display_todos(todos)

    def show_last_results(self):
        """显示上次扫描结果"""
        if not self._last_todos:
            self.show_message("<p>ℹ️ 暂无扫描结果，请先扫描文件</p>")
            return
        self._display_todos(self._last_todos)

    def _display_todos(self, todos: List[Dict]):
        """在分析面板显示 TODO 列表"""
        if not todos:
            self.show_message("""
                <h3>✅ TODO 扫描结果</h3>
                <p>未发现任何 TODO / FIXME / HACK / XXX 标记</p>
                <p><i>支持的标记：{}</i></p>
            """.format(", ".join(self.tags)))
            return

        # 按标记类型分组
        grouped: Dict[str, List[Dict]] = {}
        for todo in todos:
            grouped.setdefault(todo["tag"], []).append(todo)

        # 构建 HTML 输出
        tag_emoji = {
            "TODO": "📌",
            "FIXME": "🐛",
            "HACK": "🔧",
            "XXX": "⚠️",
            "NOTE": "📝",
            "WARNING": "🔔"
        }

        html = f"<h3>🔍 TODO 扫描结果</h3>"
        html += f"<p>共发现 <b>{len(todos)}</b> 个标记</p><hr>"

        for tag in sorted(grouped.keys()):
            items = grouped[tag]
            emoji = tag_emoji.get(tag, "📋")
            html += f"<h4>{emoji} {tag} ({len(items)})</h4>"

            for item in items:
                html += f'<p>• <a href="line:{item["line"]}">第{item["line"]}行</a> - {item["text"]}</p>'

        html += "<hr><p><i>支持的标记：{}</i></p>".format(", ".join(self.tags))
        self.show_message(html)
