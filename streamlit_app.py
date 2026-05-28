from __future__ import annotations

import streamlit as st

from analysis.ai_report import build_report
from analysis.stock_summary import summarize_stock
from app import save_report
from data.stock_data import fetch_stock_snapshot


st.set_page_config(page_title="金融市场信息分析助手", layout="centered")

st.title("金融市场信息分析助手")

symbol = st.text_input("输入股票代码", value="NVDA", placeholder="例如 AAPL, NVDA, TSLA")

if st.button("生成分析报告", type="primary"):
    clean_symbol = symbol.upper().strip()
    if not clean_symbol:
        st.warning("请先输入一个股票代码。")
    else:
        with st.spinner("正在读取数据并生成报告..."):
            snapshot = fetch_stock_snapshot(clean_symbol)
            summary = summarize_stock(snapshot)
            report = build_report(summary)
            output_path = save_report(clean_symbol, report)

        st.success(f"报告已生成：{output_path}")
        st.markdown(report)
