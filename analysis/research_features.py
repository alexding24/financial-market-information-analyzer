from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from analysis.business_signals import BusinessSignalSummary
from analysis.i18n import Language, label, missing_value
from analysis.stock_summary import StockSummary


HISTORY_DIR = Path("reports/history")

REASON_LABELS_EN = {
    "近六个月趋势偏强": "six-month trend is strong",
    "近六个月趋势偏弱": "six-month trend is weak",
    "收入增长较快": "revenue growth is strong",
    "收入增长为负": "revenue growth is negative",
    "利润率较高": "profit margin is high",
    "利润率为负": "profit margin is negative",
    "未来市盈率相对可控": "forward P/E is relatively manageable",
    "未来市盈率偏高": "forward P/E is high",
    "成交额方向偏积极": "dollar-volume direction is positive",
    "成交额方向偏谨慎": "dollar-volume direction is cautious",
    "分析师共识偏正面": "analyst consensus is positive",
    "分析师共识偏负面": "analyst consensus is negative",
}


def opportunity_score(summary: StockSummary) -> tuple[int, list[str]]:
    score = 50
    reasons: list[str] = []

    if summary.six_month_return > 0.15:
        score += 12
        reasons.append("近六个月趋势偏强")
    elif summary.six_month_return < -0.15:
        score -= 12
        reasons.append("近六个月趋势偏弱")

    if summary.revenue_growth is not None:
        if summary.revenue_growth > 0.2:
            score += 15
            reasons.append("收入增长较快")
        elif summary.revenue_growth < 0:
            score -= 12
            reasons.append("收入增长为负")

    if summary.profit_margins is not None:
        if summary.profit_margins > 0.2:
            score += 10
            reasons.append("利润率较高")
        elif summary.profit_margins < 0:
            score -= 15
            reasons.append("利润率为负")

    if summary.forward_pe is not None:
        if summary.forward_pe < 25:
            score += 8
            reasons.append("未来市盈率相对可控")
        elif summary.forward_pe > 60:
            score -= 10
            reasons.append("未来市盈率偏高")

    if summary.capital_flow.signal == "成交额方向偏流入":
        score += 8
        reasons.append("成交额方向偏积极")
    elif summary.capital_flow.signal == "成交额方向偏流出":
        score -= 8
        reasons.append("成交额方向偏谨慎")

    if summary.analyst.consensus in {"强烈看多", "看多"}:
        score += 7
        reasons.append("分析师共识偏正面")
    elif summary.analyst.consensus in {"看空", "强烈看空"}:
        score -= 7
        reasons.append("分析师共识偏负面")

    return max(0, min(100, score)), reasons


def format_buy_checklist(summary: StockSummary, language: Language = "zh") -> str:
    score, reasons = opportunity_score(summary)
    positives: list[str] = []
    cautions: list[str] = []
    questions: list[str] = []

    if language == "en":
        if summary.recent_trend == "偏强":
            positives.append("Price trend is strong, suggesting relatively high near-term market recognition.")
        if summary.revenue_growth is not None and summary.revenue_growth > 0:
            positives.append("Revenue is still growing; continue checking the quality of that growth.")
        if summary.capital_flow.signal == "成交额方向偏流入":
            positives.append("The last-three-month dollar-volume direction estimate is positive.")
        if summary.analyst.consensus in {"强烈看多", "看多"}:
            positives.append("Analyst consensus is positive.")

        if summary.forward_pe is not None and summary.forward_pe > 45:
            cautions.append("Valuation is not cheap, so future growth needs to materialize.")
        if summary.risk_level != "较低":
            cautions.append(f"Base risk level is {label(summary.risk_level, language)}.")
        if summary.analyst.target_upside is not None and summary.analyst.target_upside < 0:
            cautions.append("Average target price is below the current price; expectations may be stretched.")

        questions.extend(
            [
                "Did the latest quarter's growth come from real demand or one-off factors?",
                "Did management raise guidance or merely maintain prior expectations?",
                "Do peers offer more attractive growth, valuation, or dollar-volume signals?",
            ]
        )
        translated_reasons = [REASON_LABELS_EN.get(reason, reason) for reason in reasons]
        positives_text = "\n".join(f"- {item}" for item in positives) or "- No obvious bullish points yet."
        cautions_text = "\n".join(f"- {item}" for item in cautions) or "- No obvious extra risk, but financials and industry changes still need review."
        questions_text = "\n".join(f"- {item}" for item in questions)
        reasons_text = ", ".join(translated_reasons) if translated_reasons else "signals are relatively neutral"
        return f"""## Pre-Buy Checklist

**Opportunity score**: {score}/100  
**Reasoning**: {reasons_text}

### Bullish Points

{positives_text}

### Caution Points

{cautions_text}

### Questions To Verify Next

{questions_text}

> This is not buy/sell advice. It is a checklist for organizing research questions.
"""

    if summary.recent_trend == "偏强":
        positives.append("股价趋势偏强，说明市场短期认可度较高。")
    if summary.revenue_growth is not None and summary.revenue_growth > 0:
        positives.append("收入仍在增长，需要继续确认增长质量。")
    if summary.capital_flow.signal == "成交额方向偏流入":
        positives.append("近三个月成交额方向估算偏积极。")
    if summary.analyst.consensus in {"强烈看多", "看多"}:
        positives.append("分析师整体评价偏正面。")

    if summary.forward_pe is not None and summary.forward_pe > 45:
        cautions.append("估值不低，对未来增长兑现要求较高。")
    if summary.risk_level != "较低":
        cautions.append(f"基础风险等级为{summary.risk_level}。")
    if summary.analyst.target_upside is not None and summary.analyst.target_upside < 0:
        cautions.append("平均目标价低于当前价格，需要关注预期是否过热。")

    questions.extend(
        [
            "最近一季增长来自真实需求，还是一次性因素？",
            "管理层 guidance 是否上调，还是只维持原预期？",
            "同行公司的增长、估值和资金流是否更有吸引力？",
        ]
    )

    positives_text = "\n".join(f"- {item}" for item in positives) or "- 暂无明显看多理由。"
    cautions_text = "\n".join(f"- {item}" for item in cautions) or "- 暂无明显额外风险，但仍需看财报和行业变化。"
    questions_text = "\n".join(f"- {item}" for item in questions)
    reasons_text = "、".join(reasons) if reasons else "信号较为中性"

    return f"""## 买前检查清单

**机会评分**：{score}/100  
**评分原因**：{reasons_text}

### 看多理由

{positives_text}

### 需要谨慎的点

{cautions_text}

### 下一步要验证的问题

{questions_text}

> 这不是买卖建议，只是帮助你整理研究问题。
"""


