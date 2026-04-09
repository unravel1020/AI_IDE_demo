"""
报告导出模块
支持导出分析结果为 Markdown / HTML 格式
"""

import os
from datetime import datetime
from typing import Dict, List


class ReportExporter:
    """分析报告导出器"""

    @staticmethod
    def export_markdown(
        code: str,
        result: Dict,
        file_name: str = "未命名",
        output_path: str = ""
    ) -> str:
        """
        导出为 Markdown 格式

        Returns:
            导出的文件路径
        """
        if not output_path:
            output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        lines = []
        lines.append(f"# 📊 C++ 代码分析报告")
        lines.append("")
        lines.append(f"**文件**: `{file_name}`  ")
        lines.append(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        lines.append(f"**复杂度**: {result.get('complexity', 'unknown')}")
        lines.append("")

        # 总结
        summary = result.get("summary", "")
        if summary:
            lines.append("## 📝 总结")
            lines.append("")
            lines.append(summary)
            lines.append("")

        # 问题统计
        categories = [
            ("🐛 Bugs", "bugs"),
            ("🔒 安全问题", "security"),
            ("🧵 线程问题", "thread_issues"),
            ("💾 内存问题", "memory_issues"),
            ("📖 可读性", "readability"),
            ("🔧 可维护性", "maintainability"),
            ("⚡ 性能", "performance"),
            ("💡 优化建议", "suggestions")
        ]

        total_issues = 0
        for _, key in categories:
            total_issues += len(result.get(key, []))

        lines.append(f"## 📈 问题统计 (共 {total_issues} 项)")
        lines.append("")
        lines.append("| 类别 | 数量 |")
        lines.append("|------|------|")
        for title, key in categories:
            count = len(result.get(key, []))
            if count > 0:
                lines.append(f"| {title} | {count} |")
        lines.append("")

        # 详细问题
        for title, key in categories:
            items = result.get(key, [])
            if items:
                lines.append(f"## {title}")
                lines.append("")
                for item in items:
                    level = item.get("level", "medium")
                    line = item.get("line", -1)
                    desc = item.get("desc", "")
                    level_badge = {"high": "🔴 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}.get(level, "⚪")
                    line_info = f"**第{line}行**" if line > 0 else ""
                    lines.append(f"- {level_badge} {line_info} {desc}")
                lines.append("")

        # 原始代码
        lines.append("## 📝 原始代码")
        lines.append("")
        lines.append("```cpp")
        lines.append(code)
        lines.append("```")
        lines.append("")

        lines.append("---")
        lines.append("*由 AI C++ IDE 自动生成*")

        content = "\n".join(lines)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return os.path.abspath(output_path)

    @staticmethod
    def export_html(
        code: str,
        result: Dict,
        file_name: str = "未命名",
        output_path: str = ""
    ) -> str:
        """
        导出为 HTML 格式

        Returns:
            导出的文件路径
        """
        if not output_path:
            output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        # 构建问题列表 HTML
        categories = [
            ("🐛 Bugs", "bugs"),
            ("🔒 安全问题", "security"),
            ("🧵 线程问题", "thread_issues"),
            ("💾 内存问题", "memory_issues"),
            ("📖 可读性", "readability"),
            ("🔧 可维护性", "maintainability"),
            ("⚡ 性能", "performance"),
            ("💡 优化建议", "suggestions")
        ]

        total_issues = sum(len(result.get(key, [])) for _, key in categories)

        issues_html = ""
        for title, key in categories:
            items = result.get(key, [])
            if items:
                issues_html += f'<div class="category"><h3>{title}</h3><ul>'
                for item in items:
                    level = item.get("level", "medium")
                    line = item.get("line", -1)
                    desc = item.get("desc", "")
                    level_class = level
                    line_info = f"<span class='line'>第{line}行</span>" if line > 0 else ""
                    issues_html += f'<li class="{level_class}">{line_info} {desc}</li>'
                issues_html += '</ul></div>'

        # 转义代码中的 HTML 特殊字符
        escaped_code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>C++ 代码分析报告 - {file_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
            line-height: 1.6;
        }}
        h1 {{ color: #4EC9B0; border-bottom: 2px solid #4EC9B0; padding-bottom: 10px; }}
        h2 {{ color: #569CD6; margin-top: 30px; }}
        h3 {{ color: #CE9178; }}
        .meta {{ color: #858585; margin: 15px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #3c3c3c; padding: 8px 12px; text-align: left; }}
        th {{ background: #252526; }}
        .category {{ margin: 20px 0; padding: 15px; background: #252526; border-radius: 8px; }}
        .category ul {{ padding-left: 20px; }}
        .category li {{ margin: 8px 0; }}
        .high {{ color: #f48771; }}
        .medium {{ color: #dcdcaa; }}
        .low {{ color: #b5cea8; }}
        .line {{ color: #569CD6; font-weight: bold; margin-right: 8px; }}
        pre {{
            background: #252526;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: "Consolas", "Monaco", monospace;
            font-size: 13px;
        }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #3c3c3c; color: #858585; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <h1>📊 C++ 代码分析报告</h1>
    <div class="meta">
        <b>文件:</b> {file_name}<br>
        <b>时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        <b>复杂度:</b> {result.get('complexity', 'unknown')}<br>
        <b>问题总数:</b> {total_issues}
    </div>

    <h2>📝 总结</h2>
    <p>{result.get('summary', '无总结信息')}</p>

    <h2>📋 详细问题</h2>
    {issues_html}

    <h2>📝 原始代码</h2>
    <pre><code>{escaped_code}</code></pre>

    <div class="footer">
        由 AI C++ IDE 自动生成
    </div>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return os.path.abspath(output_path)
