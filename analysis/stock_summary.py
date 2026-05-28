from __future__ import annotations

from dataclasses import dataclass

from data.stock_data import StockSnapshot


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


def _pct(value: float | None) -> str:
    if value is None:
        return "暂无数据"
    return f"{value * 100:.1f}%"


def _money(value: float | None, currency: str) -> str:
    if value is None:
        return "暂无数据"
    if value >= 1_000_000_000_000:
        return f"{currency} {value / 1_000_000_000_000:.2f} 万亿"
    if value >= 1_000_000_000:
        return f"{currency} {value / 1_000_000_000:.2f} 十亿"
    if value >= 1_000_000:
        return f"{currency} {value / 1_000_000:.2f} 百万"
    return f"{currency} {value:,.0f}"


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


def summarize_stock(snapshot: StockSnapshot) -> StockSummary:
    close_prices = snapshot.history["Close"].dropna()
    first_close = float(close_prices.iloc[0])
    last_close = float(close_prices.iloc[-1])
    six_month_return = (last_close / first_close) - 1

    current_price = snapshot.current_price or last_close

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
    }