def _history_path(symbol: str) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    return HISTORY_DIR / f"{symbol.upper()}.jsonl"


def load_last_snapshot(symbol: str) -> dict | None:
    path = _history_path(symbol)
    if not path.exists():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def save_snapshot(summary: StockSummary, business: BusinessSignalSummary | None) -> None:
    score, _ = opportunity_score(summary)
    keyword_counts = {}
    if business is not None:
        keyword_counts = {mention.keyword: mention.total for mention in business.keyword_mentions}

    snapshot = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "symbol": summary.symbol,
        "score": score,
        "six_month_return": summary.six_month_return,
        "revenue_growth": summary.revenue_growth,
        "capital_flow": summary.capital_flow.signal,
        "analyst_consensus": summary.analyst.consensus,
        "target_upside": summary.analyst.target_upside,
        "keyword_counts": keyword_counts,
    }
    with _history_path(summary.symbol).open("a", encoding="utf-8") as file:
        file.write(json.dumps(snapshot, ensure_ascii=False) + "\n")


def format_history_comparison(
    summary: StockSummary,
    previous: dict | None,
    business: BusinessSignalSummary | None,
    language: Language = "zh",
) -> str:
    if previous is None:
        if language == "en":
            return "## Historical Report Comparison\n\nThis is the first saved snapshot for this stock. The next report will compare changes automatically.\n"
        return "## 历史报告对比\n\n这是这个股票第一次保存历史快照，下一次生成报告后会自动比较变化。\n"

    score, _ = opportunity_score(summary)
    if language == "en":
        lines = [
            f"- Last saved: {previous.get('timestamp', 'Unknown')}",
            f"- Opportunity score: {previous.get('score', missing_value(language))} -> {score}",
            f"- Dollar-volume direction estimate: {label(previous.get('capital_flow', missing_value(language)), language)} -> {label(summary.capital_flow.signal, language)}",
            f"- Analyst consensus: {label(previous.get('analyst_consensus', missing_value(language)), language)} -> {label(summary.analyst.consensus, language)}",
        ]
    else:
        lines = [
            f"- 上次保存时间：{previous.get('timestamp', '未知')}",
            f"- 机会评分变化：{previous.get('score', '暂无')} -> {score}",
            f"- 成交额方向估算变化：{previous.get('capital_flow', '暂无')} -> {summary.capital_flow.signal}",
            f"- 分析师共识变化：{previous.get('analyst_consensus', '暂无')} -> {summary.analyst.consensus}",
        ]

    if business is not None:
        previous_keywords = previous.get("keyword_counts", {}) or {}
        current_keywords = {mention.keyword: mention.total for mention in business.keyword_mentions}
        changes = []
        for keyword, count in current_keywords.items():
            old_count = previous_keywords.get(keyword, 0)
            if count != old_count:
                changes.append(f"{keyword}: {old_count} -> {count}")
        if changes:
            lines.append(("- Keyword changes: " if language == "en" else "- 关键词变化：") + ("; ".join(changes[:8]) if language == "en" else "；".join(changes[:8])))

    title = "## Historical Report Comparison" if language == "en" else "## 历史报告对比"
    return title + "\n\n" + "\n".join(lines) + "\n"


def format_industry_ranking(rows: list[dict[str, str | float | None]], language: Language = "zh") -> str:
    if len(rows) < 2:
        return ""

    scored = []
    for row in rows:
        score = 50
        if isinstance(row.get("近六个月涨跌幅"), float):
            score += 15 if row["近六个月涨跌幅"] > 0.15 else -10 if row["近六个月涨跌幅"] < -0.15 else 0
        if isinstance(row.get("收入增长"), float):
            score += 15 if row["收入增长"] > 0.2 else -10 if row["收入增长"] < 0 else 0
        if isinstance(row.get("利润率"), float):
            score += 10 if row["利润率"] > 0.2 else -10 if row["利润率"] < 0 else 0
        if row.get("成交额方向估算") == "成交额方向偏流入":
            score += 10
        if row.get("分析师共识") in {"强烈看多", "看多"}:
            score += 10
        scored.append((max(0, min(100, score)), row))

    scored.sort(key=lambda item: item[0], reverse=True)
    if language == "en":
        table = "| Rank | Symbol | Company | Industry | Opportunity score |\n| ---: | --- | --- | --- | ---: |\n"
    else:
        table = "| 排名 | 股票代码 | 公司名称 | 行业 | 机会评分 |\n| ---: | --- | --- | --- | ---: |\n"
    for index, (score, row) in enumerate(scored, start=1):
        table += f"| {index} | {row['股票代码']} | {row['公司名称']} | {row['细分行业']} | {score}/100 |\n"
    return ("## Industry / Watchlist Opportunity Ranking\n\n" if language == "en" else "## 行业 / 股票池机会评分\n\n") + table
