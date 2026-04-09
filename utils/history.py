"""
历史记录管理模块
保存和加载分析历史记录
"""

import json
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

# 历史记录文件路径
HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HISTORY_PATH = os.path.join(HISTORY_DIR, "history.json")

# 最大保存的历史记录数量
MAX_HISTORY = 50


def _ensure_history_dir():
    """确保历史记录目录存在"""
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)


def _load_history_raw() -> List[Dict]:
    """加载原始历史记录数据"""
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_history_raw(history: List[Dict]):
    """保存原始历史记录数据"""
    _ensure_history_dir()
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"[ERROR] 历史记录保存失败: {e}")


def _compute_code_hash(code: str) -> str:
    """计算代码哈希，用于去重"""
    return hashlib.md5(code.encode("utf-8")).hexdigest()[:12]


def add_history(
    code: str,
    result: Dict,
    file_path: str = "",
    operation: str = "analyze"
) -> str:
    """
    添加一条历史记录

    Args:
        code: 分析的源代码
        result: 分析结果字典
        file_path: 文件路径（如果有）
        operation: 操作类型（analyze/fix/agent）

    Returns:
        历史记录ID
    """
    history = _load_history_raw()

    # 生成唯一ID
    record_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_compute_code_hash(code)}"

    # 代码摘要（前200字符）
    code_preview = code[:200].replace('\n', ' ') + "..." if len(code) > 200 else code

    # 文件名
    file_name = os.path.basename(file_path) if file_path else "未命名"

    # 统计问题数量
    total_issues = 0
    for key in ["bugs", "security", "thread_issues", "memory_issues",
                "readability", "maintainability", "performance", "suggestions"]:
        total_issues += len(result.get(key, []))

    record = {
        "id": record_id,
        "timestamp": datetime.now().isoformat(),
        "file_name": file_name,
        "file_path": file_path,
        "operation": operation,
        "code_preview": code_preview,
        "code_hash": _compute_code_hash(code),
        "total_issues": total_issues,
        "complexity": result.get("complexity", "unknown"),
        "summary": result.get("summary", "")[:100] + "..." if len(result.get("summary", "")) > 100 else result.get("summary", ""),
        # 完整数据（压缩存储）
        "full_code": code,
        "full_result": result
    }

    # 添加到开头（最新的在前）
    history.insert(0, record)

    # 限制数量
    if len(history) > MAX_HISTORY:
        history = history[:MAX_HISTORY]

    _save_history_raw(history)
    return record_id


def get_history_list() -> List[Dict]:
    """
    获取历史记录列表（精简信息，用于UI展示）
    返回的字段：id, timestamp, file_name, operation, total_issues, complexity, summary
    """
    history = _load_history_raw()
    return [
        {
            "id": h["id"],
            "timestamp": h["timestamp"],
            "file_name": h["file_name"],
            "operation": h["operation"],
            "total_issues": h.get("total_issues", 0),
            "complexity": h.get("complexity", "unknown"),
            "summary": h.get("summary", "")
        }
        for h in history
    ]


def get_history_detail(record_id: str) -> Optional[Dict]:
    """
    获取某条历史记录的完整详情

    Returns:
        包含 full_code 和 full_result 的完整记录，或 None
    """
    history = _load_history_raw()
    for h in history:
        if h["id"] == record_id:
            return {
                "id": h["id"],
                "timestamp": h["timestamp"],
                "file_name": h["file_name"],
                "operation": h["operation"],
                "full_code": h.get("full_code", ""),
                "full_result": h.get("full_result", {})
            }
    return None


def delete_history(record_id: str) -> bool:
    """删除指定历史记录"""
    history = _load_history_raw()
    original_len = len(history)
    history = [h for h in history if h["id"] != record_id]
    if len(history) < original_len:
        _save_history_raw(history)
        return True
    return False


def clear_history():
    """清空所有历史记录"""
    _save_history_raw([])


def get_history_count() -> int:
    """获取历史记录数量"""
    return len(_load_history_raw())
