from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf


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
    return [_metric(row, combined) for row in FINANCIAL_ROWS]


def _money(value: float | None) -> str:
    if value is None:
        return "暂无数据"
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    if abs_value >= 1_000_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000_000:.2f} 万亿"
    if abs_value >= 1_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000:.2f} 十亿"
    if abs_value >= 1_000_000:
        return f"{sign}{abs_value / 1_000_000:.2f} 百万"
    return f"{sign}{abs_value:,.0f}"


def _pct(value: float | None) -> str:
    if value is None:
        return "暂无数据"
    return f"{value:.1%}"


def format_financial_metrics(metrics: list[FinancialMetric]) -> str:
    if not metrics:
        return ""

    table = "| 指标 | 最近季度 | 上一季度 | 环比变化 |\n"
    table += "| --- | ---: | ---: | ---: |\n"
    for metric in metrics:
        table += f"| {metric.name} | {_money(metric.latest)} | {_money(metric.previous)} | {_pct(metric.change)} |\n"

    return f"""## 财报关键表格

{table}

说明：这里优先读取 Yahoo Finance 可提供的最近季度财务表，适合快速观察，不替代正式 10-K / 10-Q 原文核对。
"""
