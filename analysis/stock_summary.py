from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from data.stock_data import StockSnapshot


@dataclass(frozen=True)
class CapitalFlowPeriod:
    label: str
    net_flow: float
    large_flow: float
    small_flow: float


@dataclass(frozen=True)
class CapitalFlowSummary:
    periods: list[CapitalFlowPeriod]
    signal: str


@dataclass(frozen=True)
class AnalystSummary:
    consensus: str
    total_ratings: int | None
    bullish_ratio: float | None
    hold_ratio: float | None
    bearish_ratio: float | None
    target_mean: float | None
    target_upside: float | None


@dataclass(frozen=True)
class StockSummary:
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
    six_month_return: float
    recent_trend: str
    risk_level: str
    capital_flow: CapitalFlowSummary
    analyst: AnalystSummary
    data_sources: dict[str, str]


def _pct(value: float | None) -> str:
    if value is None:
        return "暂无数据"
    return f"{value * 100:.1f}%"


def _money(value: float | None, currency: str) -> str:
    if value is None:
        return "暂无数据"
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    if abs_value >= 1_000_000_000_000:
        return f"{sign}{currency} {abs_value / 1_000_000_000_000:.2f} 万亿"
    if abs_value >= 1_000_000_000:
        return f"{sign}{currency} {abs_value / 1_000_000_000:.2f} 十亿"
    if abs_value >= 1_000_000:
        return f"{sign}{currency} {abs_value / 1_000_000:.2f} 百万"
    return f"{sign}{currency} {abs_value:,.0f}"


def _trend_from_return(six_month_return: float) -> str:
    if six_month_return >= 0.15:
        return "偏强"
    if six_month_return <= -0.15:
        return "偏弱"
    return "震荡"


def _risk_level(summary: StockSnapshot, six_month_return: float) -> str:
    risk_points = 0

    if summary.trailing_pe and summary.trailing_pe > 50:
        risk_points += 1
    if summary.profit_margins is not None and summary.profit_margins < 0:
        risk_points += 1
    if six_month_return < -0.2:
        risk_points += 1

    if risk_points >= 2:
        return "较高"
    if risk_points == 1:
        return "中等"
    return "较低"


def _capital_flow_signal(three_month_flow: float, three_month_turnover: float) -> str:
    if three_month_turnover <= 0:
        return "暂无足够数据"
    flow_ratio = three_month_flow / three_month_turnover
    if flow_ratio >= 0.03:
        return "成交额方向偏流入"
    if flow_ratio <= -0.03:
        return "成交额方向偏流出"
    return "成交额方向平衡"


def _sum_signed_flow(history: pd.DataFrame, days: int | None, label: str) -> CapitalFlowPeriod:
    window = history if days is None else history.tail(days)
    signed_flow = window["SignedFlow"]
    large_flow = window.loc[window["IsLargeVolumeDay"], "SignedFlow"].sum()
    small_flow = window.loc[~window["IsLargeVolumeDay"], "SignedFlow"].sum()
    return CapitalFlowPeriod(
        label=label,
        net_flow=float(signed_flow.sum()),
        large_flow=float(large_flow),
        small_flow=float(small_flow),
    )


def _analyze_capital_flow(history: pd.DataFrame) -> CapitalFlowSummary:
    flow_data = history[["Close", "Volume"]].dropna().copy()
    flow_data["PreviousClose"] = flow_data["Close"].shift(1)
    flow_data["Direction"] = 0
    flow_data.loc[flow_data["Close"] > flow_data["PreviousClose"], "Direction"] = 1
    flow_data.loc[flow_data["Close"] < flow_data["PreviousClose"], "Direction"] = -1
    flow_data["DollarVolume"] = flow_data["Close"] * flow_data["Volume"]
    flow_data["SignedFlow"] = flow_data["DollarVolume"] * flow_data["Direction"]
    flow_data["AverageVolume20d"] = flow_data["Volume"].rolling(20, min_periods=5).mean()
    flow_data["IsLargeVolumeDay"] = flow_data["Volume"] >= flow_data["AverageVolume20d"] * 1.5
    flow_data = flow_data.dropna(subset=["SignedFlow"])

    one_month = _sum_signed_flow(flow_data, 21, "近1个月")
    three_month = _sum_signed_flow(flow_data, 63, "近3个月")
    six_month = _sum_signed_flow(flow_data, None, "近6个月")
    turnover_3m = float(flow_data.tail(63)["DollarVolume"].sum())

    return CapitalFlowSummary(
        periods=[one_month, three_month, six_month],
        signal=_capital_flow_signal(three_month.net_flow, turnover_3m),
    )


