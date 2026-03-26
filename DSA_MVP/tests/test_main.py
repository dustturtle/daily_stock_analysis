# -*- coding: utf-8 -*-
"""Tests for DSA_MVP.main — CLI 集成测试

所有外部调用通过 mock 替代。
"""

from unittest.mock import patch

import pandas as pd

from DSA_MVP.config import Config
from DSA_MVP.main import run_analysis


def _make_hist_df(rows: int = 30) -> pd.DataFrame:
    """构造模拟的标准化 DataFrame"""
    return pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=rows, freq="B"),
            "open": [100.0 + i * 0.1 for i in range(rows)],
            "close": [100.5 + i * 0.1 for i in range(rows)],
            "high": [101.0 + i * 0.1 for i in range(rows)],
            "low": [99.5 + i * 0.1 for i in range(rows)],
            "volume": [10000 + i * 100 for i in range(rows)],
            "amount": [1e8] * rows,
        }
    )


class TestRunAnalysis:
    """run_analysis 集成测试"""

    @patch("DSA_MVP.main.get_stock_name")
    @patch("DSA_MVP.main.get_stock_data")
    def test_dry_run_no_llm(self, mock_data, mock_name, tmp_path):
        """dry-run 模式不应调用 LLM"""
        mock_data.return_value = _make_hist_df(30)
        mock_name.return_value = "贵州茅台"

        config = Config(
            stock_list=["600519"],
            db_path=str(tmp_path / "test.db"),
        )
        count = run_analysis(["600519"], config, dry_run=True)
        assert count == 1

    @patch("DSA_MVP.main.llm_analyze")
    @patch("DSA_MVP.main.get_stock_name")
    @patch("DSA_MVP.main.get_stock_data")
    def test_full_analysis_flow(self, mock_data, mock_name, mock_llm, tmp_path):
        """完整流程应成功执行"""
        mock_data.return_value = _make_hist_df(30)
        mock_name.return_value = "贵州茅台"
        mock_llm.return_value = {
            "sentiment_score": 70,
            "trend_prediction": "看多",
            "operation_advice": "持有",
            "analysis_summary": "测试摘要",
            "risk_warning": "测试风险",
        }

        config = Config(
            stock_list=["600519"],
            llm_api_key="sk-test",
            db_path=str(tmp_path / "test.db"),
        )
        count = run_analysis(["600519"], config)
        assert count == 1
        mock_llm.assert_called_once()

    @patch("DSA_MVP.main.get_stock_name")
    @patch("DSA_MVP.main.get_stock_data")
    def test_analysis_error_continues(self, mock_data, mock_name, tmp_path):
        """单只股票失败不应影响其他股票"""
        mock_name.return_value = "测试"
        mock_data.side_effect = [
            ValueError("无数据"),  # 第一只失败
            _make_hist_df(30),     # 第二只成功
        ]

        config = Config(
            stock_list=["999999", "600519"],
            db_path=str(tmp_path / "test.db"),
        )
        count = run_analysis(["999999", "600519"], config, dry_run=True)
        assert count == 1  # 只有第二只成功

    @patch("DSA_MVP.main.get_stock_name")
    @patch("DSA_MVP.main.get_stock_data")
    def test_multiple_stocks(self, mock_data, mock_name, tmp_path):
        """应支持分析多只股票"""
        mock_data.return_value = _make_hist_df(30)
        mock_name.return_value = "测试"

        config = Config(
            stock_list=["600519", "300750"],
            db_path=str(tmp_path / "test.db"),
        )
        count = run_analysis(["600519", "300750"], config, dry_run=True)
        assert count == 2
