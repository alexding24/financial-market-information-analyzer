from __future__ import annotations

import argparse
from pathlib import Path

from analysis.ai_report import build_report
from analysis.stock_summary import summarize_stock
from data.stock_data import fetch_stock_snapshot


def save_report(symbol: str, report: str) -> Path:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    output_path = reports_dir / f"{symbol.upper()}_report.md"
    output_path.write_text(report, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a simple Chinese stock analysis report.")
    parser.add_argument("symbol", help="Stock ticker, for example AAPL, NVDA, TSLA")
    args = parser.parse_args()

    symbol = args.symbol.upper().strip()
    snapshot = fetch_stock_snapshot(symbol)
    summary = summarize_stock(snapshot)
    report = build_report(summary)
    output_path = save_report(symbol, report)

    print(report)
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
