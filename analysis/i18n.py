from __future__ import annotations

from typing import Literal


Language = Literal["zh", "en"]


NO_DATA = {
    "zh": "暂无数据",
    "en": "No data",
}

NO_RATING = {
    "zh": "暂无评级数据",
    "en": "No rating data",
}

UNKNOWN = {
    "zh": "Unknown",
    "en": "Unknown",
}

FIELD_LABELS = {
    "股票代码": {"zh": "股票代码", "en": "Symbol"},
    "公司名称": {"zh": "公司名称", "en": "Company"},
    "行业板块": {"zh": "行业板块", "en": "Sector"},
    "细分行业": {"zh": "细分行业", "en": "Industry"},
    "当前价格": {"zh": "当前价格", "en": "Current price"},
    "市值": {"zh": "市值", "en": "Market cap"},
    "过去市盈率": {"zh": "过去市盈率", "en": "Trailing P/E"},
    "未来市盈率": {"zh": "未来市盈率", "en": "Forward P/E"},
    "收入增长": {"zh": "收入增长", "en": "Revenue growth"},
    "利润率": {"zh": "利润率", "en": "Profit margin"},
    "近六个月涨跌幅": {"zh": "近六个月涨跌幅", "en": "Six-month return"},
    "近期趋势": {"zh": "近期趋势", "en": "Recent trend"},
    "基础风险等级": {"zh": "基础风险等级", "en": "Base risk level"},
    "成交额方向估算": {"zh": "成交额方向估算", "en": "Dollar-volume direction estimate"},
    "分析师共识": {"zh": "分析师共识", "en": "Analyst consensus"},
    "分析师数量": {"zh": "分析师数量", "en": "Analyst count"},
    "平均目标价": {"zh": "平均目标价", "en": "Average target price"},
    "目标价空间": {"zh": "目标价空间", "en": "Target upside"},
}

VALUE_LABELS = {
    "偏强": {"zh": "偏强", "en": "Strong"},
    "偏弱": {"zh": "偏弱", "en": "Weak"},
    "震荡": {"zh": "震荡", "en": "Range-bound"},
    "较高": {"zh": "较高", "en": "High"},
    "中等": {"zh": "中等", "en": "Medium"},
    "较低": {"zh": "较低", "en": "Low"},
    "暂无足够数据": {"zh": "暂无足够数据", "en": "Not enough data"},
    "成交额方向偏流入": {"zh": "成交额方向偏流入", "en": "Dollar-volume direction skews positive"},
    "成交额方向偏流出": {"zh": "成交额方向偏流出", "en": "Dollar-volume direction skews negative"},
    "成交额方向平衡": {"zh": "成交额方向平衡", "en": "Dollar-volume direction is balanced"},
    "强烈看多": {"zh": "强烈看多", "en": "Strong bullish"},
    "看多": {"zh": "看多", "en": "Bullish"},
    "中性": {"zh": "中性", "en": "Neutral"},
    "看空": {"zh": "看空", "en": "Bearish"},
    "强烈看空": {"zh": "强烈看空", "en": "Strong bearish"},
    "暂无评级数据": {"zh": "暂无评级数据", "en": "No rating data"},
}


def label(value: str, language: Language = "zh") -> str:
    return VALUE_LABELS.get(value, {}).get(language, value)


def field_label(value: str, language: Language = "zh") -> str:
    return FIELD_LABELS.get(value, {}).get(language, value)


def missing_value(language: Language = "zh") -> str:
    return NO_DATA[language]


def missing_rating(language: Language = "zh") -> str:
    return NO_RATING[language]


def is_missing_display(value: str) -> bool:
    return value in {"暂无数据", "暂无评级数据", "No data", "No rating data", "Unknown"}
