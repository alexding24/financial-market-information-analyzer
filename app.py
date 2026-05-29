from __future__ import annotations

import argparse
import re
from pathlib import Path

from analysis.ai_report import build_report
from analysis.business_signals import (
    BusinessSignalSummary,
    SourceDocument,
    analyze_business_signals,
    format_business_signal_report,
    parse_keywords,
)
from analysis.research_features import (
    format_buy_checklist,
    format_history_comparison,
    format_industry_ranking,
    load_last_snapshot,
    save_snapshot,
)
from analysis.stock_summary import comparison_row, summarize_stock
from data.financial_tables import fetch_financial_metrics, format_financial_metrics
from data.market_symbols import normalize_symbol
from data.public_documents import fetch_public_documents
from data.stock_data import fetch_stock_snapshot
from data.ticker_search import best_ticker_match


def save_report(symbol: str, report: str) -> Path:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    output_path = reports_dir / f"{symbol.upper()}_report.md"
    output_path.write_text(report, encoding="utf-8")
    return output_path


def parse_symbols(raw_symbols: list[str], market: str = "auto") -> list[str]:
    symbols: list[str] = []
    for raw_symbol in raw_symbols:
        for part in re.split(r"[\s,]+", raw_symbol):
            raw_part = part.strip()
            symbol = best_ticker_match(raw_part) or normalize_symbol(raw_part, market)
            if symbol and symbol not in symbols:
                symbols.append(symbol)
    return symbols


def build_comparison_report(rows: list[dict[str, str | float | None]]) -> str:
    header = "| 股票代码 | 公司名称 | 行业板块 | 细分行业 | 近六个月涨跌幅 | 收入增长 | 利润率 | 未来市盈率 | 成交额方向估算 | 分析师共识 | 目标价空间 | 风险 |\n"
    divider = "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |\n"
    body = ""

    for row in rows:
        six_month_return = row["近六个月涨跌幅"]
        revenue_growth = row["收入增长"]
        profit_margins = row["利润率"]
        forward_pe = row["未来市盈率"]
        target_upside = row["目标价空间"]
        body += (
            f"| {row['股票代码']} | {row['公司名称']} | {row['行业板块']} | {row['细分行业']} | "
            f"{six_month_return:.1%} | "
            f"{'暂无数据' if revenue_growth is None else f'{revenue_growth:.1%}'} | "
            f"{'暂无数据' if profit_margins is None else f'{profit_margins:.1%}'} | "
            f"{'暂无数据' if forward_pe is None else f'{forward_pe:.1f}'} | "
            f"{row['成交额方向估算']} | "
            f"{row['分析师共识']} | "
            f"{'暂无数据' if target_upside is None else f'{target_upside:.1%}'} | "
            f"{row['基础风险等级']} |\n"
        )

    return "# 股票对比报告\n\n" + header + divider + body + "\n> 这份报告是学习和研究用途，不构成投资建议。\n"


def _read_optional_file(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def build_business_signal_summary(
    symbol: str | None,
    company_name: str | None,
    earnings_call_file: str | None,
    meeting_file: str | None,
    tenk_file: str | None,
    raw_keywords: str | None,
    auto_research: bool = False,
) -> str:
    documents = [
        SourceDocument("earnings_call", _read_optional_file(earnings_call_file)),
        SourceDocument("meeting", _read_optional_file(meeting_file)),
        SourceDocument("tenk", _read_optional_file(tenk_file)),
    ]
    notes: list[str] = []
    if auto_research and symbol:
        public_result = fetch_public_documents(symbol, company_name)
        documents.extend(public_result.documents)
        notes.extend(public_result.notes)

    return analyze_business_signals(documents, parse_keywords(raw_keywords), notes)


def build_business_signal_section(
    symbol: str | None,
    company_name: str | None,
    earnings_call_file: str | None,
    meeting_file: str | None,
    tenk_file: str | None,
    raw_keywords: str | None,
    auto_research: bool = False,
) -> str:
    signal_summary = build_business_signal_summary(
        symbol,
        company_name,
        earnings_call_file,
        meeting_file,
        tenk_file,
        raw_keywords,
        auto_research,
    )
    return format_business_signal_report(signal_summary)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a simple Chinese stock analysis report.")
    parser.add_argument("symbols", nargs="+", help="Stock tickers, for example AAPL NVDA TSLA or AAPL,NVDA,TSLA")
    parser.add_argument("--earnings-call-file", help="Text file with recent earnings call notes or transcript")
    parser.add_argument("--meeting-file", help="Text file with recent meeting notes")
    parser.add_argument("--tenk-file", help="Text file with recent 10-K notes or text")
    parser.add_argument("--keywords", help="Comma-separated keywords to count")
    parser.add_argument("--auto-research", action="store_true", help="Automatically fetch public news and SEC filings")
    parser.add_argument(
        "--market",
        choices=["auto", "us", "cn", "hk"],
        default="auto",
        help="Market used to normalize symbols: auto, us, cn, hk",
    )
    args = parser.parse_args()

    symbols = parse_symbols(args.symbols, args.market)
    if not symbols:
        raise ValueError("请至少输入一个股票代码。")

    comparison_rows = []
    for symbol in symbols:
        snapshot = fetch_stock_snapshot(symbol)
        summary = summarize_stock(snapshot)
        report = build_report(summary)
        business_signal_summary = build_business_signal_summary(
            symbol,
            summary.company_name,
            args.earnings_call_file,
            args.meeting_file,
            args.tenk_file,
            args.keywords,
            args.auto_research,
        )
        previous_snapshot = load_last_snapshot(symbol)
        report += "\n" + format_buy_checklist(summary)
        report += "\n" + format_financial_metrics(fetch_financial_metrics(symbol))
        report += "\n" + format_history_comparison(summary, previous_snapshot, business_signal_summary)
        business_signal_section = format_business_signal_report(business_signal_summary)
        if business_signal_section:
            report += "\n" + business_signal_section
        output_path = save_report(symbol, report)
        save_snapshot(summary, business_signal_summary)
        comparison_rows.append(comparison_row(summary))

        print(report)
        print(f"\nReport saved to: {output_path}\n")

    if len(comparison_rows) > 1:
        comparison_report = build_comparison_report(comparison_rows)
        comparison_report += "\n" + format_industry_ranking(comparison_rows)
        comparison_path = save_report("comparison", comparison_report)
        print(comparison_report)
        print(f"\nComparison report saved to: {comparison_path}")


if __name__ == "__main__":
    main()
