from __future__ import annotations

import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from analysis.i18n import Language, is_missing_display, label
from analysis.stock_summary import (
    StockSummary,
    format_analyst_summary,
    format_capital_flow_table,
    format_data_quality_report,
    format_summary_value,
)


def _fallback_report(summary: StockSummary, language: Language = "zh") -> str:
    values = format_summary_value(summary, language)
    separator = ": " if language == "en" else "："
    metrics = "\n".join(f"- **{key}**{separator}{value}" for key, value in values.items())
    capital_flow_table = format_capital_flow_table(summary, language)
    analyst_summary = format_analyst_summary(summary, language)
    data_quality = format_data_quality_report(summary, language)
    missing_fields = [key for key, value in values.items() if is_missing_display(value)]
    data_quality_note = ""
    if missing_fields:
        if language == "en":
            data_quality_note = (
                "\n## Data Completeness Note\n\n"
                f"The following fields were not reliably available from public/free sources: {', '.join(missing_fields)}.\n\n"
                "Common reasons include Yahoo Finance or free-source throttling, limited disclosure for the market, or analyst data requiring a specialist data provider."
            )
        else:
            data_quality_note = (
                "\n## 数据完整度提醒\n\n"
                f"本次以下字段没有从公开免费数据源稳定读到：{', '.join(missing_fields)}。\n\n"
                "常见原因是 Yahoo Finance / 免费行情源限流、该市场不公开该字段，或分析师评级需要更专业的数据源。"
                "这些字段为空时，报告会更依赖价格走势、成交量估算和公开材料关键词。"
            )

    opportunity = "值得继续观察" if language == "zh" else "worth monitoring"
    if summary.recent_trend == "偏强" and summary.revenue_growth is not None and summary.revenue_growth > 0:
        opportunity = "showing positive short-term market performance and revenue growth" if language == "en" else "短期市场表现和收入增长都比较积极"
    elif summary.recent_trend == "偏弱":
        opportunity = "showing weak recent price action, so extra caution is needed" if language == "en" else "近期股价表现偏弱，需要更谨慎"

    if language == "en":
        return f"""# {summary.company_name} ({summary.symbol}) Basic Analysis Report

## Key Data

{metrics}

## Initial View

{summary.company_name} is in the {summary.sector} sector, with a more specific industry classification of {summary.industry}. Over the last six months, the stock trend is **{label(summary.recent_trend, language)}**, and the base risk level is **{label(summary.risk_level, language)}**.

Overall, this stock is **{opportunity}**. The dollar-volume direction estimate is **{label(summary.capital_flow.signal, language)}**, and analyst consensus is **{label(summary.analyst.consensus, language)}**.
{data_quality_note}
{data_quality}

## Dollar-Volume Direction Estimate

{capital_flow_table}

Note: high-volume days are approximated using trading days where volume is well above the 20-day average. This is not true tick-level large-order or small-order flow.

## Analyst View

{analyst_summary}

## What To Check Next

- Read the latest 10-K / 10-Q to verify revenue quality and cash flow
- Review the latest earnings call to judge whether management tone is improving
- Compare valuation, growth, and margins with peers
- Watch whether industry news and keyword momentum continue

> This report is for learning and research only. It is not investment advice.
"""

    return f"""# {summary.company_name}（{summary.symbol}）基础分析报告

## 核心数据

{metrics}

## 初步判断

{summary.company_name} 属于 {summary.sector} 板块，细分行业是 {summary.industry}。从最近六个月股价表现看，走势为 **{label(summary.recent_trend, language)}**，基础风险等级为 **{label(summary.risk_level, language)}**。

整体来看，这只股票目前 **{opportunity}**。成交额方向估算显示 **{label(summary.capital_flow.signal, language)}**，分析师共识为 **{label(summary.analyst.consensus, language)}**。
{data_quality_note}
{data_quality}

## 成交额方向估算

{capital_flow_table}

说明：这里的“大额成交日”是用成交量明显高于近 20 日平均成交量的交易日近似估算，不等于真实逐笔大单或小单资金流。

## 分析师评价

{analyst_summary}

## 下一步需要补充

- 读取最近 10-K / 10-Q 财报，确认收入增长质量和现金流情况
- 分析最近 earnings call，判断管理层语气是否变乐观
- 和同行公司比较估值、增长和利润率
- 观察行业新闻和关键词热度是否持续上升

> 这份报告是学习和研究用途，不构成投资建议。
"""


def _build_prompt(summary: StockSummary, language: Language = "zh") -> str:
    values = format_summary_value(summary, language)
    metrics = "\n".join(f"{key}: {value}" for key, value in values.items())
    capital_flow_table = format_capital_flow_table(summary, language)
    analyst_summary = format_analyst_summary(summary, language)
    data_quality = format_data_quality_report(summary, language)
    if language == "en":
        return f"""Write an English stock analysis report based only on the data below.

Requirements:
- Clear language for a beginner investor
- Do not promise future returns
- Explicitly state this is not investment advice
- Include company overview, price trend, valuation and growth, dollar-volume direction estimate, data quality, analyst view, main risks, and what to check next
- Do not invent missing data
- Explain that dollar-volume direction is estimated from price and volume, not true tick-level order flow

Data:
{metrics}

Dollar-volume direction estimate:
{capital_flow_table}

Data quality:
{data_quality}

Analyst view:
{analyst_summary}
"""
    return f"""请根据以下股票基础数据，写一份中文股票分析报告。

要求：
- 语言清楚，适合金融初学者阅读
- 不要承诺未来收益
- 明确说明这不是投资建议
- 包含：公司概况、股价趋势、估值和增长、成交额方向估算、数据质量、分析师评价、主要风险、下一步应该看什么
- 不要编造没有给出的数据
- 说明成交额方向估算是用价格和成交量估算，不是真实逐笔大单数据

数据：
{metrics}

成交额方向估算：
{capital_flow_table}

数据质量：
{data_quality}

分析师评价：
{analyst_summary}
"""


def build_report(summary: StockSummary, language: Language = "zh") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return _fallback_report(summary, language)

    client = OpenAI(api_key=api_key)
    system_prompt = (
        "You are a careful, clear financial research assistant. Write in English."
        if language == "en"
        else "你是一个谨慎、清晰的中文金融研究助手。"
    )
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": _build_prompt(summary, language)},
        ],
        temperature=0.3,
    )
    report = response.choices[0].message.content or _fallback_report(summary, language)
    quality_heading = "## Data Quality" if language == "en" else "## 数据质量"
    if quality_heading not in report:
        report += "\n\n" + format_data_quality_report(summary, language)
    return report
