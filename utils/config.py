"""
配置管理模块
统一管理应用配置，支持加载、保存、默认值回退
"""

import json
import os
import copy

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.moonshot.cn/v1",
    "model": "kimi-k2.5",
    "temperature": 1.0,
    "theme": "light"
}

# 缓存的配置
_cached_config = None


def get_default_config() -> dict:
    """返回默认配置的深拷贝"""
    return copy.deepcopy(DEFAULT_CONFIG)


def _ensure_config_dir():
    """确保配置目录存在"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)


def load_config() -> dict:
    """
    从文件加载配置。
    如果文件不存在或解析失败，返回默认配置。
    加载时会与默认配置合并，确保所有键都存在。
    """
    config = get_default_config()

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # 合并配置：以默认值为基础，用加载的值覆盖
            config.update(loaded)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[WARN] 配置文件读取失败: {e}，使用默认配置")

    return config


def save_config(config: dict):
    """
    保存配置到文件
    """
    _ensure_config_dir()
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"[ERROR] 配置文件保存失败: {e}")


def get_config() -> dict:
    """
    获取当前配置（单例模式）
    首次调用时加载并缓存，后续直接返回缓存
    """
    global _cached_config
    if _cached_config is None:
        _cached_config = load_config()
    return _cached_config


def reload_config() -> dict:
    """
    重新加载配置（用于外部修改后刷新）
    """
    global _cached_config
    _cached_config = load_config()
    return _cached_config
