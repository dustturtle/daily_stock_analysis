# -*- coding: utf-8 -*-
"""Tests for DSA_MVP.llm_analyzer

LLM 调用通过 mock 替代，确保 CI 无需 API Key 即可运行。
"""

import json
from unittest.mock import MagicMock, patch

from DSA_MVP.config import Config
from DSA_MVP.llm_analyzer import analyze, _DEFAULT_RESULT


_SAMPLE_TECH = {
    "price": 1850.0,
    "change_pct": 1.5,
    "trend": "多头排列",
    "ma5": 1840.0,
    "ma10": 1820.0,
    "ma20": 1800.0,
    "volume_status": "放量",
}

_SAMPLE_LLM_RESPONSE = {
    "sentiment_score": 75,
    "trend_prediction": "看多",
    "operation_advice": "买入",
    "analysis_summary": "技术面多头排列，量能配合，短期趋势向好。",
    "risk_warning": "注意获利回吐风险。",
}


class TestAnalyze:
    """llm_analyzer.analyze 测试"""

    def test_no_api_key_returns_default(self):
        """未配置 API Key 应返回默认结果"""
        config = Config(llm_api_key="")
        result = analyze("贵州茅台", _SAMPLE_TECH, config)
        assert result == _DEFAULT_RESULT

    @patch("DSA_MVP.llm_analyzer.OpenAI")
    def test_successful_analysis(self, mock_openai_cls):
        """正常调用应返回 LLM 解析结果"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = json.dumps(_SAMPLE_LLM_RESPONSE)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        config = Config(llm_api_key="sk-test", llm_model="test-model")
        result = analyze("贵州茅台", _SAMPLE_TECH, config)

        assert result["sentiment_score"] == 75
        assert result["trend_prediction"] == "看多"
        assert result["operation_advice"] == "买入"

    @patch("DSA_MVP.llm_analyzer.OpenAI")
    def test_markdown_wrapped_json(self, mock_openai_cls):
        """LLM 返回 markdown 代码块包裹的 JSON 也能正确解析"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        wrapped = f"```json\n{json.dumps(_SAMPLE_LLM_RESPONSE)}\n```"
        mock_message = MagicMock()
        mock_message.content = wrapped
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        config = Config(llm_api_key="sk-test")
        result = analyze("贵州茅台", _SAMPLE_TECH, config)
        assert result["sentiment_score"] == 75

    @patch("DSA_MVP.llm_analyzer.OpenAI")
    def test_api_error_returns_default(self, mock_openai_cls):
        """API 调用异常应返回默认结果"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("超时")

        config = Config(llm_api_key="sk-test")
        result = analyze("贵州茅台", _SAMPLE_TECH, config)
        assert result == _DEFAULT_RESULT

    @patch("DSA_MVP.llm_analyzer.OpenAI")
    def test_missing_fields_filled_with_defaults(self, mock_openai_cls):
        """LLM 返回缺少必要字段时应补充默认值"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        partial = {"analysis_summary": "只有摘要"}
        mock_message = MagicMock()
        mock_message.content = json.dumps(partial)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        config = Config(llm_api_key="sk-test")
        result = analyze("贵州茅台", _SAMPLE_TECH, config)
        assert result["sentiment_score"] == _DEFAULT_RESULT["sentiment_score"]
        assert result["analysis_summary"] == "只有摘要"
