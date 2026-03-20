# -*- coding: utf-8 -*-
"""Tests for DSA_MVP.storage"""

import os
import sqlite3

import pytest

from DSA_MVP.storage import init_db, query_all_latest, query_latest, save_analysis


_SAMPLE_TECH = {
    "price": 1850.0,
    "change_pct": 1.5,
    "trend": "多头排列",
}

_SAMPLE_ANALYSIS = {
    "sentiment_score": 75,
    "trend_prediction": "看多",
    "operation_advice": "买入",
    "analysis_summary": "看好后市。",
    "risk_warning": "注意风险。",
}


@pytest.fixture
def db_path(tmp_path):
    """临时数据库路径"""
    return str(tmp_path / "test_analysis.db")


class TestInitDb:
    """init_db 测试"""

    def test_creates_db_file(self, db_path):
        """应创建数据库文件"""
        init_db(db_path)
        assert os.path.exists(db_path)

    def test_creates_parent_dir(self, tmp_path):
        """应自动创建父目录"""
        nested = str(tmp_path / "nested" / "dir" / "test.db")
        init_db(nested)
        assert os.path.exists(nested)

    def test_idempotent(self, db_path):
        """重复调用不应报错"""
        init_db(db_path)
        init_db(db_path)


class TestSaveAnalysis:
    """save_analysis 测试"""

    def test_save_and_query(self, db_path):
        """保存后应能查询到记录"""
        save_analysis(db_path, "600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        records = query_latest(db_path, "600519")
        assert len(records) == 1
        assert records[0]["stock_code"] == "600519"
        assert records[0]["stock_name"] == "贵州茅台"
        assert records[0]["sentiment_score"] == 75

    def test_save_multiple(self, db_path):
        """多次保存应产生多条记录"""
        for i in range(3):
            analysis = dict(_SAMPLE_ANALYSIS, sentiment_score=70 + i)
            save_analysis(db_path, "600519", "贵州茅台", _SAMPLE_TECH, analysis)
        records = query_latest(db_path, "600519", limit=10)
        assert len(records) == 3

    def test_save_different_stocks(self, db_path):
        """不同股票应独立存储"""
        save_analysis(db_path, "600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        save_analysis(db_path, "300750", "宁德时代", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        records_moutai = query_latest(db_path, "600519")
        records_catl = query_latest(db_path, "300750")
        assert len(records_moutai) == 1
        assert len(records_catl) == 1

    def test_stores_technical_data(self, db_path):
        """应存储技术指标数据"""
        save_analysis(db_path, "600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        records = query_latest(db_path, "600519")
        assert records[0]["price"] == 1850.0
        assert records[0]["change_pct"] == 1.5
        assert records[0]["trend"] == "多头排列"


class TestQuery:
    """查询功能测试"""

    def test_query_latest_limit(self, db_path):
        """limit 参数应生效"""
        for i in range(10):
            save_analysis(db_path, "600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        records = query_latest(db_path, "600519", limit=3)
        assert len(records) == 3

    def test_query_nonexistent_stock(self, db_path):
        """查询不存在的股票应返回空列表"""
        init_db(db_path)
        records = query_latest(db_path, "999999")
        assert records == []

    def test_query_nonexistent_db(self, tmp_path):
        """查询不存在的数据库应返回空列表"""
        records = query_latest(str(tmp_path / "nonexist.db"), "600519")
        assert records == []

    def test_query_all_latest(self, db_path):
        """query_all_latest 应返回所有股票的记录"""
        save_analysis(db_path, "600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        save_analysis(db_path, "300750", "宁德时代", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        records = query_all_latest(db_path, limit=10)
        assert len(records) == 2

    def test_query_all_latest_ordered_by_time(self, db_path):
        """query_all_latest 应按时间倒序"""

        save_analysis(db_path, "600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        # 手动插入第二条并设置更晚的时间戳，避免同一秒内插入顺序不确定
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO analysis "
            "(stock_code, stock_name, sentiment_score, trend_prediction, "
            "operation_advice, analysis_summary, risk_warning, price, change_pct, trend, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+1 second'))",
            (
                "300750", "宁德时代", 80, "看多", "买入", "摘要", "风险",
                200.0, 2.0, "多头排列",
            ),
        )
        conn.commit()
        conn.close()

        records = query_all_latest(db_path, limit=10)
        # 最后插入的（更晚时间戳）应排在前面
        assert records[0]["stock_code"] == "300750"
