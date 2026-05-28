from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests


@dataclass(frozen=True)
class FreeApiData:
    company_name: str | None = None
    sector: str | None = None
    industry: str | None = None
    currency: str | None = None
    current_price: float | None = None
    market_cap: float | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    revenue_growth: float | None = None
    profit_margins: float | None = None
    recommendations_summary: pd.DataFrame | None = None
    analyst_price_targets: dict[str, float] | None = None


def fetch_free_api_data(symbol: str) -> FreeApiData:
    merged = FreeApiData()
    for provider_data in [
        _fetch_fmp_data(symbol),
        _fetch_finnhub_data(symbol),
        _fetch_alpha_vantage_data(symbol),
    ]:
        merged = _merge(merged, provider_data)
    return merged


def _merge(base: FreeApiData, update: FreeApiData) -> FreeApiData:
    return FreeApiData(
        company_name=base.company_name or update.company_name,
        sector=base.sector or update.sector,
        industry=base.industry or update.industry,
        currency=base.currency or update.currency,
        current_price=base.current_price if base.current_price is not None else update.current_price,
        market_cap=base.market_cap if base.market_cap is not None else update.market_cap,
        trailing_pe=base.trailing_pe if base.trailing_pe is not None else update.trailing_pe,
        forward_pe=base.forward_pe if base.forward_pe is not None else update.forward_pe,
        revenue_growth=base.revenue_growth if base.revenue_growth is not None else update.revenue_growth,
        profit_margins=base.profit_margins if base.profit_margins is not None else update.profit_margins,
        recommendations_summary=(
            base.recommendations_summary
            if base.recommendations_summary is not None
            else update.recommendations_summary
        ),
        analyst_price_targets=base.analyst_price_targets or update.analyst_price_targets,
    )


def _get_json(url: str, params: dict[str, str]) -> Any:
    try:
        response = requests.get(url, params=params, timeout=12)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def _first(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    if isinstance(value, dict):
        return value
    return {}


def _num(value: Any, scale: float = 1.0) -> float | None:
    if value in (None, "", "None", "N/A"):
        return None
    try:
        return float(value) * scale
    except (TypeError, ValueError):
        return None


def _pick_num(data: dict[str, Any], keys: list[str], scale: float = 1.0) -> float | None:
    for key in keys:
        value = _num(data.get(key), scale=scale)
        if value is not None:
            return value
    return None


def _recommendations_frame(values: dict[str, Any]) -> pd.DataFrame | None:
    row = {
        "strongBuy": int(_num(values.get("strongBuy")) or 0),
        "buy": int(_num(values.get("buy")) or 0),
        "hold": int(_num(values.get("hold")) or 0),
        "sell": int(_num(values.get("sell")) or 0),
        "strongSell": int(_num(values.get("strongSell")) or 0),
    }
    if not any(row.values()):
        return None
    return pd.DataFrame([row])


def _target_dict(mean: float | None) -> dict[str, float] | None:
    if mean is None:
        return None
    return {"mean": mean}


def _fetch_fmp_data(symbol: str) -> FreeApiData:
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return FreeApiData()

    params = {"apikey": api_key}
    profile = _first(_get_json(f"https://financialmodelingprep.com/api/v3/profile/{symbol}", params))
    ratios = _first(_get_json(f"https://financialmodelingprep.com/api/v3/ratios-ttm/{symbol}", params))
    metrics = _first(_get_json(f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{symbol}", params))
    income = _get_json(
        f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}",
        {"period": "annual", "limit": "2", "apikey": api_key},
    )
    price_target = _first(
        _get_json("https://financialmodelingprep.com/api/v4/price-target-summary", {"symbol": symbol, "apikey": api_key})
    )

    revenue_growth = _revenue_growth_from_income(income)
    target_mean = _pick_num(price_target, ["targetMean", "targetMeanPrice", "priceTargetAverage", "average"])

    return FreeApiData(
        company_name=profile.get("companyName") or profile.get("companyNameLong"),
        sector=profile.get("sector"),
        industry=profile.get("industry"),
        currency=profile.get("currency"),
        current_price=_pick_num(profile, ["price"]),
        market_cap=_pick_num(profile, ["mktCap", "marketCap"]),
        trailing_pe=_pick_num(ratios, ["priceEarningsRatioTTM", "peRatioTTM"]) or _pick_num(metrics, ["peRatioTTM"]),
        forward_pe=_pick_num(ratios, ["priceEarningsToGrowthRatioTTM", "pegRatioTTM"]),
        revenue_growth=revenue_growth,
        profit_margins=_pick_num(ratios, ["netProfitMarginTTM", "netProfitMargin"]),
        analyst_price_targets=_target_dict(target_mean),
    )


def _revenue_growth_from_income(value: Any) -> float | None:
    if not isinstance(value, list) or len(value) < 2:
        return None
    latest = _num(value[0].get("revenue"))
    previous = _num(value[1].get("revenue"))
    if latest is None or previous in (None, 0):
        return None
    return (latest / previous) - 1


def _fetch_finnhub_data(symbol: str) -> FreeApiData:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return FreeApiData()

    profile = _first(_get_json("https://finnhub.io/api/v1/stock/profile2", {"symbol": symbol, "token": api_key}))
    metric_result = _first(_get_json("https://finnhub.io/api/v1/stock/metric", {"symbol": symbol, "metric": "all", "token": api_key}))
    metrics = _first(metric_result.get("metric"))
    recommendations = _get_json("https://finnhub.io/api/v1/stock/recommendation", {"symbol": symbol, "token": api_key})
    price_target = _first(_get_json("https://finnhub.io/api/v1/stock/price-target", {"symbol": symbol, "token": api_key}))

    latest_rec = _first(recommendations)
    market_cap_millions = _num(profile.get("marketCapitalization"), scale=1_000_000)
    target_mean = _pick_num(price_target, ["targetMean", "targetMedian"])

    return FreeApiData(
        company_name=profile.get("name"),
        sector=profile.get("finnhubIndustry"),
        industry=profile.get("finnhubIndustry"),
        currency=profile.get("currency"),
        current_price=None,
        market_cap=market_cap_millions,
        trailing_pe=_pick_num(metrics, ["peTTM", "peBasicExclExtraTTM", "peNormalizedAnnual"]),
        forward_pe=_pick_num(metrics, ["forwardPE"]),
        revenue_growth=_pick_num(metrics, ["revenueGrowthTTMYoy", "revenueGrowthQuarterlyYoy"]),
        profit_margins=_pick_num(metrics, ["netProfitMarginTTM", "netProfitMarginAnnual"]),
        recommendations_summary=_recommendations_frame(latest_rec),
        analyst_price_targets=_target_dict(target_mean),
    )


def _fetch_alpha_vantage_data(symbol: str) -> FreeApiData:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return FreeApiData()

    overview = _first(
        _get_json("https://www.alphavantage.co/query", {"function": "OVERVIEW", "symbol": symbol, "apikey": api_key})
    )
    target = _pick_num(overview, ["AnalystTargetPrice"])

    return FreeApiData(
        company_name=overview.get("Name"),
        sector=overview.get("Sector"),
        industry=overview.get("Industry"),
        currency=overview.get("Currency"),
        market_cap=_pick_num(overview, ["MarketCapitalization"]),
        trailing_pe=_pick_num(overview, ["PERatio", "TrailingPE"]),
        forward_pe=_pick_num(overview, ["ForwardPE"]),
        revenue_growth=_pick_num(overview, ["QuarterlyRevenueGrowthYOY"]),
        profit_margins=_pick_num(overview, ["ProfitMargin"]),
        analyst_price_targets=_target_dict(target),
    )
