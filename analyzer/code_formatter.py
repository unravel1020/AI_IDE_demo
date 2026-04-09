"""
代码格式化器
调用 AI 对代码进行风格格式化（不改变逻辑）
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from API_Call_SDK_v1 import AIClient


class CodeFormatter:
    """C++ 代码格式化器"""

    def __init__(self):
        self.ai = AIClient()

    def build_prompt(self, code: str, style: str = "google") -> str:
        """
        构建格式化 Prompt

        Args:
            code: 原始代码
            style: 代码风格 (google/llvm/microsoft/mozilla)
        """
        style_desc = {
            "google": "Google C++ Style Guide (2空格缩进, 80列限制)",
            "llvm": "LLVM Coding Standards (2空格缩进)",
            "microsoft": "Microsoft C++ Style (4空格缩进)",
            "mozilla": "Mozilla C++ Style (2空格缩进)",
            "default": "标准 C++ 风格 (4空格缩进, 恰当的换行和括号位置)"
        }.get(style, style)

        return f"""
你是一个 C++ 代码格式化工具。请对以下代码进行风格格式化，**不要修改任何逻辑**。

风格要求：{style_desc}

需要执行的格式化操作：
1. 统一缩进（根据风格使用空格或制表符）
2. 统一括号位置（K&R 或 Allman 风格）
3. 适当的空格和换行
4. 统一命名规范（如果明显不一致）
5. 删除多余的空行和尾部空格
6. 保持代码功能**完全一致**

原始代码：

{code}

要求：
1. 只输出格式化后的代码
2. 不要解释
3. 不要使用 ``` 包裹
4. 保持所有注释
"""

    def format(self, code: str, style: str = "default") -> str:
        """
        格式化代码

        Args:
            code: 原始代码
            style: 代码风格

        Returns:
            格式化后的代码
        """
        if not code.strip():
            return ""

        prompt = self.build_prompt(code, style)
        return self.ai.chat(prompt)
