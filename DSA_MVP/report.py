# -*- coding: utf-8 -*-
"""
DSA_MVP — 报告生成模块

将分析结果格式化为 Markdown 文本并打印到终端。
"""

from typing import Any, Dict


def format_report(
    stock_code: str,
    stock_name: str,
    technical_data: Dict[str, Any],
    analysis: Dict[str, Any],
) -> str:
    """将分析结果格式化为 Markdown 报告

    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        technical_data: 技术指标（price, change_pct, trend, ma5, ma10, ma20, volume_status）
        analysis: LLM 分析结果（sentiment_score, trend_prediction, operation_advice, ...）

    Returns:
        Markdown 格式的报告文本
    """
    score = analysis.get("sentiment_score", 50)
    if score >= 60:
        emoji = "🟢"
    elif score >= 40:
        emoji = "🟡"
    else:
        emoji = "🔴"

    trend_prediction = analysis.get("trend_prediction", "未知")
    operation_advice = analysis.get("operation_advice", "未知")
    analysis_summary = analysis.get("analysis_summary", "暂无分析")
    risk_warning = analysis.get("risk_warning", "投资有风险，入市需谨慎。")

    price = technical_data.get("price", "N/A")
    change_pct = technical_data.get("change_pct", "N/A")
    trend = technical_data.get("trend", "未知")
    ma5 = technical_data.get("ma5", "N/A")
    ma10 = technical_data.get("ma10", "N/A")
    ma20 = technical_data.get("ma20", "N/A")
    volume_status = technical_data.get("volume_status", "未知")

    return (
        f"{'=' * 60}\n"
        f"{emoji} {stock_name}（{stock_code}）分析报告\n"
        f"{'=' * 60}\n"
        f"\n"
        f"综合评分: {score}/100 | 趋势: {trend_prediction} | 建议: {operation_advice}\n"
        f"\n"
        f"--- 技术面 ---\n"
        f"当前价格: {price}  涨跌幅: {change_pct}%\n"
        f"均线状态: {trend}\n"
        f"  MA5={ma5}  MA10={ma10}  MA20={ma20}\n"
        f"量能状态: {volume_status}\n"
        f"\n"
        f"--- 分析摘要 ---\n"
        f"{analysis_summary}\n"
        f"\n"
        f"--- ⚠️ 风险提示 ---\n"
        f"{risk_warning}\n"
        f"{'=' * 60}\n"
    )


def print_report(report: str) -> None:
    """将报告打印到终端（通知推送）

    Args:
        report: Markdown 格式的报告文本
    """
    print(report)
