from __future__ import annotations

import re


MARKET_OPTIONS = {
    "自动识别": "auto",
    "美股": "us",
    "A股": "cn",
    "港股": "hk",
}


def normalize_symbol(symbol: str, market: str = "auto") -> str:
    clean_symbol = symbol.strip().upper()
    clean_market = market.lower()

    if not clean_symbol or "." in clean_symbol:
        return clean_symbol

    if clean_market == "hk":
        digits = re.sub(r"\D", "", clean_symbol)
        return f"{digits.zfill(4)}.HK" if digits else clean_symbol

    if clean_market == "cn":
        return _normalize_a_share(clean_symbol)

    if clean_market == "auto":
        if re.fullmatch(r"\d{4,5}", clean_symbol):
            return f"{clean_symbol.zfill(4)}.HK"
        if re.fullmatch(r"\d{6}", clean_symbol):
            return _normalize_a_share(clean_symbol)

    return clean_symbol


def _normalize_a_share(symbol: str) -> str:
    digits = re.sub(r"\D", "", symbol)
    if not digits:
        return symbol
    if digits.startswith(("5", "6", "9")):
        return f"{digits}.SS"
    return f"{digits}.SZ"


def is_us_symbol(symbol: str) -> bool:
    return "." not in symbol
