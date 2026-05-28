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
    "0700.HK": "Tencent Holdings Limited",
    "9988.HK": "Alibaba Group Holding Limited",
    "3690.HK": "Meituan",
    "1810.HK": "Xiaomi Corporation",
    "0939.HK": "China Construction Bank",
    "1299.HK": "AIA Group Limited",
    "600519.SS": "Kweichow Moutai Co., Ltd.",
    "000858.SZ": "Wuliangye Yibin Co., Ltd.",
    "300750.SZ": "Contemporary Amperex Technology Co., Limited",
    "601318.SS": "Ping An Insurance",
    "600036.SS": "China Merchants Bank",
    "000333.SZ": "Midea Group Co., Ltd.",
    "002594.SZ": "BYD Company Limited",
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
