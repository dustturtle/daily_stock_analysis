# -*- coding: utf-8 -*-
"""
DSA_MVP — LLM 分析模块

使用兼容 OpenAI 协议的 LLM API 对股票技术指标进行智能分析。
"""

import json
import logging
from typing import Any, Dict

from openai import OpenAI

from DSA_MVP.config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
你是一位专业的股票分析师。请根据提供的技术指标数据，给出分析报告。

请严格以 JSON 格式输出，包含以下字段：
- sentiment_score: 综合评分(0-100 的整数)
- trend_prediction: 趋势预测(强烈看多/看多/震荡/看空/强烈看空)
- operation_advice: 操作建议(买入/持有/卖出/观望)
- analysis_summary: 综合分析(200字以内)
- risk_warning: 风险提示(100字以内)

仅输出 JSON，不要输出任何其他内容。\
"""

# 当 LLM 调用失败时使用的默认结果
_DEFAULT_RESULT: Dict[str, Any] = {
    "sentiment_score": 50,
    "trend_prediction": "震荡",
    "operation_advice": "观望",
    "analysis_summary": "LLM 分析不可用，请参考技术指标自行判断。",
    "risk_warning": "当前分析基于默认结果，仅供参考。",
}


def analyze(
    stock_name: str,
    technical_data: Dict[str, Any],
    config: Config,
) -> Dict[str, Any]:
    """调用 LLM 进行股票分析

    Args:
        stock_name: 股票名称
        technical_data: 技术指标字典（来自 technical_analyzer.analyze）
        config: 配置实例

    Returns:
        分析结果字典（sentiment_score, trend_prediction, operation_advice, ...）
    """
    if not config.llm_api_key:
        logger.warning("LLM_API_KEY 未配置，返回默认分析结果")
        return dict(_DEFAULT_RESULT)

    user_message = (
        f"股票：{stock_name}\n"
        f"当前价格：{technical_data['price']}\n"
        f"涨跌幅：{technical_data['change_pct']}%\n"
        f"趋势状态：{technical_data['trend']}\n"
        f"MA5={technical_data['ma5']}, "
        f"MA10={technical_data['ma10']}, "
        f"MA20={technical_data['ma20']}\n"
        f"量能状态：{technical_data['volume_status']}"
    )

    try:
        client = OpenAI(api_key=config.llm_api_key, base_url=config.llm_base_url)
        response = client.chat.completions.create(
            model=config.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content or ""
        # 尝试提取 JSON（处理可能的 markdown 代码块包裹）
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if len(lines) >= 3:
                content = "\n".join(lines[1:-1])
            else:
                # Single-line code block like ```json {...}```
                content = content.strip("`").strip()
                if content.startswith("json"):
                    content = content[4:].strip()
        result = json.loads(content)
        # 校验必要字段
        for key in ("sentiment_score", "trend_prediction", "operation_advice"):
            if key not in result:
                logger.warning("LLM 返回缺少字段 %s，使用默认值", key)
                result[key] = _DEFAULT_RESULT[key]
        return result
    except Exception as exc:
        logger.error("LLM 分析失败: %s", exc)
        return dict(_DEFAULT_RESULT)
