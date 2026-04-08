import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from API_Call_SDK_v1 import AIClient


class CodeFixer:
    def __init__(self):
        self.ai = AIClient()

    def build_prompt(self, code: str) -> str:
        return f"""
你是一个资深C++工程师，请修复以下代码中的问题：

{code}

要求：
1. 修复所有潜在bug（尤其是内存/多态问题）
2. 保持原有逻辑不变
3. 返回“完整修复后的代码”
4. 不要解释
5. 不要使用 ``` 包裹
"""

    def fix(self, code: str) -> str:
        prompt = self.build_prompt(code)
        return self.ai.chat(prompt)