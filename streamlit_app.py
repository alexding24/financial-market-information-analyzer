from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from analysis.ai_report import build_report
from analysis.business_signals import (
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
from app import build_comparison_report, parse_symbols, save_report
from data.financial_tables import fetch_financial_metrics, format_financial_metrics
from data.market_symbols import MARKET_OPTIONS
from data.public_documents import fetch_public_documents
from data.stock_data import fetch_stock_snapshot
from data.ticker_search import suggest_tickers, ticker_from_suggestion
from yfinance.exceptions import YFRateLimitError


st.set_page_config(page_title="金融市场信息分析助手", layout="centered")

st.title("金融市场信息分析助手")


def _replace_last_symbol(raw_text: str, symbol: str) -> str:
    parts = [part.strip() for part in raw_text.split(",")]
    if not parts:
        return symbol
    parts[-1] = symbol
    return ", ".join(part for part in parts if part)


def _manual_documents() -> list[SourceDocument]:
    return [
        SourceDocument("earnings_call", earnings_call_text),
        SourceDocument("meeting", meeting_text),
        SourceDocument("tenk", tenk_text),
    ]


def _build_document_only_report(symbol: str, reason: str) -> tuple[str, str]:
    documents = _manual_documents()
    notes = [f"{symbol}: 行情数据暂时不可用，已切换为公开材料分析模式。原因：{reason}"]
    if auto_research:
        public_result = fetch_public_documents(symbol, symbol)
        documents.extend(public_result.documents)
        notes.extend(public_result.notes)

    signal_summary = analyze_business_signals(
        documents,
        parse_keywords(keywords_text),
        notes,
    )
    signal_section = format_business_signal_report(signal_summary)
    report = f"""# {symbol} 公开材料分析报告

## 数据状态

行情数据源暂时限流或不可用，所以本次先跳过价格走势、资金流、估值和分析师评级。

这个报告仍会尽量根据 earnings call、meeting、10-K、SEC 文件和新闻摘要分析公司业务动向。
"""
    if signal_section:
        report += "\n" + signal_section
    else:
        report += "\n## 业务信号分析\n\n暂时没有足够公开材料可分析。可以展开上面的输入框，手动粘贴 earnings call、meeting 或 10-K 摘要后再生成。\n"

    output_path = save_report(symbol, report)
    return report, str(output_path)


def _set_optional_api_key(env_name: str, value: str) -> None:
    clean_value = value.strip()
    if clean_value:
        os.environ[env_name] = clean_value


def _set_optional_env(env_name: str, value: str) -> None:
    os.environ[env_name] = value.strip()


market_label = st.selectbox("市场", list(MARKET_OPTIONS.keys()), index=0)
market = MARKET_OPTIONS[market_label]
symbols_text = st.text_input("输入股票代码", value="NVDA", placeholder="例如 AAPL, NVDA, TSLA")
suggestions = suggest_tickers(symbols_text.split(",")[-1].strip())
if suggestions:
    selected_suggestion = st.selectbox("你是不是想搜这个", ["不使用提示"] + suggestions)
    if selected_suggestion != "不使用提示":
        symbols_text = _replace_last_symbol(symbols_text, ticker_from_suggestion(selected_suggestion))
auto_research = st.checkbox("自动搜索公开材料", value=True)

with st.expander("可选：免费数据源 API key"):
    provider_options = {
        "Financial Modeling Prep": "fmp",
        "Finnhub": "finnhub",
        "Alpha Vantage": "alpha_vantage",
        "EODHD": "eodhd",
        "Twelve Data": "twelve_data",
        "SEC EDGAR 官方财报": "sec",
        "AkShare A股/港股": "akshare",
        "自定义 API": "custom",
    }
    selected_providers = st.multiselect(
        "选择要使用的数据源",
        list(provider_options.keys()),
        default=["SEC EDGAR 官方财报", "Financial Modeling Prep", "Finnhub", "Alpha Vantage", "EODHD"],
    )
    os.environ["FREE_DATA_PROVIDERS"] = ",".join(provider_options[name] for name in selected_providers)
    fmp_api_key = st.text_input("Financial Modeling Prep API key", type="password")
    finnhub_api_key = st.text_input("Finnhub API key", type="password")
    alpha_vantage_api_key = st.text_input("Alpha Vantage API key", type="password")
    eodhd_api_key = st.text_input("EODHD API key", type="password")
    twelve_data_api_key = st.text_input("Twelve Data API key", type="password")
    custom_api_url = st.text_input(
        "自定义 API URL 模板",
        placeholder="例如 https://example.com/api?symbol={symbol}&apikey={api_key}",
    )
    custom_api_key = st.text_input("自定义 API key", type="password")
    _set_optional_api_key("FMP_API_KEY", fmp_api_key)
    _set_optional_api_key("FINNHUB_API_KEY", finnhub_api_key)
    _set_optional_api_key("ALPHA_VANTAGE_API_KEY", alpha_vantage_api_key)
    _set_optional_api_key("EODHD_API_KEY", eodhd_api_key)
    _set_optional_api_key("TWELVE_DATA_API_KEY", twelve_data_api_key)
    _set_optional_env("CUSTOM_FINANCIAL_API_URL", custom_api_url)
    _set_optional_api_key("CUSTOM_FINANCIAL_API_KEY", custom_api_key)

with st.expander("可选：加入 earnings call、meeting、10-K 业务信号分析"):
    earnings_call_text = st.text_area("最近 earnings call 摘要或文字", height=120)
    meeting_text = st.text_area("最近 meeting / investor day 摘要或文字", height=120)
    tenk_text = st.text_area("最近 10-K 摘要或关键段落", height=120)
    keywords_text = st.text_area(
        "要统计的关键词",
        value="AI, data center, cloud, GPU, demand, margin, inventory, capex, guidance, competition, China",
        height=80,
    )

if st.button("生成分析报告", type="primary"):
    symbols = parse_symbols([symbols_text], market)
    if not symbols:
        st.warning("请先输入至少一个股票代码。")
    else:
        try:
            with st.spinner("正在读取数据并生成报告..."):
                reports = []
                comparison_rows = []
                for symbol in symbols:
                    try:
                        snapshot = fetch_stock_snapshot(symbol)
                    except (YFRateLimitError, ValueError) as exc:
                        report, output_path = _build_document_only_report(symbol, str(exc))
                        reports.append((symbol, report, output_path))
                        continue

                    summary = summarize_stock(snapshot)
                    report = build_report(summary)
                    documents = _manual_documents()
                    notes = []
                    if auto_research:
                        public_result = fetch_public_documents(symbol, summary.company_name)
                        documents.extend(public_result.documents)
                        notes.extend(public_result.notes)
                    business_signal_summary = analyze_business_signals(
                        documents,
                        parse_keywords(keywords_text),
                        notes,
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
                    reports.append((symbol, report, output_path))
                    comparison_rows.append(comparison_row(summary))

                if len(comparison_rows) > 1:
                    comparison_report = build_comparison_report(comparison_rows)
                    comparison_report += "\n" + format_industry_ranking(comparison_rows)
                    save_report("comparison", comparison_report)
        except YFRateLimitError:
            st.error("公开行情数据源暂时限流了。请等几分钟再试，或者先关闭“自动搜索公开材料”后重试。")
            st.stop()
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        except Exception as exc:
            st.error(f"生成报告时遇到问题：{exc}")
            st.stop()

        st.success("报告已生成。")

        if len(comparison_rows) > 1:
            st.subheader("股票对比")
            comparison_df = pd.DataFrame(comparison_rows)
            st.dataframe(
                comparison_df,
                hide_index=True,
                column_config={
                    "市值": st.column_config.NumberColumn("市值", format="compact"),
                    "收入增长": st.column_config.NumberColumn("收入增长", format="percent"),
                    "利润率": st.column_config.NumberColumn("利润率", format="percent"),
                    "近六个月涨跌幅": st.column_config.NumberColumn("近六个月涨跌幅", format="percent"),
                    "过去市盈率": st.column_config.NumberColumn("过去市盈率", format="%.1f"),
                    "未来市盈率": st.column_config.NumberColumn("未来市盈率", format="%.1f"),
                    "目标价空间": st.column_config.NumberColumn("目标价空间", format="percent"),
                },
            )
            ranking = format_industry_ranking(comparison_rows)
            if ranking:
                st.markdown(ranking)

        for symbol, report, output_path in reports:
            st.caption(f"{symbol} 报告已保存：{output_path}")
            st.markdown(report)
