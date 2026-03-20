# -*- coding: utf-8 -*-
"""Tests for DSA_MVP.technical_analyzer"""

import numpy as np
import pandas as pd
import pytest

from DSA_MVP.technical_analyzer import analyze


def _make_df(
    prices: list,
    volumes: list | None = None,
) -> pd.DataFrame:
    """构造测试用 DataFrame"""
    n = len(prices)
    if volumes is None:
        volumes = [10000] * n
    return pd.DataFrame(
        {
            "close": prices,
            "volume": volumes,
            "open": prices,
            "high": [p + 1 for p in prices],
            "low": [p - 1 for p in prices],
        }
    )


class TestAnalyze:
    """technical_analyzer.analyze 测试"""

    def test_bull_trend(self):
        """单调上升数据应判定为多头排列"""
        prices = [100.0 + i for i in range(30)]
        df = _make_df(prices)
        result = analyze(df)
        assert result["trend"] == "多头排列"

    def test_bear_trend(self):
        """单调下降数据应判定为空头排列"""
        prices = [130.0 - i for i in range(30)]
        df = _make_df(prices)
        result = analyze(df)
        assert result["trend"] == "空头排列"

    def test_consolidation(self):
        """横盘波动数据应判定为盘整"""
        # MA5 > MA10 但 MA10 < MA20 → 盘整
        # 先跌后涨，使 MA20 > MA10，但短期 MA5 > MA10
        prices = [110.0 - i * 0.5 for i in range(20)] + [100.0 + i * 0.3 for i in range(10)]
        df = _make_df(prices)
        result = analyze(df)
        assert result["trend"] == "盘整"

    def test_ma_values(self):
        """均线值应正确计算"""
        prices = [100.0 + i for i in range(30)]
        df = _make_df(prices)
        result = analyze(df)
        # MA5 应接近最近 5 天的均值
        expected_ma5 = np.mean(prices[-5:])
        assert abs(result["ma5"] - expected_ma5) < 0.01

    def test_volume_heavy(self):
        """放量应正确判定"""
        # 最近 5 天：4 天正常量 + 最后一天大幅放量
        # rolling(5).mean 会是 (10000*4+30000)/5 = 14000, 30000 > 14000*1.3 = 18200 → 放量
        volumes = [10000] * 29 + [30000]
        prices = [100.0 + i for i in range(30)]
        df = _make_df(prices, volumes)
        result = analyze(df)
        assert result["volume_status"] == "放量"

    def test_volume_shrink(self):
        """缩量应正确判定"""
        # 最近 5 天：4 天正常量 + 最后一天大幅缩量
        # rolling(5).mean 会是 (10000*4+2000)/5 = 8400, 2000 < 8400*0.7 = 5880 → 缩量
        volumes = [10000] * 29 + [2000]
        prices = [100.0 + i for i in range(30)]
        df = _make_df(prices, volumes)
        result = analyze(df)
        assert result["volume_status"] == "缩量"

    def test_volume_normal(self):
        """正常量能应正确判定"""
        volumes = [10000] * 30
        prices = [100.0 + i for i in range(30)]
        df = _make_df(prices, volumes)
        result = analyze(df)
        assert result["volume_status"] == "正常"

    def test_change_pct(self):
        """涨跌幅应正确计算"""
        prices = [100.0] * 29 + [102.0]
        df = _make_df(prices)
        result = analyze(df)
        assert result["change_pct"] == 2.0

    def test_insufficient_data(self):
        """不足 20 行应抛出 ValueError"""
        prices = [100.0] * 10
        df = _make_df(prices)
        with pytest.raises(ValueError, match="数据不足"):
            analyze(df)

    def test_output_structure(self):
        """输出应包含所有必要字段"""
        prices = [100.0 + i for i in range(30)]
        df = _make_df(prices)
        result = analyze(df)
        expected_keys = {"trend", "ma5", "ma10", "ma20", "volume_status", "price", "change_pct"}
        assert set(result.keys()) == expected_keys

    def test_price_field(self):
        """price 应为最新收盘价"""
        prices = [100.0 + i for i in range(30)]
        df = _make_df(prices)
        result = analyze(df)
        assert result["price"] == round(prices[-1], 2)
