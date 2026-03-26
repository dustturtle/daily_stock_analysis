# -*- coding: utf-8 -*-
"""
DSA_MVP — 行情数据获取模块

使用 akshare 获取 A 股日 K 线数据，返回标准化的 DataFrame。
"""

import logging
from typing import Optional

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)

# 标准化列名映射（akshare 中文列 → 英文列）
_COLUMN_MAP = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "change_pct",
    "涨跌额": "change_amount",
    "换手率": "turnover",
}


def get_stock_data(stock_code: str, days: int = 60) -> pd.DataFrame:
    """获取股票日 K 线数据

    Args:
        stock_code: A 股代码，如 "600519"
        days: 获取最近多少个交易日的数据

    Returns:
        标准化列名的 DataFrame（date, open, close, high, low, volume, ...）

    Raises:
        ValueError: 股票代码无效或无数据
    """
    logger.info("获取 %s 日 K 线数据（最近 %d 天）", stock_code, days)
    try:
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            adjust="qfq",
        )
    except Exception as exc:
        raise ValueError(f"获取 {stock_code} 行情数据失败: {exc}") from exc

    if df is None or df.empty:
        raise ValueError(f"股票 {stock_code} 无数据，请检查代码是否正确")

    df = df.rename(columns=_COLUMN_MAP)
    df = df.tail(days).reset_index(drop=True)
    return df


def get_stock_name(stock_code: str) -> Optional[str]:
    """通过实时行情获取股票名称

    Args:
        stock_code: A 股代码

    Returns:
        股票名称，获取失败返回 None
    """
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == stock_code]
        if not row.empty:
            return str(row.iloc[0]["名称"])
    except Exception as exc:
        logger.warning("获取 %s 名称失败: %s", stock_code, exc)
    return None
