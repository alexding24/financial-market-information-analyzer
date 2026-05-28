from __future__ import annotations


COMMON_TICKERS = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "AMD": "Advanced Micro Devices, Inc.",
    "INTC": "Intel Corporation",
    "AVGO": "Broadcom Inc.",
    "TSM": "Taiwan Semiconductor Manufacturing Company",
    "ASML": "ASML Holding N.V.",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
    "META": "Meta Platforms, Inc.",
    "TSLA": "Tesla, Inc.",
    "NFLX": "Netflix, Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "BAC": "Bank of America Corporation",
    "V": "Visa Inc.",
    "MA": "Mastercard Incorporated",
    "UNH": "UnitedHealth Group Incorporated",
    "LLY": "Eli Lilly and Company",
    "NVO": "Novo Nordisk A/S",
    "MRK": "Merck & Co., Inc.",
    "PFE": "Pfizer Inc.",
    "XOM": "Exxon Mobil Corporation",
    "CVX": "Chevron Corporation",
    "CAT": "Caterpillar Inc.",
    "GE": "GE Aerospace",
    "BA": "The Boeing Company",
    "LMT": "Lockheed Martin Corporation",
    "NEE": "NextEra Energy, Inc.",
    "DUK": "Duke Energy Corporation",
    "PLTR": "Palantir Technologies Inc.",
    "CRWD": "CrowdStrike Holdings, Inc.",
    "SNOW": "Snowflake Inc.",
    "SHOP": "Shopify Inc.",
    "UBER": "Uber Technologies, Inc.",
    "ABNB": "Airbnb, Inc.",
    "COIN": "Coinbase Global, Inc.",
    "MSTR": "MicroStrategy Incorporated",
}


def suggest_tickers(query: str, limit: int = 8) -> list[str]:
    clean_query = query.strip().lower()
    if not clean_query:
        return []

    matches: list[tuple[int, str]] = []
    for ticker, name in COMMON_TICKERS.items():
        clean_ticker = ticker.lower()
        clean_name = name.lower()
        if clean_ticker.startswith(clean_query):
            matches.append((0, ticker))
        elif clean_query in clean_ticker:
            matches.append((1, ticker))
        elif clean_query in clean_name:
            matches.append((2, ticker))

    matches.sort(key=lambda item: (item[0], item[1]))
    return [f"{ticker} - {COMMON_TICKERS[ticker]}" for _, ticker in matches[:limit]]


def ticker_from_suggestion(value: str) -> str:
    return value.split(" - ", 1)[0].strip().upper()
