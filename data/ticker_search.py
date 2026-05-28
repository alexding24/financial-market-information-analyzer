from __future__ import annotations


TICKERS = {
    "AAPL": ("Apple Inc.", ["apple", "iphone", "mac", "苹果"]),
    "MSFT": ("Microsoft Corporation", ["microsoft", "微软", "azure", "office", "cloud", "ai"]),
    "NVDA": ("NVIDIA Corporation", ["nvidia", "英伟达", "gpu", "ai", "data center", "芯片"]),
    "AMD": ("Advanced Micro Devices, Inc.", ["amd", "超威", "gpu", "cpu", "芯片"]),
    "INTC": ("Intel Corporation", ["intel", "英特尔", "cpu", "芯片", "semiconductor"]),
    "AVGO": ("Broadcom Inc.", ["broadcom", "博通", "chip", "semiconductor", "networking"]),
    "TSM": ("Taiwan Semiconductor Manufacturing Company", ["tsmc", "台积电", "foundry", "semiconductor"]),
    "ASML": ("ASML Holding N.V.", ["asml", "光刻机", "semiconductor equipment"]),
    "AMZN": ("Amazon.com, Inc.", ["amazon", "亚马逊", "aws", "cloud", "ecommerce"]),
    "GOOGL": ("Alphabet Inc.", ["google", "alphabet", "谷歌", "search", "youtube", "ai"]),
    "META": ("Meta Platforms, Inc.", ["meta", "facebook", "instagram", "元宇宙", "广告"]),
    "TSLA": ("Tesla, Inc.", ["tesla", "特斯拉", "ev", "electric vehicle", "电动车"]),
    "NFLX": ("Netflix, Inc.", ["netflix", "奈飞", "streaming", "视频"]),
    "JPM": ("JPMorgan Chase & Co.", ["jpmorgan", "摩根大通", "bank", "银行"]),
    "BAC": ("Bank of America Corporation", ["bank of america", "美国银行", "bank", "银行"]),
    "V": ("Visa Inc.", ["visa", "支付", "payment"]),
    "MA": ("Mastercard Incorporated", ["mastercard", "万事达", "payment", "支付"]),
    "UNH": ("UnitedHealth Group Incorporated", ["unitedhealth", "health insurance", "医保"]),
    "LLY": ("Eli Lilly and Company", ["eli lilly", "礼来", "obesity", "减肥药", "diabetes"]),
    "NVO": ("Novo Nordisk A/S", ["novo", "novonordisk", "诺和诺德", "obesity", "减肥药", "diabetes"]),
    "MRK": ("Merck & Co., Inc.", ["merck", "默沙东", "pharma", "药"]),
    "PFE": ("Pfizer Inc.", ["pfizer", "辉瑞", "vaccine", "药"]),
    "XOM": ("Exxon Mobil Corporation", ["exxon", "埃克森", "oil", "energy", "石油"]),
    "CVX": ("Chevron Corporation", ["chevron", "雪佛龙", "oil", "energy", "石油"]),
    "CAT": ("Caterpillar Inc.", ["caterpillar", "卡特彼勒", "industrial", "工程机械"]),
    "GE": ("GE Aerospace", ["ge", "aerospace", "航空"]),
    "BA": ("The Boeing Company", ["boeing", "波音", "aircraft", "飞机"]),
    "LMT": ("Lockheed Martin Corporation", ["lockheed", "洛克希德", "defense", "军工"]),
    "NEE": ("NextEra Energy, Inc.", ["nextera", "renewable", "utility", "电力"]),
    "DUK": ("Duke Energy Corporation", ["duke", "utility", "电力"]),
    "PLTR": ("Palantir Technologies Inc.", ["palantir", "ai", "data", "software"]),
    "CRWD": ("CrowdStrike Holdings, Inc.", ["crowdstrike", "cybersecurity", "网络安全"]),
    "SNOW": ("Snowflake Inc.", ["snowflake", "data cloud", "database"]),
    "SHOP": ("Shopify Inc.", ["shopify", "ecommerce", "电商"]),
    "UBER": ("Uber Technologies, Inc.", ["uber", "ride hailing", "打车"]),
    "ABNB": ("Airbnb, Inc.", ["airbnb", "民宿", "travel"]),
    "COIN": ("Coinbase Global, Inc.", ["coinbase", "crypto", "bitcoin", "加密"]),
    "MSTR": ("MicroStrategy Incorporated", ["microstrategy", "bitcoin", "比特币"]),
    "0700.HK": ("Tencent Holdings Limited", ["tencent", "腾讯", "tenxun", "wechat", "微信", "游戏"]),
    "9988.HK": ("Alibaba Group Holding Limited", ["alibaba", "阿里巴巴", "阿里", "taobao", "淘宝", "cloud"]),
    "3690.HK": ("Meituan", ["meituan", "美团", "外卖", "本地生活"]),
    "1810.HK": ("Xiaomi Corporation", ["xiaomi", "小米", "手机", "ev", "电动车"]),
    "0939.HK": ("China Construction Bank", ["建设银行", "建行", "ccb", "bank", "银行"]),
    "1299.HK": ("AIA Group Limited", ["aia", "友邦", "保险"]),
    "600519.SS": ("Kweichow Moutai Co., Ltd.", ["贵州茅台", "茅台", "maotai", "白酒"]),
    "000858.SZ": ("Wuliangye Yibin Co., Ltd.", ["五粮液", "wuliangye", "白酒"]),
    "300750.SZ": ("Contemporary Amperex Technology Co., Limited", ["宁德时代", "宁德", "catl", "battery", "电池"]),
    "601318.SS": ("Ping An Insurance", ["中国平安", "平安", "pingan", "保险"]),
    "600036.SS": ("China Merchants Bank", ["招商银行", "招行", "cmb", "bank", "银行"]),
    "000333.SZ": ("Midea Group Co., Ltd.", ["美的", "midea", "家电"]),
    "002594.SZ": ("BYD Company Limited", ["比亚迪", "byd", "新能源车", "电动车"]),
}

