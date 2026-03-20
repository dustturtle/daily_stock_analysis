# -*- coding: utf-8 -*-
"""
DSA_MVP — CLI 主入口

将数据获取、技术分析、LLM 分析、报告生成、持久化串联为完整流程。
"""

import argparse
import logging
import sys
from typing import List

from DSA_MVP.config import Config, load_config
from DSA_MVP.data_fetcher import get_stock_data, get_stock_name
from DSA_MVP.llm_analyzer import analyze as llm_analyze
from DSA_MVP.report import format_report, print_report
from DSA_MVP.storage import init_db, save_analysis
from DSA_MVP.technical_analyzer import analyze as tech_analyze


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="DSA MVP — A 股智能分析（最小化版本）",
    )
    parser.add_argument(
        "--stocks",
        type=str,
        default=None,
        help="要分析的股票代码，逗号分隔（覆盖 .env 中的 STOCK_LIST）",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=60,
        help="获取最近多少个交易日的数据（默认 60）",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用 DEBUG 日志",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅获取数据和技术分析，跳过 LLM 调用",
    )
    return parser.parse_args()


def run_analysis(
    stock_codes: List[str],
    config: Config,
    days: int = 60,
    dry_run: bool = False,
) -> int:
    """执行分析主流程

    Args:
        stock_codes: 股票代码列表
        config: 配置实例
        days: 获取最近多少交易日数据
        dry_run: 是否跳过 LLM 调用

    Returns:
        成功分析的股票数量
    """
    init_db(config.db_path)
    success_count = 0

    for stock_code in stock_codes:
        print(f"\n{'─' * 60}")
        print(f"正在分析 {stock_code} ...")
        print(f"{'─' * 60}")

        try:
            # 1. 获取股票名称
            stock_name = get_stock_name(stock_code) or stock_code

            # 2. 获取行情数据
            df = get_stock_data(stock_code, days=days)
            logging.info("获取到 %d 条数据", len(df))

            # 3. 技术分析
            tech_result = tech_analyze(df)
            logging.info("技术分析完成: %s", tech_result)

            # 4. LLM 分析
            if dry_run:
                analysis = {
                    "sentiment_score": 50,
                    "trend_prediction": "未分析（dry-run 模式）",
                    "operation_advice": "未分析（dry-run 模式）",
                    "analysis_summary": "dry-run 模式下跳过 LLM 分析。",
                    "risk_warning": "请配置 LLM_API_KEY 后运行完整分析。",
                }
            else:
                analysis = llm_analyze(stock_name, tech_result, config)

            # 5. 生成报告并打印
            report = format_report(stock_code, stock_name, tech_result, analysis)
            print_report(report)

            # 6. 持久化
            save_analysis(
                config.db_path, stock_code, stock_name, tech_result, analysis
            )

            success_count += 1

        except Exception as exc:
            logging.error("分析 %s 失败: %s", stock_code, exc)
            print(f"❌ 分析 {stock_code} 失败: {exc}")

    return success_count


def main() -> None:
    """CLI 入口"""
    args = parse_arguments()

    # 配置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 加载配置
    config = load_config()

    # 确定要分析的股票
    if args.stocks:
        stock_codes = [s.strip() for s in args.stocks.split(",") if s.strip()]
    else:
        stock_codes = config.stock_list

    if not stock_codes:
        print("❌ 未指定股票代码，请设置 STOCK_LIST 或使用 --stocks 参数")
        sys.exit(1)

    print(f"📊 DSA MVP — 开始分析 {len(stock_codes)} 只股票")
    print(f"   股票列表: {', '.join(stock_codes)}")
    if args.dry_run:
        print("   模式: dry-run（跳过 LLM 调用）")

    count = run_analysis(
        stock_codes, config, days=args.days, dry_run=args.dry_run
    )

    print(f"\n✅ 分析完成: {count}/{len(stock_codes)} 只股票成功")


if __name__ == "__main__":
    main()
