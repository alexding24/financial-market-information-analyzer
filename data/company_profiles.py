from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyProfile:
    name: str
    sector: str
    industry: str
    currency: str = "USD"


COMPANY_PROFILES: dict[str, CompanyProfile] = {
    "AAPL": CompanyProfile("Apple Inc.", "Technology", "Consumer Electronics"),
    "MSFT": CompanyProfile("Microsoft Corporation", "Technology", "Software - Infrastructure"),
    "NVDA": CompanyProfile("NVIDIA Corporation", "Technology", "Semiconductors"),
    "AMD": CompanyProfile("Advanced Micro Devices, Inc.", "Technology", "Semiconductors"),
    "INTC": CompanyProfile("Intel Corporation", "Technology", "Semiconductors"),
    "AVGO": CompanyProfile("Broadcom Inc.", "Technology", "Semiconductors"),
    "TSM": CompanyProfile("Taiwan Semiconductor Manufacturing Company", "Technology", "Semiconductors"),
    "ASML": CompanyProfile("ASML Holding N.V.", "Technology", "Semiconductor Equipment"),
    "AMZN": CompanyProfile("Amazon.com, Inc.", "Consumer Cyclical", "Internet Retail"),
    "GOOGL": CompanyProfile("Alphabet Inc.", "Communication Services", "Internet Content & Information"),
    "META": CompanyProfile("Meta Platforms, Inc.", "Communication Services", "Internet Content & Information"),
    "TSLA": CompanyProfile("Tesla, Inc.", "Consumer Cyclical", "Auto Manufacturers"),
    "JPM": CompanyProfile("JPMorgan Chase & Co.", "Financial Services", "Banks - Diversified"),
    "BAC": CompanyProfile("Bank of America Corporation", "Financial Services", "Banks - Diversified"),
    "V": CompanyProfile("Visa Inc.", "Financial Services", "Credit Services"),
    "MA": CompanyProfile("Mastercard Incorporated", "Financial Services", "Credit Services"),
    "LLY": CompanyProfile("Eli Lilly and Company", "Healthcare", "Drug Manufacturers - General"),
    "XOM": CompanyProfile("Exxon Mobil Corporation", "Energy", "Oil & Gas Integrated"),
    "PLTR": CompanyProfile("Palantir Technologies Inc.", "Technology", "Software - Infrastructure"),
    "CRWD": CompanyProfile("CrowdStrike Holdings, Inc.", "Technology", "Software - Infrastructure"),
    "0700.HK": CompanyProfile("Tencent Holdings Limited", "Communication Services", "Internet Content & Information", "HKD"),
    "9988.HK": CompanyProfile("Alibaba Group Holding Limited", "Consumer Cyclical", "Internet Retail", "HKD"),
    "3690.HK": CompanyProfile("Meituan", "Consumer Cyclical", "Internet Retail", "HKD"),
    "1810.HK": CompanyProfile("Xiaomi Corporation", "Technology", "Consumer Electronics", "HKD"),
    "600519.SS": CompanyProfile("Kweichow Moutai Co., Ltd.", "Consumer Defensive", "Beverages - Wineries & Distilleries", "CNY"),
    "000858.SZ": CompanyProfile("Wuliangye Yibin Co., Ltd.", "Consumer Defensive", "Beverages - Wineries & Distilleries", "CNY"),
    "300750.SZ": CompanyProfile("Contemporary Amperex Technology Co., Limited", "Consumer Cyclical", "Auto Parts", "CNY"),
    "002594.SZ": CompanyProfile("BYD Company Limited", "Consumer Cyclical", "Auto Manufacturers", "CNY"),
}


def get_company_profile(symbol: str) -> CompanyProfile | None:
    return COMPANY_PROFILES.get(symbol.upper())