COMMON_TICKERS = {ticker: data[0] for ticker, data in TICKERS.items()}


def _compact(value: str) -> str:
    return value.lower().replace(" ", "").replace("-", "").replace(".", "")


def _score_match(query: str, ticker: str, name: str, aliases: list[str]) -> int | None:
    clean_query = query.strip().lower()
    compact_query = _compact(clean_query)
    if not clean_query:
        return None

    searchable = [ticker, name, *aliases]
    compact_searchable = [_compact(item) for item in searchable]

    if ticker.lower().startswith(clean_query):
        return 0
    if any(item.startswith(compact_query) for item in compact_searchable):
        return 1
    if clean_query in name.lower():
        return 2
    if any(clean_query in item.lower() for item in aliases):
        return 3
    if any(compact_query in item for item in compact_searchable):
        return 4
    return None


def suggest_tickers(query: str, limit: int = 8) -> list[str]:
    clean_query = query.strip().lower()
    if not clean_query:
        return []

    matches: list[tuple[int, str]] = []
    for ticker, (name, aliases) in TICKERS.items():
        score = _score_match(clean_query, ticker, name, aliases)
        if score is not None:
            matches.append((score, ticker))

    matches.sort(key=lambda item: (item[0], item[1]))
    return [f"{ticker} - {COMMON_TICKERS[ticker]}" for _, ticker in matches[:limit]]


def best_ticker_match(query: str) -> str | None:
    suggestions = suggest_tickers(query, limit=1)
    if not suggestions:
        return None
    return ticker_from_suggestion(suggestions[0])


def ticker_from_suggestion(value: str) -> str:
    return value.split(" - ", 1)[0].strip().upper()
