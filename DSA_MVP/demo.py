# -*- coding: utf-8 -*-
"""
DSA_MVP — 演示脚本

使用内置样本数据演示完整分析流程，无需网络访问。
也可选择使用 akshare 获取实时数据（需要网络）。
"""

import logging
import os
import sys
import tempfile

import pandas as pd

from DSA_MVP.data_fetcher import get_stock_data, get_stock_name
from DSA_MVP.report import format_report, print_report
from DSA_MVP.storage import init_db, query_latest, save_analysis
from DSA_MVP.technical_analyzer import analyze as tech_analyze


def _sample_kline_data() -> pd.DataFrame:
    """生成样本 K 线数据（模拟 60 个交易日的贵州茅台走势）"""
    import numpy as np

    np.random.seed(42)
    n = 60
    base_price = 1500.0
    # 模拟一个先涨后回调的走势
    trend = (
        [float(i) for i in range(30)]
        + [30 - i * 0.5 for i in range(30)]
    )
    prices_close = [base_price + t * 10 + np.random.randn() * 5 for t in trend]
    dates = pd.bdate_range(end="2026-03-20", periods=n)

    data = {
        "date": dates,
        "open": [p - abs(np.random.randn()) * 3 for p in prices_close],
        "close": prices_close,
        "high": [p + abs(np.random.randn()) * 5 for p in prices_close],
        "low": [p - abs(np.random.randn()) * 5 for p in prices_close],
        "volume": [
            int(50000 + np.random.randn() * 10000 + (5000 if i > 45 else 0))
            for i in range(n)
        ],
        "amount": [1e8 + np.random.randn() * 1e7 for _ in range(n)],
    }
    return pd.DataFrame(data)


def run_demo() -> None:
    """运行演示分析流程"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 使用临时数据库
    db_path = os.path.join(tempfile.gettempdir(), "dsa_mvp_demo.db")

    stock_code = "600519"
    stock_name = "贵州茅台"

    print("=" * 60)
    print("  DSA MVP — 完整流程演示")
    print("=" * 60)

    # 尝试获取真实数据，失败则使用样本数据
    print("\n📡 尝试获取实时行情数据...")
    try:
        df = get_stock_data(stock_code, days=60)
        real_name = get_stock_name(stock_code)
        if real_name:
            stock_name = real_name
        print(f"✅ 成功获取 {stock_name}（{stock_code}）实时数据，共 {len(df)} 条")
        data_source = "akshare 实时数据"
    except Exception as exc:
        print(f"⚠️  实时数据获取失败: {exc}")
        print("📦 使用内置样本数据继续演示...")
        df = _sample_kline_data()
        data_source = "内置样本数据"

    print(f"   数据来源: {data_source}")
    print(f"   数据范围: {len(df)} 个交易日")
    print(f"   最新收盘价: {df.iloc[-1]['close']:.2f}")

    # 技术分析
    print("\n📈 执行技术分析...")
    tech_result = tech_analyze(df)
    print(f"   趋势状态: {tech_result['trend']}")
    print(f"   MA5={tech_result['ma5']}  MA10={tech_result['ma10']}  MA20={tech_result['ma20']}")
    print(f"   量能状态: {tech_result['volume_status']}")
    print(f"   涨跌幅: {tech_result['change_pct']}%")

    # 生成分析结果（dry-run 模式，不调用 LLM）
    print("\n🤖 LLM 分析（dry-run 模式）...")
    analysis = {
        "sentiment_score": 50,
        "trend_prediction": "未分析（dry-run 模式）",
        "operation_advice": "未分析（dry-run 模式）",
        "analysis_summary": "dry-run 模式下跳过 LLM 分析，仅展示技术面指标。",
        "risk_warning": "请配置 LLM_API_KEY 后运行完整分析。",
    }

    # 生成报告
    print("\n📝 生成分析报告...")
    report = format_report(stock_code, stock_name, tech_result, analysis)
    print_report(report)

    # 持久化
    print("💾 保存到数据库...")
    init_db(db_path)
    save_analysis(db_path, stock_code, stock_name, tech_result, analysis)

    # 验证读取
    records = query_latest(db_path, stock_code, limit=1)
    if records:
        r = records[0]
        print(f"   ✅ 数据库验证成功: {r['stock_code']} ({r['stock_name']})")
        print(f"      评分={r['sentiment_score']}, 趋势={r['trend_prediction']}")
    else:
        print("   ❌ 数据库验证失败")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  ✅ DSA MVP 演示完成！所有模块运行正常。")
    print("=" * 60)

    # 清理临时数据库
    try:
        os.remove(db_path)
    except OSError:
        pass


if __name__ == "__main__":
    run_demo()
