from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from analysis.business_signals import BusinessSignalSummary
from analysis.stock_summary import StockSummary


HISTORY_DIR = Path("reports/history")


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


def format_buy_checklist(summary: StockSummary) -> str:
    score, reasons = opportunity_score(summary)
    positives: list[str] = []
    cautions: list[str] = []
    questions: list[str] = []

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


def format_history_comparison(summary: StockSummary, previous: dict | None, business: BusinessSignalSummary | None) -> str:
    if previous is None:
        return "## 历史报告对比\n\n这是这个股票第一次保存历史快照，下一次生成报告后会自动比较变化。\n"

    score, _ = opportunity_score(summary)
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
            lines.append("- 关键词变化：" + "；".join(changes[:8]))

    return "## 历史报告对比\n\n" + "\n".join(lines) + "\n"


def format_industry_ranking(rows: list[dict[str, str | float | None]]) -> str:
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
    table = "| 排名 | 股票代码 | 公司名称 | 行业 | 机会评分 |\n| ---: | --- | --- | --- | ---: |\n"
    for index, (score, row) in enumerate(scored, start=1):
        table += f"| {index} | {row['股票代码']} | {row['公司名称']} | {row['细分行业']} | {score}/100 |\n"
    return "## 行业 / 股票池机会评分\n\n" + table
