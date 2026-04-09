import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from API_Call_SDK_v1 import AIClient


class CppAnalyzer:
    def __init__(self):
        self.ai = AIClient()

    def build_prompt(self, code: str) -> str:
        return f"""
你是一个资深C++/Qt工程师，请对以下代码进行全面质量分析：

{code}

请从以下维度进行分析，并尽量推断出问题所在的行号：

1. **bugs（严重问题）**：编译错误、运行时崩溃、未定义行为、逻辑错误等
2. **thread_issues（线程问题）**：数据竞争、死锁、原子操作不当等
3. **memory_issues（内存问题）**：内存泄漏、野指针、重复释放、越界访问等
4. **security（安全漏洞）**：缓冲区溢出、注入风险、不安全的函数调用等
5. **readability（可读性）**：命名不规范、代码过长、缺少注释、魔法数字等
6. **maintainability（可维护性）**：重复代码、紧耦合、违反单一职责原则等
7. **performance（性能）**：不必要的拷贝、低效的算法、频繁的内存分配等
8. **suggestions（优化建议）**：现代化C++特性建议、设计模式应用等

输出严格JSON格式（不要markdown代码块）：

{{
  "summary": "代码整体评估，包括优点和主要改进方向",
  "complexity": "simple/medium/complex",
  "bugs": [
    {{"level": "high/medium/low", "line": 行号或-1, "desc": "问题描述"}}
  ],
  "thread_issues": [
    {{"level": "high/medium/low", "line": 行号或-1, "desc": "问题描述"}}
  ],
  "memory_issues": [
    {{"level": "high/medium/low", "line": 行号或-1, "desc": "问题描述"}}
  ],
  "security": [
    {{"level": "high/medium/low", "line": 行号或-1, "desc": "问题描述"}}
  ],
  "readability": [
    {{"level": "high/medium/low", "line": 行号或-1, "desc": "问题描述"}}
  ],
  "maintainability": [
    {{"level": "high/medium/low", "line": 行号或-1, "desc": "问题描述"}}
  ],
  "performance": [
    {{"level": "high/medium/low", "line": 行号或-1, "desc": "问题描述"}}
  ],
  "suggestions": [
    {{"level": "high/medium/low", "line": 行号或-1, "desc": "建议描述"}}
  ]
}}

要求：
- level必须标注严重程度（high/medium/low）
- line字段尽量提供具体行号，无法确定时设为-1
- 如果没有某类问题，返回空数组
- 只输出JSON，不要有其他内容
"""

    def analyze(self, code: str) -> dict:
        prompt = self.build_prompt(code)
        return self.ai.chat_json(prompt)
