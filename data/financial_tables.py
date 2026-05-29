from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf

from analysis.i18n import Language, missing_value
from data.cache import ttl_cache
from data.sec_company_facts import fetch_sec_company_facts


FINANCIAL_ROWS = [
    "Total Revenue",
    "Gross Profit",
    "Operating Income",
    "Net Income",
    "Operating Cash Flow",
    "Free Cash Flow",
    "Total Debt",
]


@dataclass(frozen=True)
class FinancialMetric:
    name: str
    latest: float | None
    previous: float | None
    change: float | None


def _get_row(frame: pd.DataFrame, row_name: str) -> tuple[float | None, float | None]:
    if frame is None or frame.empty or row_name not in frame.index:
        return None, None
    values = frame.loc[row_name].dropna()
    if values.empty:
        return None, None
    latest = float(values.iloc[0])
    previous = float(values.iloc[1]) if len(values) > 1 else None
    return latest, previous


def _metric(name: str, frame: pd.DataFrame) -> FinancialMetric:
    latest, previous = _get_row(frame, name)
    change = None
    if latest is not None and previous not in (None, 0):
        change = (latest / previous) - 1
    return FinancialMetric(name=name, latest=latest, previous=previous, change=change)


@ttl_cache(seconds=3600)
def fetch_financial_metrics(symbol: str) -> list[FinancialMetric]:
    ticker = yf.Ticker(symbol)
    frames = []
    for loader in [lambda: ticker.quarterly_financials, lambda: ticker.quarterly_cashflow, lambda: ticker.quarterly_balance_sheet]:
        try:
            frame = loader()
        except Exception:
            frame = pd.DataFrame()
        frames.append(frame)

    combined = pd.concat(frames) if frames else pd.DataFrame()
    metrics = [_metric(row, combined) for row in FINANCIAL_ROWS]
    if all(metric.latest is None for metric in metrics):
        sec_facts = fetch_sec_company_facts(symbol)
        return [
            FinancialMetric(fact.name, fact.latest, fact.previous, fact.change)
            for fact in (sec_facts.facts or [])
        ]
    return metrics


def _money(value: float | None, language: Language = "zh") -> str:
    if value is None:
        return missing_value(language)
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    if language == "en":
        if abs_value >= 1_000_000_000_000:
            return f"{sign}{abs_value / 1_000_000_000_000:.2f}T"
        if abs_value >= 1_000_000_000:
            return f"{sign}{abs_value / 1_000_000_000:.2f}B"
        if abs_value >= 1_000_000:
            return f"{sign}{abs_value / 1_000_000:.2f}M"
        return f"{sign}{abs_value:,.0f}"
    if abs_value >= 1_000_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000_000:.2f} 万亿"
    if abs_value >= 1_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000:.2f} 十亿"
    if abs_value >= 1_000_000:
        return f"{sign}{abs_value / 1_000_000:.2f} 百万"
    return f"{sign}{abs_value:,.0f}"


def _pct(value: float | None, language: Language = "zh") -> str:
    if value is None:
        return missing_value(language)
    return f"{value:.1%}"


def format_financial_metrics(metrics: list[FinancialMetric], language: Language = "zh") -> str:
    if not metrics:
        return ""

    if language == "en":
        table = "| Metric | Latest quarter | Previous quarter | QoQ change |\n"
    else:
        table = "| 指标 | 最近季度 | 上一季度 | 环比变化 |\n"
    table += "| --- | ---: | ---: | ---: |\n"
    for metric in metrics:
        table += f"| {metric.name} | {_money(metric.latest, language)} | {_money(metric.previous, language)} | {_pct(metric.change, language)} |\n"

    if language == "en":
        return f"""## Key Financial Tables

{table}

Note: this section prioritizes the latest quarterly financial tables available through Yahoo Finance. It is useful for a quick check, but it does not replace reviewing the official 10-K / 10-Q.
"""

    return f"""## 财报关键表格

{table}

说明：这里优先读取 Yahoo Finance 可提供的最近季度财务表，适合快速观察，不替代正式 10-K / 10-Q 原文核对。
"""
