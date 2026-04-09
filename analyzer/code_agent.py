import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from API_Call_SDK_v1 import AIClient


class CodeAgent:
    def __init__(self):
        self.ai = AIClient()

    def build_prompt(self, code: str) -> str:
        return f"""
你是一个高级C++代码审查Agent。

请分析以下代码，并"自行决策"如何处理：

{code}

你的任务：

1. 判断代码是否存在严重问题（内存/崩溃/未定义行为）
2. 如果问题严重：
   → 输出修复后的完整代码
3. 如果问题不严重：
   → 输出分析结果（JSON）

输出格式（二选一）：

【情况1：需要修复】
FIX:
<完整修复代码>

【情况2：仅分析】
ANALYSIS:
{{JSON}}

要求：
- 不要解释
- 不要使用 ``` 包裹
"""

    def run(self, code: str) -> str:
        prompt = self.build_prompt(code)
        return self.ai.chat(prompt)
