from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
import yfinance as yf
from yfinance.exceptions import YFRateLimitError

from data.company_profiles import get_company_profile
from data.free_api_data import fetch_free_api_data
from data.ticker_search import COMMON_TICKERS


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
    normalized_symbol = symbol.upper()
    ticker = yf.Ticker(symbol)
    info = _safe_dict(lambda: ticker.info) or {}
    fast_info = _safe_dict(lambda: dict(ticker.fast_info)) or {}
    free_api_data = fetch_free_api_data(normalized_symbol)
    profile = get_company_profile(normalized_symbol)
    history = _safe_history(lambda: ticker.history(period=period))
    if history.empty:
        history = _fetch_stooq_history(normalized_symbol)

    recommendations_summary = _safe_dataframe(lambda: ticker.recommendations_summary)
    analyst_price_targets = _safe_dict(lambda: ticker.analyst_price_targets)

    if history.empty:
        raise ValueError(f"没有找到 {normalized_symbol} 的股价数据，请检查股票代码是否正确，或稍后再试。")

    return StockSnapshot(
        symbol=normalized_symbol,
        company_name=(
            info.get("longName")
            or info.get("shortName")
            or free_api_data.company_name
            or (profile.name if profile else None)
            or COMMON_TICKERS.get(normalized_symbol)
            or normalized_symbol
        ),
        sector=info.get("sector") or free_api_data.sector or (profile.sector if profile else "Unknown"),
        industry=info.get("industry") or free_api_data.industry or (profile.industry if profile else "Unknown"),
        currency=info.get("currency") or fast_info.get("currency") or free_api_data.currency or (profile.currency if profile else "USD"),
        current_price=_safe_float(
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or fast_info.get("last_price")
            or fast_info.get("lastPrice")
        ) or free_api_data.current_price,
        market_cap=_safe_float(info.get("marketCap") or fast_info.get("market_cap") or fast_info.get("marketCap"))
        or free_api_data.market_cap,
        trailing_pe=_safe_float(info.get("trailingPE")) or free_api_data.trailing_pe,
        forward_pe=_safe_float(info.get("forwardPE")) or free_api_data.forward_pe,
        revenue_growth=_safe_float(info.get("revenueGrowth")) or free_api_data.revenue_growth,
        profit_margins=_safe_float(info.get("profitMargins")) or free_api_data.profit_margins,
        history=history,
        recommendations_summary=(
            recommendations_summary
            if recommendations_summary is not None
            else free_api_data.recommendations_summary
        ),
        analyst_price_targets=analyst_price_targets or free_api_data.analyst_price_targets,
    )


def _safe_dataframe(loader) -> pd.DataFrame | None:
    try:
        value = loader()
    except Exception:
        return None
    if isinstance(value, pd.DataFrame) and not value.empty:
        return value
    return None


def _safe_history(loader) -> pd.DataFrame:
    try:
        value = loader()
    except YFRateLimitError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()
    if isinstance(value, pd.DataFrame) and not value.empty:
        return value
    return pd.DataFrame()


def _safe_dict(loader) -> dict[str, float] | None:
    try:
        value = loader()
    except Exception:
        return None
    if isinstance(value, dict) and value:
        return value
    return None


def _fetch_stooq_history(symbol: str) -> pd.DataFrame:
    if "." in symbol:
        return pd.DataFrame()
    api_key = os.getenv("STOOQ_API_KEY")
    if not api_key:
        return pd.DataFrame()

    end = date.today()
    start = end - timedelta(days=210)
    url = (
        "https://stooq.com/q/d/l/"
        f"?s={symbol.lower()}.us&i=d&d1={start:%Y%m%d}&d2={end:%Y%m%d}&apikey={api_key}"
    )

    try:
        history = pd.read_csv(url, parse_dates=["Date"])
    except Exception:
        return pd.DataFrame()

    if history.empty or "Close" not in history.columns:
        return pd.DataFrame()

    history = history.set_index("Date").sort_index()
    return history.rename_axis(None)
