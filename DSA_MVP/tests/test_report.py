# -*- coding: utf-8 -*-
"""Tests for DSA_MVP.report"""

from DSA_MVP.report import format_report, print_report


_SAMPLE_TECH = {
    "price": 1850.0,
    "change_pct": 1.5,
    "trend": "多头排列",
    "ma5": 1840.0,
    "ma10": 1820.0,
    "ma20": 1800.0,
    "volume_status": "放量",
}

_SAMPLE_ANALYSIS = {
    "sentiment_score": 75,
    "trend_prediction": "看多",
    "operation_advice": "买入",
    "analysis_summary": "技术面多头排列，量能配合良好。",
    "risk_warning": "注意高位回调风险。",
}


class TestFormatReport:
    """format_report 测试"""

    def test_contains_stock_info(self):
        """报告应包含股票代码和名称"""
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        assert "600519" in report
        assert "贵州茅台" in report

    def test_contains_score(self):
        """报告应包含综合评分"""
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        assert "75/100" in report

    def test_contains_advice(self):
        """报告应包含操作建议"""
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        assert "买入" in report

    def test_contains_trend(self):
        """报告应包含趋势预测"""
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        assert "看多" in report

    def test_contains_technical_data(self):
        """报告应包含技术指标"""
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        assert "1850.0" in report
        assert "1.5%" in report
        assert "MA5=1840.0" in report

    def test_contains_analysis_summary(self):
        """报告应包含分析摘要"""
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        assert "技术面多头排列" in report

    def test_contains_risk_warning(self):
        """报告应包含风险提示"""
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        assert "高位回调" in report

    def test_green_emoji_for_high_score(self):
        """高评分应显示绿色 emoji"""
        analysis = dict(_SAMPLE_ANALYSIS, sentiment_score=75)
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, analysis)
        assert "🟢" in report

    def test_yellow_emoji_for_medium_score(self):
        """中评分应显示黄色 emoji"""
        analysis = dict(_SAMPLE_ANALYSIS, sentiment_score=50)
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, analysis)
        assert "🟡" in report

    def test_red_emoji_for_low_score(self):
        """低评分应显示红色 emoji"""
        analysis = dict(_SAMPLE_ANALYSIS, sentiment_score=20)
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, analysis)
        assert "🔴" in report

    def test_handles_missing_fields(self):
        """缺少字段时应使用默认值，不崩溃"""
        report = format_report("600519", "茅台", {}, {})
        assert "600519" in report
        assert "N/A" in report


class TestPrintReport:
    """print_report 测试"""

    def test_prints_to_stdout(self, capsys):
        """应将报告打印到标准输出"""
        report = format_report("600519", "贵州茅台", _SAMPLE_TECH, _SAMPLE_ANALYSIS)
        print_report(report)
        captured = capsys.readouterr()
        assert "贵州茅台" in captured.out
        assert "75/100" in captured.out
