from __future__ import annotations

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


market_label = st.selectbox("市场", list(MARKET_OPTIONS.keys()), index=0)
market = MARKET_OPTIONS[market_label]
symbols_text = st.text_input("输入股票代码", value="NVDA", placeholder="例如 AAPL, NVDA, TSLA")
suggestions = suggest_tickers(symbols_text.split(",")[-1].strip())
if suggestions:
    selected_suggestion = st.selectbox("你是不是想搜这个", ["不使用提示"] + suggestions)
    if selected_suggestion != "不使用提示":
        symbols_text = _replace_last_symbol(symbols_text, ticker_from_suggestion(selected_suggestion))
auto_research = st.checkbox("自动搜索公开材料", value=True)

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
                    snapshot = fetch_stock_snapshot(symbol)
                    summary = summarize_stock(snapshot)
                    report = build_report(summary)
                    documents = [
                        SourceDocument("earnings_call", earnings_call_text),
                        SourceDocument("meeting", meeting_text),
                        SourceDocument("tenk", tenk_text),
                    ]
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
