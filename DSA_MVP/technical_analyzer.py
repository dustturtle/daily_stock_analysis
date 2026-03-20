# -*- coding: utf-8 -*-
"""
DSA_MVP — 技术分析模块

计算均线（MA5/MA10/MA20）和量能状态，输出结构化技术指标。
"""

import logging
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    """计算技术指标

    Args:
        df: 包含 close, volume 列的日 K 线 DataFrame（至少 20 行）

    Returns:
        技术指标字典:
            - trend: 趋势状态（多头排列 / 空头排列 / 盘整）
            - ma5, ma10, ma20: 均线值
            - volume_status: 量能状态（放量 / 缩量 / 正常）
            - price: 最新收盘价
            - change_pct: 涨跌幅(%)

    Raises:
        ValueError: 数据不足以计算指标
    """
    if len(df) < 20:
        raise ValueError(f"数据不足：需要至少 20 行，实际 {len(df)} 行")

    df = df.copy()

    # 计算均线
    df["ma5"] = df["close"].rolling(5).mean()
    df["ma10"] = df["close"].rolling(10).mean()
    df["ma20"] = df["close"].rolling(20).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # 趋势判断
    ma5 = latest["ma5"]
    ma10 = latest["ma10"]
    ma20 = latest["ma20"]

    if ma5 > ma10 > ma20:
        trend = "多头排列"
    elif ma5 < ma10 < ma20:
        trend = "空头排列"
    else:
        trend = "盘整"

    # 量能判断
    vol_avg = df["volume"].rolling(5).mean().iloc[-1]
    current_vol = latest["volume"]
    if vol_avg > 0:
        if current_vol > vol_avg * 1.3:
            volume_status = "放量"
        elif current_vol < vol_avg * 0.7:
            volume_status = "缩量"
        else:
            volume_status = "正常"
    else:
        volume_status = "正常"

    # 涨跌幅
    if prev["close"] != 0:
        change_pct = round(
            (latest["close"] - prev["close"]) / prev["close"] * 100, 2
        )
    else:
        logger.warning("前一交易日收盘价为 0，无法计算涨跌幅")
        change_pct = 0.0

    return {
        "trend": trend,
        "ma5": round(float(ma5), 2),
        "ma10": round(float(ma10), 2),
        "ma20": round(float(ma20), 2),
        "volume_status": volume_status,
        "price": round(float(latest["close"]), 2),
        "change_pct": change_pct,
    }
