from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class StockSnapshot:
    symbol: str
    company_name: str
    sector: str
    industry: str
    currency: str
    current_price: float | None
    market_cap: float | None
    trailing_pe: float | None
    forward_pe: float | None
    revenue_growth: float | None
    profit_margins: float | None
    history: pd.DataFrame
    recommendations_summary: pd.DataFrame | None
    analyst_price_targets: dict[str, float] | None


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_stock_snapshot(symbol: str, period: str = "6mo") -> StockSnapshot:
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    history = ticker.history(period=period)
    recommendations_summary = _safe_dataframe(lambda: ticker.recommendations_summary)
    analyst_price_targets = _safe_dict(lambda: ticker.analyst_price_targets)

    if history.empty:
        raise ValueError(f"没有找到 {symbol} 的股价数据，请检查股票代码是否正确。")

    return StockSnapshot(
        symbol=symbol.upper(),
        company_name=info.get("longName") or info.get("shortName") or symbol.upper(),
        sector=info.get("sector") or "Unknown",
        industry=info.get("industry") or "Unknown",
        currency=info.get("currency") or "USD",
        current_price=_safe_float(info.get("currentPrice") or info.get("regularMarketPrice")),
        market_cap=_safe_float(info.get("marketCap")),
        trailing_pe=_safe_float(info.get("trailingPE")),
        forward_pe=_safe_float(info.get("forwardPE")),
        revenue_growth=_safe_float(info.get("revenueGrowth")),
        profit_margins=_safe_float(info.get("profitMargins")),
        history=history,
        recommendations_summary=recommendations_summary,
        analyst_price_targets=analyst_price_targets,
    )


def _safe_dataframe(loader) -> pd.DataFrame | None:
    try:
        value = loader()
    except Exception:
        return None
    if isinstance(value, pd.DataFrame) and not value.empty:
        return value
    return None


def _safe_dict(loader) -> dict[str, float] | None:
    try:
        value = loader()
    except Exception:
        return None
    if isinstance(value, dict) and value:
        return value
    return None
