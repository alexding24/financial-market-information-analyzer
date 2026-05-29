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
from data.public_documents import fetch_public_documents
from data.stock_data import fetch_stock_snapshot
from data.ticker_search import suggest_tickers, ticker_from_suggestion
from data.yfinance_compat import YFRateLimitError


UI_TEXT = {
    "zh": {
        "page_title": "金融市场信息分析助手",
        "language": "语言 / Language",
        "market": "市场",
        "symbol_input": "输入股票代码",
        "symbol_placeholder": "例如 AAPL, NVDA, TSLA",
        "suggest": "你是不是想搜这个",
        "no_suggest": "不使用提示",
        "auto_research": "自动搜索公开材料",
        "api_expander": "可选：免费数据源 API key",
        "provider_select": "选择要使用的数据源",
        "custom_api_url": "自定义 API URL 模板",
        "custom_api_placeholder": "例如 https://example.com/api?symbol={symbol}&apikey={api_key}",
        "custom_api_key": "自定义 API key",
        "sec_help": "SEC 建议填写应用名和真实联系邮箱，例如 financial-market-analyzer/0.1 your@email.com",
        "docs_expander": "可选：加入 earnings call、meeting、10-K 业务信号分析",
        "earnings": "最近 earnings call 摘要或文字",
        "meeting": "最近 meeting / investor day 摘要或文字",
        "tenk": "最近 10-K 摘要或关键段落",
        "keywords": "要统计的关键词",
        "generate": "生成分析报告",
        "need_symbol": "请先输入至少一个股票代码。",
        "spinner": "正在读取数据并生成报告...",
        "rate_limit": "公开行情数据源暂时限流了。请等几分钟再试，或者先关闭“自动搜索公开材料”后重试。",
        "error": "生成报告时遇到问题：{exc}",
        "success": "报告已生成。",
        "comparison": "股票对比",
        "saved": "{symbol} 报告已保存：{path}",
    },
    "en": {
        "page_title": "Financial Market Information Analyzer",
        "language": "Language / 语言",
        "market": "Market",
        "symbol_input": "Enter tickers",
        "symbol_placeholder": "For example AAPL, NVDA, TSLA",
        "suggest": "Did you mean this ticker?",
        "no_suggest": "Do not use suggestion",
        "auto_research": "Automatically search public materials",
        "api_expander": "Optional: free data source API keys",
        "provider_select": "Select data sources",
        "custom_api_url": "Custom API URL template",
        "custom_api_placeholder": "For example https://example.com/api?symbol={symbol}&apikey={api_key}",
        "custom_api_key": "Custom API key",
        "sec_help": "SEC recommends an app name and real contact email, for example financial-market-analyzer/0.1 your@email.com",
        "docs_expander": "Optional: add earnings call, meeting, and 10-K business signal analysis",
        "earnings": "Recent earnings call summary or text",
        "meeting": "Recent meeting / investor day summary or text",
        "tenk": "Recent 10-K summary or key excerpts",
        "keywords": "Keywords to count",
        "generate": "Generate analysis report",
        "need_symbol": "Please enter at least one ticker.",
        "spinner": "Reading data and generating the report...",
        "rate_limit": "The public market data source is temporarily rate limited. Please wait a few minutes and retry, or disable automatic public-material search first.",
        "error": "Report generation failed: {exc}",
        "success": "Report generated.",
        "comparison": "Stock Comparison",
        "saved": "{symbol} report saved: {path}",
    },
}

MARKET_LABELS = {
    "zh": {"自动识别": "auto", "美股": "us", "A股": "cn", "港股": "hk"},
    "en": {"Auto detect": "auto", "US stocks": "us", "A-shares": "cn", "Hong Kong stocks": "hk"},
}

PROVIDER_LABELS = {
    "zh": {
        "Financial Modeling Prep": "fmp",
        "Finnhub": "finnhub",
        "Alpha Vantage": "alpha_vantage",
        "EODHD": "eodhd",
        "Twelve Data": "twelve_data",
        "SEC EDGAR 官方财报": "sec",
        "AkShare A股/港股": "akshare",
        "自定义 API": "custom",
    },
    "en": {
        "Financial Modeling Prep": "fmp",
        "Finnhub": "finnhub",
        "Alpha Vantage": "alpha_vantage",
        "EODHD": "eodhd",
        "Twelve Data": "twelve_data",
        "SEC EDGAR official filings": "sec",
        "AkShare A-share/HK": "akshare",
        "Custom API": "custom",
    },
}


st.set_page_config(page_title="Financial Market Information Analyzer", layout="centered")

language_label = st.selectbox("语言 / Language", ["中文", "English"], index=0)
language = "en" if language_label == "English" else "zh"
t = UI_TEXT[language]

st.title(t["page_title"])


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
    signal_section = format_business_signal_report(signal_summary, language)
    if language == "en":
        report = f"""# {symbol} Public Materials Analysis Report

## Data Status

Market data is temporarily unavailable or rate limited, so this report skips price trend, dollar-volume direction, valuation, and analyst-rating sections.

It still analyzes company business signals using earnings calls, meetings, 10-K/SEC filings, and news summaries where available.
"""
        if signal_section:
            report += "\n" + signal_section
        else:
            report += "\n## Business Signal Analysis\n\nNot enough public materials are available yet. You can paste earnings call, meeting, or 10-K text in the input area above and generate the report again.\n"
        output_path = save_report(symbol, report)
        return report, str(output_path)

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


