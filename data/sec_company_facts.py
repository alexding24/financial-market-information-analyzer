from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from typing import Any

import requests

from data.cache import ttl_cache


SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


@dataclass(frozen=True)
class SecFact:
    name: str
    latest: float | None
    previous: float | None
    change: float | None


@dataclass(frozen=True)
class SecCompanyFacts:
    revenue_growth: float | None = None
    profit_margins: float | None = None
    facts: list[SecFact] = None


SEC_FACT_ROWS = {
    "Total Revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "Gross Profit": ["GrossProfit"],
    "Operating Income": ["OperatingIncomeLoss"],
    "Net Income": ["NetIncomeLoss", "ProfitLoss"],
    "Operating Cash Flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "Free Cash Flow": ["FreeCashFlow"],
    "Total Assets": ["Assets"],
    "Total Debt": ["LongTermDebtAndFinanceLeaseObligations", "LongTermDebt", "DebtCurrent"],
    "Stockholders Equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
}


@ttl_cache(seconds=21600)
def fetch_sec_company_facts(symbol: str) -> SecCompanyFacts:
    cik = ticker_to_cik(symbol)
    if not cik:
        return SecCompanyFacts(facts=[])

    payload = _get_json(SEC_COMPANY_FACTS_URL.format(cik=cik))
    facts_payload = payload.get("facts", {}).get("us-gaap", {}) if isinstance(payload, dict) else {}
    facts = [_build_fact(label, facts_payload, tags) for label, tags in SEC_FACT_ROWS.items()]
    revenue = _find_latest_pair(facts_payload, SEC_FACT_ROWS["Total Revenue"], annual=True)
    net_income = _find_latest_pair(facts_payload, SEC_FACT_ROWS["Net Income"], annual=True)
    revenue_growth = _change(revenue.latest, revenue.previous) if revenue else None
    profit_margins = None
    if revenue and net_income and revenue.latest not in (None, 0) and net_income.latest is not None:
        profit_margins = net_income.latest / revenue.latest

    return SecCompanyFacts(
        revenue_growth=revenue_growth,
        profit_margins=profit_margins,
        facts=facts,
    )


@lru_cache(maxsize=1)
def _ticker_map() -> dict[str, str]:
    payload = _get_json(SEC_COMPANY_TICKERS_URL)
    if not isinstance(payload, dict):
        return {}
    return {
        str(company.get("ticker", "")).upper(): str(company.get("cik_str", "")).zfill(10)
        for company in payload.values()
    }


def ticker_to_cik(symbol: str) -> str | None:
    return _ticker_map().get(symbol.upper().split(".", 1)[0])


def _headers() -> dict[str, str]:
    return {
        "User-Agent": os.getenv("SEC_USER_AGENT", "financial-market-analyzer/0.1 research@example.com"),
        "Accept-Encoding": "gzip, deflate",
    }


def _get_json(url: str) -> Any:
    try:
        response = requests.get(url, headers=_headers(), timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def _build_fact(label: str, facts_payload: dict[str, Any], tags: list[str]) -> SecFact:
    latest_pair = _find_latest_pair(facts_payload, tags, annual=False)
    if latest_pair is None:
        return SecFact(label, None, None, None)
    return SecFact(
        name=label,
        latest=latest_pair.latest,
        previous=latest_pair.previous,
        change=_change(latest_pair.latest, latest_pair.previous),
    )


@dataclass(frozen=True)
class _FactPair:
    latest: float | None
    previous: float | None


def _find_latest_pair(facts_payload: dict[str, Any], tags: list[str], annual: bool) -> _FactPair | None:
    all_values = []
    for tag in tags:
        fact = facts_payload.get(tag, {})
        units = fact.get("units", {}) if isinstance(fact, dict) else {}
        values = []
        for unit_values in units.values():
            if isinstance(unit_values, list):
                values.extend(unit_values)
        filtered = [_clean_fact_value(value, annual) for value in values]
        filtered = [value for value in filtered if value is not None]
        all_values.extend(filtered)
    all_values.sort(key=lambda value: (value["end"], value.get("filed", "")), reverse=True)
    if all_values:
        latest = all_values[0]["val"]
        previous = all_values[1]["val"] if len(all_values) > 1 else None
        return _FactPair(latest, previous)
    return None


def _clean_fact_value(value: dict[str, Any], annual: bool) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    form = value.get("form")
    frame = str(value.get("frame", ""))
    if annual and form not in {"10-K", "20-F", "40-F"}:
        return None
    if not annual and form not in {"10-K", "10-Q", "20-F", "40-F"}:
        return None
    duration_days = _duration_days(value)
    if annual and duration_days is not None and duration_days < 300:
        return None
    if not annual and duration_days is not None and duration_days > 140:
        return None
    if not annual and frame.startswith("CY") and not frame.endswith(("Q1", "Q2", "Q3", "Q4")) and form == "10-Q":
        return None
    try:
        return {
            "val": float(value["val"]),
            "end": str(value.get("end", "")),
            "filed": str(value.get("filed", "")),
        }
    except (KeyError, TypeError, ValueError):
        return None


def _change(latest: float | None, previous: float | None) -> float | None:
    if latest is None or previous in (None, 0):
        return None
    return (latest / previous) - 1


def _duration_days(value: dict[str, Any]) -> int | None:
    start = value.get("start")
    end = value.get("end")
    if not start or not end:
        return None
    try:
        return (date.fromisoformat(str(end)) - date.fromisoformat(str(start))).days
    except ValueError:
        return None