def _safe_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _analyze_analysts(snapshot: StockSnapshot, current_price: float | None) -> AnalystSummary:
    recs = snapshot.recommendations_summary
    latest = None if recs is None or recs.empty else recs.iloc[0]

    strong_buy = _safe_int(latest.get("strongBuy")) if latest is not None else 0
    buy = _safe_int(latest.get("buy")) if latest is not None else 0
    hold = _safe_int(latest.get("hold")) if latest is not None else 0
    sell = _safe_int(latest.get("sell")) if latest is not None else 0
    strong_sell = _safe_int(latest.get("strongSell")) if latest is not None else 0
    total = strong_buy + buy + hold + sell + strong_sell

    if total:
        score = ((strong_buy * 5) + (buy * 4) + (hold * 3) + (sell * 2) + strong_sell) / total
        bullish_ratio = (strong_buy + buy) / total
        hold_ratio = hold / total
        bearish_ratio = (sell + strong_sell) / total
        if score >= 4.2:
            consensus = "强烈看多"
        elif score >= 3.6:
            consensus = "看多"
        elif score >= 2.8:
            consensus = "中性"
        elif score >= 2.2:
            consensus = "看空"
        else:
            consensus = "强烈看空"
    else:
        consensus = "暂无评级数据"
        bullish_ratio = None
        hold_ratio = None
        bearish_ratio = None

    targets = snapshot.analyst_price_targets or {}
    target_mean = targets.get("mean")
    target_upside = None
    if current_price and target_mean:
        target_upside = (float(target_mean) / current_price) - 1

    return AnalystSummary(
        consensus=consensus,
        total_ratings=total or None,
        bullish_ratio=bullish_ratio,
        hold_ratio=hold_ratio,
        bearish_ratio=bearish_ratio,
        target_mean=None if target_mean is None else float(target_mean),
        target_upside=target_upside,
    )


def summarize_stock(snapshot: StockSnapshot) -> StockSummary:
    close_prices = snapshot.history["Close"].dropna()
    first_close = float(close_prices.iloc[0])
    last_close = float(close_prices.iloc[-1])
    six_month_return = (last_close / first_close) - 1

    current_price = snapshot.current_price or last_close
    capital_flow = _analyze_capital_flow(snapshot.history)
    analyst = _analyze_analysts(snapshot, current_price)

    return StockSummary(
        symbol=snapshot.symbol,
        company_name=snapshot.company_name,
        sector=snapshot.sector,
        industry=snapshot.industry,
        currency=snapshot.currency,
        current_price=current_price,
        market_cap=snapshot.market_cap,
        trailing_pe=snapshot.trailing_pe,
        forward_pe=snapshot.forward_pe,
        revenue_growth=snapshot.revenue_growth,
        profit_margins=snapshot.profit_margins,
        six_month_return=six_month_return,
        recent_trend=_trend_from_return(six_month_return),
        risk_level=_risk_level(snapshot, six_month_return),
        capital_flow=capital_flow,
        analyst=analyst,
        data_sources=snapshot.data_sources,
    )


def format_summary_value(summary: StockSummary) -> dict[str, str]:
    return {
        "股票代码": summary.symbol,
        "公司名称": summary.company_name,
        "行业板块": summary.sector,
        "细分行业": summary.industry,
        "当前价格": _money(summary.current_price, summary.currency),
        "市值": _money(summary.market_cap, summary.currency),
        "过去市盈率": "暂无数据" if summary.trailing_pe is None else f"{summary.trailing_pe:.1f}",
        "未来市盈率": "暂无数据" if summary.forward_pe is None else f"{summary.forward_pe:.1f}",
        "收入增长": _pct(summary.revenue_growth),
        "利润率": _pct(summary.profit_margins),
        "近六个月涨跌幅": _pct(summary.six_month_return),
        "近期趋势": summary.recent_trend,
        "基础风险等级": summary.risk_level,
        "成交额方向估算": summary.capital_flow.signal,
        "分析师共识": summary.analyst.consensus,
        "分析师数量": "暂无数据" if summary.analyst.total_ratings is None else str(summary.analyst.total_ratings),
        "平均目标价": _money(summary.analyst.target_mean, summary.currency),
        "目标价空间": _pct(summary.analyst.target_upside),
    }


