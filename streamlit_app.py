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
from analysis.stock_summary import comparison_row, summarize_stock
from app import build_comparison_report, parse_symbols, save_report
from data.stock_data import fetch_stock_snapshot


st.set_page_config(page_title="金融市场信息分析助手", layout="centered")

st.title("金融市场信息分析助手")

symbols_text = st.text_input("输入股票代码", value="NVDA", placeholder="例如 AAPL, NVDA, TSLA")

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
    symbols = parse_symbols([symbols_text])
    if not symbols:
        st.warning("请先输入至少一个股票代码。")
    else:
        with st.spinner("正在读取数据并生成报告..."):
            reports = []
            comparison_rows = []
            business_signal_summary = analyze_business_signals(
                [
                    SourceDocument("earnings_call", earnings_call_text),
                    SourceDocument("meeting", meeting_text),
                    SourceDocument("tenk", tenk_text),
                ],
                parse_keywords(keywords_text),
            )
            business_signal_section = format_business_signal_report(business_signal_summary)
            for symbol in symbols:
                snapshot = fetch_stock_snapshot(symbol)
                summary = summarize_stock(snapshot)
                report = build_report(summary)
                if business_signal_section:
                    report += "\n" + business_signal_section
                output_path = save_report(symbol, report)
                reports.append((symbol, report, output_path))
                comparison_rows.append(comparison_row(summary))

            if len(comparison_rows) > 1:
                comparison_report = build_comparison_report(comparison_rows)
                save_report("comparison", comparison_report)

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

        for symbol, report, output_path in reports:
            st.caption(f"{symbol} 报告已保存：{output_path}")
            st.markdown(report)
