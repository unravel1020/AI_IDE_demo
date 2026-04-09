import os
import sys
import time
import json
from openai import OpenAI

# 确保能导入 utils
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.config import load_config


class AIClient:
    def __init__(self):
        # 加载配置
        config = load_config()

        # 优先使用环境变量，其次使用配置文件
        api_key = os.getenv("MOONSHOT_API_KEY") or config.get("api_key", "")
        if not api_key:
            raise ValueError("MOONSHOT_API_KEY not set (环境变量或配置文件)")

        base_url = config.get("base_url", "https://api.moonshot.cn/v1")
        self.model = config.get("model", "kimi-k2.5")
        self.temperature = config.get("temperature", 1.0)

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        # 多轮对话上下文
        self.messages = [
            {"role": "system", "content": "你是一个专业的工程助手"}
        ]

    # =========================
    # 普通对话
    # =========================
    def chat(self, prompt: str) -> str:
        return self._request(prompt, expect_json=False)

    # =========================
    # JSON结构化输出
    # =========================
    def chat_json(self, prompt: str) -> dict:
        json_prompt = f"""
你必须严格按照JSON格式输出。

{prompt}

要求：
- 只输出JSON
- 不要输出 ``` 或 ```json
- 不要解释
"""

        result = self._request(json_prompt, expect_json=True)

        # ✅ 清洗
        cleaned = self._clean_json_text(result)

        # ✅ 尝试解析
        try:
            return json.loads(cleaned)
        except Exception:
            print("[WARN] JSON解析失败，尝试修复...")

            fix_prompt = f"""
以下内容不是合法JSON，请修复：

{cleaned}

要求：
1. 只输出JSON
2. 不要解释
3. 不要添加字段
"""
            fixed = self._request(fix_prompt, expect_json=True)
            fixed_cleaned = self._clean_json_text(fixed)

            try:
                return json.loads(fixed_cleaned)
            except Exception:
                return {
                    "error": "JSON解析失败",
                    "raw": result
                }

    # =========================
    # 核心请求函数
    # =========================
    def _request(self, prompt: str, expect_json: bool) -> str:
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # ✅ JSON模式：独立上下文（防污染）
                if expect_json:
                    messages = [
                        {"role": "system", "content": "你是一个严格输出JSON的AI"},
                        {"role": "user", "content": prompt}
                    ]
                else:
                    self.messages.append({
                        "role": "user",
                        "content": prompt
                    })

                    # ✅ 裁剪上下文
                    if len(self.messages) > 20:
                        self.messages = self.messages[-20:]

                    messages = self.messages

                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature
                )

                reply = completion.choices[0].message.content

                # ✅ 只有普通聊天才写入上下文
                if not expect_json:
                    self.messages.append({
                        "role": "assistant",
                        "content": reply
                    })

                return reply

            except Exception as e:
                error_msg = str(e)

                if "overloaded" in error_msg or "429" in error_msg:
                    print(f"[Retry {attempt + 1}] 模型繁忙，重试中...")
                    time.sleep(2)
                    continue
                else:
                    return f"[ERROR] {error_msg}"

        return "[ERROR] 多次重试失败"

    # =========================
    # JSON清洗（关键）
    # =========================
    def _clean_json_text(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]

        text = text.replace("json", "", 1).strip()
        text = text.replace("```", "").strip()

        return text