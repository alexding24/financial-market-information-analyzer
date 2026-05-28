from __future__ import annotations

import argparse
import re
from pathlib import Path

from analysis.ai_report import build_report
from analysis.stock_summary import comparison_row, summarize_stock
from data.stock_data import fetch_stock_snapshot


def save_report(symbol: str, report: str) -> Path:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    output_path = reports_dir / f"{symbol.upper()}_report.md"
    output_path.write_text(report, encoding="utf-8")
    return output_path


def parse_symbols(raw_symbols: list[str]) -> list[str]:
    symbols: list[str] = []
    for raw_symbol in raw_symbols:
        for part in re.split(r"[\s,]+", raw_symbol):
            symbol = part.upper().strip()
            if symbol and symbol not in symbols:
                symbols.append(symbol)
    return symbols


def build_comparison_report(rows: list[dict[str, str | float | None]]) -> str:
    header = "| 股票代码 | 公司名称 | 行业板块 | 细分行业 | 近六个月涨跌幅 | 收入增长 | 利润率 | 未来市盈率 | 资金流向 | 分析师共识 | 目标价空间 | 风险 |\n"
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
            f"{row['资金流向']} | "
            f"{row['分析师共识']} | "
            f"{'暂无数据' if target_upside is None else f'{target_upside:.1%}'} | "
            f"{row['基础风险等级']} |\n"
        )

    return "# 股票对比报告\n\n" + header + divider + body + "\n> 这份报告是学习和研究用途，不构成投资建议。\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a simple Chinese stock analysis report.")
    parser.add_argument("symbols", nargs="+", help="Stock tickers, for example AAPL NVDA TSLA or AAPL,NVDA,TSLA")
    args = parser.parse_args()

    symbols = parse_symbols(args.symbols)
    if not symbols:
        raise ValueError("请至少输入一个股票代码。")

    comparison_rows = []
    for symbol in symbols:
        snapshot = fetch_stock_snapshot(symbol)
        summary = summarize_stock(snapshot)
        report = build_report(summary)
        output_path = save_report(symbol, report)
        comparison_rows.append(comparison_row(summary))

        print(report)
        print(f"\nReport saved to: {output_path}\n")

    if len(comparison_rows) > 1:
        comparison_report = build_comparison_report(comparison_rows)
        comparison_path = save_report("comparison", comparison_report)
        print(comparison_report)
        print(f"\nComparison report saved to: {comparison_path}")


if __name__ == "__main__":
    main()
