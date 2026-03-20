# -*- coding: utf-8 -*-
"""
DSA_MVP — 配置管理模块

从 .env 文件或环境变量读取配置，提供类型安全的访问接口。
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """MVP 配置类"""

    stock_list: List[str] = field(default_factory=list)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    db_path: str = "data/analysis.db"


def load_config(env_path: Optional[str] = None) -> Config:
    """加载配置

    Args:
        env_path: .env 文件路径，为 None 时自动查找

    Returns:
        Config 实例
    """
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    stock_list_raw = os.getenv("STOCK_LIST", "")
    stock_list = [s.strip() for s in stock_list_raw.split(",") if s.strip()]

    return Config(
        stock_list=stock_list,
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        llm_model=os.getenv("LLM_MODEL", "deepseek-chat"),
        db_path=os.getenv("DB_PATH", "data/analysis.db"),
    )
