from __future__ import annotations

import os

from openai import OpenAI

from analysis.stock_summary import (
    StockSummary,
    format_analyst_summary,
    format_capital_flow_table,
    format_summary_value,
)


def _fallback_report(summary: StockSummary) -> str:
    values = format_summary_value(summary)
    metrics = "\n".join(f"- **{key}**：{value}" for key, value in values.items())
    capital_flow_table = format_capital_flow_table(summary)
    analyst_summary = format_analyst_summary(summary)
    missing_fields = [key for key, value in values.items() if value in {"暂无数据", "暂无评级数据", "Unknown"}]
    data_quality = ""
    if missing_fields:
        data_quality = (
            "\n## 数据完整度提醒\n\n"
            f"本次以下字段没有从公开免费数据源稳定读到：{', '.join(missing_fields)}。\n\n"
            "常见原因是 Yahoo Finance / 免费行情源限流、该市场不公开该字段，或分析师评级需要更专业的数据源。"
            "这些字段为空时，报告会更依赖价格走势、成交量估算和公开材料关键词。"
        )

    opportunity = "值得继续观察"
    if summary.recent_trend == "偏强" and summary.revenue_growth is not None and summary.revenue_growth > 0:
        opportunity = "短期市场表现和收入增长都比较积极"
    elif summary.recent_trend == "偏弱":
        opportunity = "近期股价表现偏弱，需要更谨慎"

    return f"""# {summary.company_name}（{summary.symbol}）基础分析报告

## 核心数据

{metrics}

## 初步判断

{summary.company_name} 属于 {summary.sector} 板块，细分行业是 {summary.industry}。从最近六个月股价表现看，走势为 **{summary.recent_trend}**，基础风险等级为 **{summary.risk_level}**。

整体来看，这只股票目前 **{opportunity}**。资金流向估算显示 **{summary.capital_flow.signal}**，分析师共识为 **{summary.analyst.consensus}**。
{data_quality}

## 资金流向估算

{capital_flow_table}

说明：这里的“大额成交日”是用成交量明显高于近 20 日平均成交量的交易日近似估算，不等于真实逐笔大单数据。

## 分析师评价

{analyst_summary}

## 下一步需要补充

- 读取最近 10-K / 10-Q 财报，确认收入增长质量和现金流情况
- 分析最近 earnings call，判断管理层语气是否变乐观
- 和同行公司比较估值、增长和利润率
- 观察行业新闻和关键词热度是否持续上升

> 这份报告是学习和研究用途，不构成投资建议。
"""


def _build_prompt(summary: StockSummary) -> str:
    values = format_summary_value(summary)
    metrics = "\n".join(f"{key}: {value}" for key, value in values.items())
    capital_flow_table = format_capital_flow_table(summary)
    analyst_summary = format_analyst_summary(summary)
    return f"""请根据以下股票基础数据，写一份中文股票分析报告。

要求：
- 语言清楚，适合金融初学者阅读
- 不要承诺未来收益
- 明确说明这不是投资建议
- 包含：公司概况、股价趋势、估值和增长、资金流向估算、分析师评价、主要风险、下一步应该看什么
- 不要编造没有给出的数据
- 说明资金流向是用价格和成交量估算，不是真实逐笔大单数据

数据：
{metrics}

资金流向估算：
{capital_flow_table}

分析师评价：
{analyst_summary}
"""


def build_report(summary: StockSummary) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_report(summary)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "你是一个谨慎、清晰的中文金融研究助手。"},
            {"role": "user", "content": _build_prompt(summary)},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or _fallback_report(summary)
