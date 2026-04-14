from __future__ import annotations

import pandas as pd
import streamlit as st

from eco_damage_monitor.analytics.reporting import AnalyticsService
from eco_damage_monitor.config import load_settings
from eco_damage_monitor.nlp.vector_search import VectorSearchEngine
from eco_damage_monitor.storage.database import Database


def run_dashboard() -> None:
    _, app_config, _, _ = load_settings()
    db = Database(app_config.db_url)
    db.init_db()
    rows = db.fetch_documents()
    analytics = AnalyticsService(rows)
    df = pd.DataFrame(rows)

    st.set_page_config(page_title="生态破坏监测面板", layout="wide")
    st.title("广域生态破坏公开网络信息分析面板")
    st.metric("文档总数", len(rows))

    st.subheader("数据采集状态")
    if df.empty:
        st.info("当前数据库暂无数据。")
        return
    st.dataframe(df[["title", "source_type", "province", "publish_time", "relevance_score"]].head(20))

    st.subheader("关键词检索")
    keyword = st.text_input("输入关键词")
    if keyword:
        st.dataframe(df[df["title"].str.contains(keyword, na=False) | df["content"].str.contains(keyword, na=False)])

    st.subheader("语义检索")
    query = st.text_input("输入语义检索问题")
    if query:
        engine = VectorSearchEngine()
        engine.index(rows)
        st.dataframe(pd.DataFrame(engine.search(query)))

    st.subheader("时间趋势")
    time_df = pd.DataFrame(analytics.time_series())
    if not time_df.empty:
        st.line_chart(time_df.set_index("date"))

    st.subheader("地区分布")
    region_df = pd.DataFrame(analytics.map_aggregation())
    if not region_df.empty:
        st.dataframe(region_df)

    st.subheader("主题聚类")
    topic_df = pd.DataFrame(analytics.topic_evolution())
    if not topic_df.empty:
        st.dataframe(topic_df)

    st.subheader("典型文本查看")
    selected = st.selectbox("选择文档", df["title"].tolist())
    record = df[df["title"] == selected].iloc[0].to_dict()
    st.write(record.get("content"))

    st.subheader("高影响案例列表")
    st.dataframe(pd.DataFrame(analytics.high_impact_cases()))

    st.subheader("地图聚合结果预览")
    st.dataframe(region_df)
