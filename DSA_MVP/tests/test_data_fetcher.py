# -*- coding: utf-8 -*-
"""Tests for DSA_MVP.data_fetcher

所有网络调用通过 mock 替代，确保 CI 无需联网即可运行。
"""

from unittest.mock import patch

import pandas as pd
import pytest

from DSA_MVP.data_fetcher import get_stock_data, get_stock_name


def _make_hist_df(rows: int = 60) -> pd.DataFrame:
    """构造模拟的 akshare 日 K 线数据"""
    data = {
        "日期": pd.date_range("2025-01-01", periods=rows, freq="B"),
        "开盘": [100.0 + i * 0.1 for i in range(rows)],
        "收盘": [100.5 + i * 0.1 for i in range(rows)],
        "最高": [101.0 + i * 0.1 for i in range(rows)],
        "最低": [99.5 + i * 0.1 for i in range(rows)],
        "成交量": [10000 + i * 100 for i in range(rows)],
        "成交额": [1e8 + i * 1e6 for i in range(rows)],
        "振幅": [1.5] * rows,
        "涨跌幅": [0.1 * i for i in range(rows)],
        "涨跌额": [0.1] * rows,
        "换手率": [1.0] * rows,
    }
    return pd.DataFrame(data)


class TestGetStockData:
    """get_stock_data 测试"""

    @patch("DSA_MVP.data_fetcher.ak.stock_zh_a_hist")
    def test_returns_standardized_columns(self, mock_hist):
        """返回的 DataFrame 应有标准化英文列名"""
        mock_hist.return_value = _make_hist_df(60)
        df = get_stock_data("600519", days=30)
        assert "close" in df.columns
        assert "volume" in df.columns
        assert "date" in df.columns
        assert len(df) == 30

    @patch("DSA_MVP.data_fetcher.ak.stock_zh_a_hist")
    def test_respects_days_param(self, mock_hist):
        """应只返回最近 N 天的数据"""
        mock_hist.return_value = _make_hist_df(100)
        df = get_stock_data("600519", days=20)
        assert len(df) == 20

    @patch("DSA_MVP.data_fetcher.ak.stock_zh_a_hist")
    def test_raises_on_empty_data(self, mock_hist):
        """空数据应抛出 ValueError"""
        mock_hist.return_value = pd.DataFrame()
        with pytest.raises(ValueError, match="无数据"):
            get_stock_data("999999")

    @patch("DSA_MVP.data_fetcher.ak.stock_zh_a_hist")
    def test_raises_on_api_error(self, mock_hist):
        """API 异常应抛出 ValueError"""
        mock_hist.side_effect = Exception("网络超时")
        with pytest.raises(ValueError, match="获取.*失败"):
            get_stock_data("600519")


class TestGetStockName:
    """get_stock_name 测试"""

    @patch("DSA_MVP.data_fetcher.ak.stock_zh_a_spot_em")
    def test_returns_name(self, mock_spot):
        """应返回正确的股票名称"""
        mock_spot.return_value = pd.DataFrame(
            {"代码": ["600519"], "名称": ["贵州茅台"]}
        )
        assert get_stock_name("600519") == "贵州茅台"

    @patch("DSA_MVP.data_fetcher.ak.stock_zh_a_spot_em")
    def test_returns_none_on_not_found(self, mock_spot):
        """找不到的代码应返回 None"""
        mock_spot.return_value = pd.DataFrame({"代码": [], "名称": []})
        assert get_stock_name("999999") is None

    @patch("DSA_MVP.data_fetcher.ak.stock_zh_a_spot_em")
    def test_returns_none_on_error(self, mock_spot):
        """API 异常应返回 None"""
        mock_spot.side_effect = Exception("超时")
        assert get_stock_name("600519") is None
