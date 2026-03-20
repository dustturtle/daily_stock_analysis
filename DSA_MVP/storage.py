# -*- coding: utf-8 -*-
"""
DSA_MVP — 数据持久化模块

使用 SQLite 存储分析结果，支持历史查询。
"""

import logging
import os
import sqlite3
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    sentiment_score INTEGER,
    trend_prediction TEXT,
    operation_advice TEXT,
    analysis_summary TEXT,
    risk_warning TEXT,
    price REAL,
    change_pct REAL,
    trend TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_INSERT_SQL = """\
INSERT INTO analysis (
    stock_code, stock_name, sentiment_score, trend_prediction,
    operation_advice, analysis_summary, risk_warning, price, change_pct, trend
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_QUERY_LATEST_SQL = """\
SELECT * FROM analysis
WHERE stock_code = ?
ORDER BY created_at DESC
LIMIT ?
"""

_QUERY_ALL_LATEST_SQL = """\
SELECT * FROM analysis
ORDER BY created_at DESC
LIMIT ?
"""


def _ensure_dir(db_path: str) -> None:
    """确保数据库所在目录存在"""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


def init_db(db_path: str) -> None:
    """初始化数据库（创建表）

    Args:
        db_path: 数据库文件路径
    """
    _ensure_dir(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(_CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()
    logger.info("数据库已初始化: %s", db_path)


def save_analysis(
    db_path: str,
    stock_code: str,
    stock_name: str,
    technical_data: Dict[str, Any],
    analysis: Dict[str, Any],
) -> None:
    """保存分析结果到数据库

    Args:
        db_path: 数据库文件路径
        stock_code: 股票代码
        stock_name: 股票名称
        technical_data: 技术指标数据
        analysis: LLM 分析结果
    """
    _ensure_dir(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(_CREATE_TABLE_SQL)
        conn.execute(
            _INSERT_SQL,
            (
                stock_code,
                stock_name,
                analysis.get("sentiment_score"),
                analysis.get("trend_prediction"),
                analysis.get("operation_advice"),
                analysis.get("analysis_summary"),
                analysis.get("risk_warning"),
                technical_data.get("price"),
                technical_data.get("change_pct"),
                technical_data.get("trend"),
            ),
        )
        conn.commit()
        logger.info("分析结果已保存: %s %s", stock_code, stock_name)
    finally:
        conn.close()


def query_latest(
    db_path: str, stock_code: str, limit: int = 5
) -> List[Dict[str, Any]]:
    """查询指定股票的最近分析记录

    Args:
        db_path: 数据库文件路径
        stock_code: 股票代码
        limit: 返回记录数上限

    Returns:
        记录列表（字典形式）
    """
    if not os.path.exists(db_path):
        logger.debug("数据库文件不存在: %s", db_path)
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(_QUERY_LATEST_SQL, (stock_code, limit))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def query_all_latest(
    db_path: str, limit: int = 20
) -> List[Dict[str, Any]]:
    """查询所有股票的最近分析记录

    Args:
        db_path: 数据库文件路径
        limit: 返回记录数上限

    Returns:
        记录列表（字典形式）
    """
    if not os.path.exists(db_path):
        logger.debug("数据库文件不存在: %s", db_path)
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(_QUERY_ALL_LATEST_SQL, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
