"""
代码解释器
调用 AI 对代码进行逐行/整体解释
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from API_Call_SDK_v1 import AIClient


class CodeExplainer:
    """C++ 代码解释器"""

    def __init__(self):
        self.ai = AIClient()

    def explain(self, code: str, detail_level: str = "medium") -> str:
        """
        解释代码功能

        Args:
            code: 源代码
            detail_level: 详细程度 (brief/medium/detailed)

        Returns:
            解释文本
        """
        detail_desc = {
            "brief": "简要概述代码的主要功能和入口点",
            "medium": "逐函数解释代码功能，说明关键逻辑",
            "detailed": "逐行详细解释，包括每个变量的作用、算法原理、设计意图"
        }.get(detail_level, "medium")

        prompt = f"""
你是一个 C++ 代码讲解专家。请对以下代码进行解释。

解释要求：{detail_desc}

原始代码：

{code}

输出格式要求：
1. 先用一句话概括代码整体功能
2. 然后分点解释关键部分
3. 如果涉及算法，说明时间/空间复杂度
4. 如果涉及设计模式，指出使用了什么模式

要求：
- 使用中文回答
- 不要使用 ``` 包裹代码块
- 结构清晰，使用标题和列表
"""
        return self.ai.chat(prompt)

    def explain_function(self, code: str, function_name: str) -> str:
        """解释特定函数"""
        prompt = f"""
请解释以下 C++ 代码中 `{function_name}` 函数的功能：

{code}

要求：
1. 说明函数参数和返回值
2. 解释函数的主要逻辑
3. 指出可能的边界情况
- 使用中文，结构清晰
"""
        return self.ai.chat(prompt)