def comparison_row(summary: StockSummary) -> dict[str, str | float | None]:
    return {
        "股票代码": summary.symbol,
        "公司名称": summary.company_name,
        "行业板块": summary.sector,
        "细分行业": summary.industry,
        "当前价格": None if summary.current_price is None else round(summary.current_price, 2),
        "市值": summary.market_cap,
        "过去市盈率": summary.trailing_pe,
        "未来市盈率": summary.forward_pe,
        "收入增长": None if summary.revenue_growth is None else summary.revenue_growth,
        "利润率": None if summary.profit_margins is None else summary.profit_margins,
        "近六个月涨跌幅": summary.six_month_return,
        "近期趋势": summary.recent_trend,
        "基础风险等级": summary.risk_level,
        "成交额方向估算": summary.capital_flow.signal,
        "分析师共识": summary.analyst.consensus,
        "目标价空间": summary.analyst.target_upside,
    }


def format_capital_flow_table(summary: StockSummary) -> str:
    header = "| 周期 | 成交额方向估算 | 大额成交日估算 | 普通成交日估算 |\n"
    divider = "| --- | ---: | ---: | ---: |\n"
    body = ""
    for period in summary.capital_flow.periods:
        body += (
            f"| {period.label} | {_money(period.net_flow, summary.currency)} | "
            f"{_money(period.large_flow, summary.currency)} | {_money(period.small_flow, summary.currency)} |\n"
        )
    return header + divider + body


def data_quality_score(summary: StockSummary) -> int:
    values = format_summary_value(summary)
    tracked_fields = [
        "行业板块",
        "细分行业",
        "当前价格",
        "市值",
        "过去市盈率",
        "未来市盈率",
        "收入增长",
        "利润率",
        "分析师共识",
        "平均目标价",
    ]
    available = sum(1 for field in tracked_fields if values.get(field) not in {"暂无数据", "暂无评级数据", "Unknown"})
    return round(available / len(tracked_fields) * 100)


def format_data_quality_report(summary: StockSummary) -> str:
    sources = summary.data_sources or {}
    values = format_summary_value(summary)
    missing_fields = [
        field
        for field in ["行业板块", "细分行业", "当前价格", "市值", "过去市盈率", "未来市盈率", "收入增长", "利润率", "分析师共识", "平均目标价"]
        if values.get(field) in {"暂无数据", "暂无评级数据", "Unknown"}
    ]
    source_rows = [
        ("价格历史", sources.get("price_history", "Unknown")),
        ("公司名称", sources.get("company_name", "Unknown")),
        ("行业板块", sources.get("sector", "Unknown")),
        ("细分行业", sources.get("industry", "Unknown")),
        ("当前价格", sources.get("current_price", "Unknown")),
        ("市值", sources.get("market_cap", "Unknown")),
        ("PE", sources.get("trailing_pe", "Unknown")),
        ("收入增长", sources.get("revenue_growth", "Unknown")),
        ("利润率", sources.get("profit_margins", "Unknown")),
        ("分析师评级", sources.get("recommendations_summary", "Unknown")),
        ("目标价", sources.get("analyst_price_targets", "Unknown")),
    ]
    table = "| 字段 | 来源 |\n| --- | --- |\n"
    table += "".join(f"| {field} | {source} |\n" for field, source in source_rows)
    missing_text = "无明显缺失" if not missing_fields else "、".join(missing_fields)
    return f"""## 数据质量

- **完整度评分**：{data_quality_score(summary)}/100
- **缺失字段**：{missing_text}

{table}
"""


def format_analyst_summary(summary: StockSummary) -> str:
    analyst = summary.analyst
    bullish = _pct(analyst.bullish_ratio)
    hold = _pct(analyst.hold_ratio)
    bearish = _pct(analyst.bearish_ratio)
    return (
        f"- **共识评级**：{analyst.consensus}\n"
        f"- **覆盖分析师数量**：{'暂无数据' if analyst.total_ratings is None else analyst.total_ratings}\n"
        f"- **看多 / 中性 / 看空比例**：{bullish} / {hold} / {bearish}\n"
        f"- **平均目标价**：{_money(analyst.target_mean, summary.currency)}\n"
        f"- **相对当前价格空间**：{_pct(analyst.target_upside)}"
    )