market_labels = MARKET_LABELS[language]
market_label = st.selectbox(t["market"], list(market_labels.keys()), index=0)
market = market_labels[market_label]
symbols_text = st.text_input(t["symbol_input"], value="NVDA", placeholder=t["symbol_placeholder"])
suggestions = suggest_tickers(symbols_text.split(",")[-1].strip())
if suggestions:
    selected_suggestion = st.selectbox(t["suggest"], [t["no_suggest"]] + suggestions)
    if selected_suggestion != t["no_suggest"]:
        symbols_text = _replace_last_symbol(symbols_text, ticker_from_suggestion(selected_suggestion))
auto_research = st.checkbox(t["auto_research"], value=True)

with st.expander(t["api_expander"]):
    provider_options = PROVIDER_LABELS[language]
    default_providers = [
        name
        for name, provider in provider_options.items()
        if provider in {"sec", "fmp", "finnhub", "alpha_vantage", "eodhd"}
    ]
    selected_providers = st.multiselect(
        t["provider_select"],
        list(provider_options.keys()),
        default=default_providers,
    )
    os.environ["FREE_DATA_PROVIDERS"] = ",".join(provider_options[name] for name in selected_providers)
    fmp_api_key = st.text_input("Financial Modeling Prep API key", type="password")
    finnhub_api_key = st.text_input("Finnhub API key", type="password")
    alpha_vantage_api_key = st.text_input("Alpha Vantage API key", type="password")
    eodhd_api_key = st.text_input("EODHD API key", type="password")
    twelve_data_api_key = st.text_input("Twelve Data API key", type="password")
    custom_api_url = st.text_input(
        t["custom_api_url"],
        placeholder=t["custom_api_placeholder"],
    )
    custom_api_key = st.text_input(t["custom_api_key"], type="password")
    sec_user_agent = st.text_input(
        "SEC User-Agent",
        value=os.getenv("SEC_USER_AGENT", "financial-market-analyzer/0.1 research@example.com"),
        help=t["sec_help"],
    )
    _set_optional_api_key("FMP_API_KEY", fmp_api_key)
    _set_optional_api_key("FINNHUB_API_KEY", finnhub_api_key)
    _set_optional_api_key("ALPHA_VANTAGE_API_KEY", alpha_vantage_api_key)
    _set_optional_api_key("EODHD_API_KEY", eodhd_api_key)
    _set_optional_api_key("TWELVE_DATA_API_KEY", twelve_data_api_key)
    _set_optional_env("CUSTOM_FINANCIAL_API_URL", custom_api_url)
    _set_optional_api_key("CUSTOM_FINANCIAL_API_KEY", custom_api_key)
    _set_optional_env("SEC_USER_AGENT", sec_user_agent)

with st.expander(t["docs_expander"]):
    earnings_call_text = st.text_area(t["earnings"], height=120)
    meeting_text = st.text_area(t["meeting"], height=120)
    tenk_text = st.text_area(t["tenk"], height=120)
    keywords_text = st.text_area(
        t["keywords"],
        value="AI, data center, cloud, GPU, demand, margin, inventory, capex, guidance, competition, China",
        height=80,
    )

if st.button(t["generate"], type="primary"):
    symbols = parse_symbols([symbols_text], market)
    if not symbols:
        st.warning(t["need_symbol"])
    else:
        try:
            with st.spinner(t["spinner"]):
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
                    report = build_report(summary, language)
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
                    report += "\n" + format_buy_checklist(summary, language)
                    report += "\n" + format_financial_metrics(fetch_financial_metrics(symbol), language)
                    report += "\n" + format_history_comparison(summary, previous_snapshot, business_signal_summary, language)
                    business_signal_section = format_business_signal_report(business_signal_summary, language)
                    if business_signal_section:
                        report += "\n" + business_signal_section
                    output_path = save_report(symbol, report)
                    save_snapshot(summary, business_signal_summary)
                    reports.append((symbol, report, output_path))
                    comparison_rows.append(comparison_row(summary))

                if len(comparison_rows) > 1:
                    comparison_report = build_comparison_report(comparison_rows, language)
                    comparison_report += "\n" + format_industry_ranking(comparison_rows, language)
                    save_report("comparison", comparison_report)
        except YFRateLimitError:
            st.error(t["rate_limit"])
            st.stop()
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        except Exception as exc:
            st.error(t["error"].format(exc=exc))
            st.stop()

        st.success(t["success"])

        if len(comparison_rows) > 1:
            st.subheader(t["comparison"])
            comparison_df = pd.DataFrame(comparison_rows)
            st.dataframe(
                comparison_df,
                hide_index=True,
                column_config={
                    "市值": st.column_config.NumberColumn("市值" if language == "zh" else "Market cap", format="compact"),
                    "收入增长": st.column_config.NumberColumn("收入增长" if language == "zh" else "Revenue growth", format="percent"),
                    "利润率": st.column_config.NumberColumn("利润率" if language == "zh" else "Profit margin", format="percent"),
                    "近六个月涨跌幅": st.column_config.NumberColumn("近六个月涨跌幅" if language == "zh" else "Six-month return", format="percent"),
                    "过去市盈率": st.column_config.NumberColumn("过去市盈率" if language == "zh" else "Trailing P/E", format="%.1f"),
                    "未来市盈率": st.column_config.NumberColumn("未来市盈率" if language == "zh" else "Forward P/E", format="%.1f"),
                    "目标价空间": st.column_config.NumberColumn("目标价空间" if language == "zh" else "Target upside", format="percent"),
                },
            )
            ranking = format_industry_ranking(comparison_rows, language)
            if ranking:
                st.markdown(ranking)

        for symbol, report, output_path in reports:
            st.caption(t["saved"].format(symbol=symbol, path=output_path))
            st.markdown(report)
