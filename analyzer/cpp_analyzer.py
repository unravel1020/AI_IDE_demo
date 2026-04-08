import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from API_Call_SDK_v1 import AIClient


class CppAnalyzer:
    def __init__(self):
        self.ai = AIClient()

    def build_prompt(self, code: str) -> str:
        return f"""
你是一个资深C++/Qt工程师，请分析以下代码：

{code}

分析内容：

1. bugs（严重问题）
2. thread_issues（线程问题）
3. memory_issues（内存问题）
4. suggestions（优化建议）

输出JSON：

{{
  "bugs": [
    {{"level": "high/medium/low", "desc": ""}}
  ],
  "thread_issues": [],
  "memory_issues": [],
  "suggestions": []
}}

要求：
- level必须标注严重程度
- 只输出JSON
"""

    def analyze(self, code: str) -> dict:
        prompt = self.build_prompt(code)
        return self.ai.chat_json(prompt)
