"""数据可视化模块。

包含全部 Plotly 图表(时序折线、情感饼图、竞品对比、相关性探针、
热力图、移动平均、语义聚类)与词云、高赞评论卡片的渲染逻辑。

所有图表统一引用 ``ui_components.SENTIMENT_COLOR_MAP`` 语义配色,
并通过 ``ui_components.apply_plotly_theme`` 应用学术风暗色主题。
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from .sentiment import contains_chinese
from .ui_components import (
    SENTIMENT_COLOR_MAP,
    apply_plotly_theme,
    render_quote_card,
    render_section_title,
)


# ============================================================
# 主舆情大屏
# ============================================================
def render_dashboard(df: pd.DataFrame) -> None:
    """舆情大屏:日度时序波动 + 整体情绪分布占比。"""
    col1, col2 = st.columns([2, 1])

    with col1:
        render_section_title("📈 舆情数量时序波动(日)")
        trend_daily = df.groupby("date", as_index=False).size().rename(columns={"size": "comment_count"})

        fig_line = px.line(
            trend_daily,
            x="date",
            y="comment_count",
            markers=True,
            color_discrete_sequence=["#8b5cf6"],
        )
        fig_line.update_traces(line=dict(width=3), marker=dict(size=8, symbol="circle"))
        apply_plotly_theme(fig_line)
        st.plotly_chart(fig_line, use_container_width=True)

    with col2:
        render_section_title("🍩 整体情绪分布占比")
        sentiment_dist = (
            df.groupby("sentiment", as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )
        fig_pie = px.pie(
            sentiment_dist,
            names="sentiment",
            values="count",
            hole=0.55,
            color="sentiment",
            color_discrete_map=SENTIMENT_COLOR_MAP,
        )
        apply_plotly_theme(fig_pie)
        st.plotly_chart(fig_pie, use_container_width=True)


# ============================================================
# 竞品 / 多关键词对比
# ============================================================
def plot_competitive_keywords(df: pd.DataFrame) -> None:
    """竞品与关键词维度多维对比分析。"""
    if "keyword" not in df.columns or df["keyword"].nunique() <= 1:
        render_section_title("⚔️ 多维竞品对比透视")
        st.info("💡 竞品对比分析激活中:当前抓取任务仅包含单个关键词。若要激活本分析模块,请在侧边栏中配置多个关键词(如:'特斯拉, 比亚迪, 小米汽车' 逗号分隔)。")
        return

    render_section_title("⚔️ 多维竞品对比透视")

    stats = df.groupby("keyword").agg(
        total_comments=("comment_id", "count"),
        avg_sentiment=("sentiment_score", "mean"),
        avg_likes=("like_count", "mean"),
    ).reset_index()

    sentiment_ratios = df.groupby(["keyword", "sentiment"]).size().unstack(fill_value=0)
    sentiment_ratios_pct = sentiment_ratios.div(sentiment_ratios.sum(axis=1), axis=0) * 100
    sentiment_ratios_pct = sentiment_ratios_pct.reset_index()
    melted_ratios = sentiment_ratios_pct.melt(id_vars="keyword", var_name="sentiment", value_name="percentage")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            stats,
            x="keyword",
            y="total_comments",
            color="avg_sentiment",
            color_continuous_scale="Viridis",
            title="各竞品评论声量(柱高)与平均情绪指数(颜色偏黄表示积极)",
            labels={"total_comments": "评论总量", "avg_sentiment": "平均情绪得分"},
        )
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(
            melted_ratios,
            x="keyword",
            y="percentage",
            color="sentiment",
            barmode="group",
            title="竞品核心情感分布占比",
            color_discrete_map=SENTIMENT_COLOR_MAP,
            labels={"percentage": "占比百分比 (%)", "sentiment": "情绪属性"},
        )
        apply_plotly_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)


# ============================================================
# 点赞 / 文本长度 相关性探针
# ============================================================
def plot_engagement_correlation(df: pd.DataFrame) -> None:
    """用户点赞交互数与评论文本字数的相关性深度探针 (Pearson r)。"""
    render_section_title("🔍 用户点赞数与评论文本长度的相关性探针")

    df_copy = df.copy()
    df_copy["comment_length"] = df_copy["comment_text"].str.len()

    corr = df_copy["comment_length"].corr(df_copy["like_count"])
    if pd.isna(corr):
        corr = 0.0

    if abs(corr) < 0.1:
        interpretation = "极弱或近乎无线性相关关系"
        color = "#94a3b8"
    elif abs(corr) < 0.3:
        interpretation = "弱度线性正相关" if corr > 0 else "弱度线性负相关"
        color = "#fbbf24"
    else:
        interpretation = "中等至强度线性正相关" if corr > 0 else "中等至强度线性负相关"
        color = "#10b981"

    c1, c2 = st.columns([1, 2.5])
    with c1:
        st.markdown(
            f"""
            <div class="metric-card" style="margin-top: 15px;">
                <div class="metric-title">皮尔逊相关系数 r</div>
                <div class="metric-value" style="color: {color}; font-size: 38px;">{corr:.4f}</div>
                <div class="metric-subtitle" style="font-weight: 600; color: {color}; font-size:13px; margin-top:8px;">结论:{interpretation}</div>
                <p style="font-size: 12px; color: #64748b; margin-top: 15px; line-height: 1.6;">
                    皮尔逊相关系数用来衡量两个变量的线性关联强度,范围在 [-1, 1]:<br/>
                    • <b>r > 0</b>: 评论越长,获得点赞越多(可能长文更有逻辑)。<br/>
                    • <b>r < 0</b>: 评论越短,点赞数越多(可能短评梗词更吸睛)。<br/>
                    • <b>r 趋于 0</b>: 长度与点赞无显著关联。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        q_like = df_copy["like_count"].quantile(0.98)
        scatter_data = df_copy[df_copy["like_count"] <= max(q_like, 15)]

        fig = px.scatter(
            scatter_data,
            x="comment_length",
            y="like_count",
            color="sentiment",
            size=scatter_data["like_count"].apply(lambda v: max(v, 3)),
            hover_data=["author", "comment_text"],
            title="评论字符字数 vs 获得点赞数(已剔除极端尖峰值)",
            color_discrete_map=SENTIMENT_COLOR_MAP,
            labels={
                "comment_length": "评论字符长度 (Chars)",
                "like_count": "点赞数 (Likes)",
                "sentiment": "情感",
            },
        )
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 时段密度热力图
# ============================================================
def plot_temporal_heatmap(df: pd.DataFrame) -> None:
    """舆情时段密度活跃度热力图(周几 vs 一天的小时)。"""
    render_section_title("📅 舆情活动周/时密度热力透视")

    df_copy = df.copy()
    df_copy["published_at"] = pd.to_datetime(df_copy["published_at"], utc=True)
    df_copy["hour"] = df_copy["published_at"].dt.hour
    df_copy["day_of_week"] = df_copy["published_at"].dt.day_name()

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_cn = {
        "Monday": "周一 (Mon)", "Tuesday": "周二 (Tue)", "Wednesday": "周三 (Wed)",
        "Thursday": "周四 (Thu)", "Friday": "周五 (Fri)", "Saturday": "周六 (Sat)", "Sunday": "周日 (Sun)",
    }

    heatmap_data = df_copy.groupby(["day_of_week", "hour"]).size().unstack(fill_value=0)
    heatmap_data = heatmap_data.reindex(weekday_order, fill_value=0)
    # 确保列覆盖 0-23 全部 24 小时,与 px.imshow 的 x=list(range(24)) 对齐
    heatmap_data = heatmap_data.reindex(columns=range(24), fill_value=0)
    heatmap_data.index = [weekday_cn[d] for d in heatmap_data.index]

    fig = px.imshow(
        heatmap_data,
        labels=dict(x="一天中的小时 (Hour of Day)", y="星期 (Day of Week)", color="评论活跃数"),
        x=list(range(24)),
        y=heatmap_data.index.tolist(),
        color_continuous_scale="Viridis",
        title="舆情发帖活动密度分布(发现用户发声最密集的时间窗口)",
    )
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    flat_data = df_copy.groupby(["day_of_week", "hour"]).size().reset_index(name="count")
    if not flat_data.empty:
        peak = flat_data.loc[flat_data["count"].idxmax()]
        day_cn = weekday_cn[peak["day_of_week"]].split(" ")[0]
        st.markdown(
            f"""
            💡 **危机公关监控建议**:监测显示,本项任务中最密集的互动爆发时段位于 **{day_cn} 的 {peak['hour']}:00 - {peak['hour']+1}:00** (爆发了 **{peak['count']}** 条评论)。
            建议品牌公关团队在该活跃窗口期**增强巡检,对发帖高度集中的舆论倾向进行秒级防范**。
            """
        )


# ============================================================
# 情感移动平均衰减线
# ============================================================
def plot_rolling_sentiment(df: pd.DataFrame) -> None:
    """情感时序移动平均衰减走势(舆情平息/复苏/恶化趋势)。"""
    render_section_title("📈 情感移动平均时序衰减线 (舆情恶化/修复曲线)")

    df_sorted = df.sort_values("published_at").copy()
    window_size = max(10, int(len(df_sorted) * 0.05))
    df_sorted["rolling_sentiment"] = df_sorted["sentiment_score"].rolling(window=window_size, min_periods=5).mean()

    fig = px.line(
        df_sorted,
        x="published_at",
        y="rolling_sentiment",
        title=f"时间轴平滑情感轨迹线 (滑动平均窗口:前 {window_size} 条评论)",
        color_discrete_sequence=["#8b5cf6"],
    )

    fig.add_shape(
        type="line",
        x0=df_sorted["published_at"].min(),
        y0=0.5,
        x1=df_sorted["published_at"].max(),
        y1=0.5,
        line=dict(color="rgba(244,63,94,0.35)", width=2, dash="dash"),
    )
    fig.add_annotation(
        x=df_sorted["published_at"].max(),
        y=0.52,
        text="中立情感红线 (0.50)",
        showarrow=False,
        font=dict(color="rgba(244,63,94,0.6)", size=10),
    )

    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    if len(df_sorted) > window_size * 2:
        start_sentiment = df_sorted["rolling_sentiment"].iloc[window_size: window_size * 2].mean()
        end_sentiment = df_sorted["rolling_sentiment"].iloc[-window_size:].mean()
        delta = end_sentiment - start_sentiment

        if delta > 0.05:
            st.markdown("📈 **舆情态势研判:正向回暖!** 移动窗口中评论情感值呈现明确上扬趋势,说明负面情绪正在平息,公关危机得到阶段性控制。")
        elif delta < -0.05:
            st.markdown("📉 **舆情态势研判:负向恶化!** 近期情绪表现出明显的下滑趋势。网民负向情绪在淤积且无好转迹象,可能存在第二波舆情次生灾害风险,需紧急干预!")
        else:
            st.markdown("📊 **舆情态势研判:震荡僵持。** 滑动情感得分平稳,代表网民态度对立中和,舆论热点正处于稳步消耗阶段。")


# ============================================================
# 语义聚类 (TF-IDF + K-Means + PCA)
# ============================================================
def plot_semantic_clustering(df: pd.DataFrame) -> None:
    """使用 TF-IDF + K-Means + PCA 进行评论的主题聚类与降维可视化。"""
    render_section_title("🔮 评论语义聚类与学术话题阵营提炼")

    comments = df["comment_text"].dropna().astype(str).tolist()
    if len(comments) < 15:
        st.info("💡 聚类分析激活条件:当前抓取的评论样本过少(少于 15 条),建议在侧边栏增大采样深度后再体验机器学习聚类功能。")
        return

    st.markdown(
        """
        利用机器学习非监督算法将网民评论转化为高维 TF-IDF 语义向量,通过 **K-Means** 聚类划分为不同的"话题阵营",最后使用 **主成分分析 (PCA)** 将高维空间降维投影至二维,实现公众讨论焦点的科学聚类分布透视。
        """
    )

    n_clusters = st.slider("选择话题聚类簇数 (K)", min_value=2, max_value=6, value=4, help="K 代表网民发言主要集中的对立或发散的话题阵营数")

    with st.spinner("正在进行 TF-IDF 向量化与 K-Means 聚类运算..."):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.cluster import KMeans
            from sklearn.decomposition import PCA
            import jieba

            tokenized_comments = []
            for comment in comments:
                if contains_chinese(comment):
                    words = jieba.cut(comment)
                    words_filtered = [w.strip() for w in words if len(w.strip()) > 1]
                    tokenized_comments.append(" ".join(words_filtered))
                else:
                    tokenized_comments.append(comment.lower())

            vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(tokenized_comments)

            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
            cluster_labels = kmeans.fit_predict(tfidf_matrix)

            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(tfidf_matrix.toarray())

            plot_data = df.copy()
            plot_data["x"] = coords[:, 0]
            plot_data["y"] = coords[:, 1]
            plot_data["cluster"] = [f"Topic {label + 1}" for label in cluster_labels]
            plot_data["comment_preview"] = plot_data["comment_text"].apply(lambda t: t[:80] + "..." if len(t) > 80 else t)

            terms = vectorizer.get_feature_names_out()
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]

            cluster_keywords = {}
            for i in range(n_clusters):
                top_terms = [terms[ind] for ind in order_centroids[i, :5]]
                cluster_keywords[f"Topic {i + 1}"] = top_terms

            col1, col2 = st.columns([2.5, 1])

            with col1:
                fig = px.scatter(
                    plot_data,
                    x="x",
                    y="y",
                    color="cluster",
                    size=plot_data["like_count"].apply(lambda v: max(v, 4)),
                    hover_data=["author", "like_count", "comment_preview", "sentiment"],
                    title=f"评论语义高维映射与 PCA 2D 投影图 (聚类簇 K={n_clusters})",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig.update_traces(marker=dict(opacity=0.75, line=dict(width=1, color="rgba(255,255,255,0.15)")))
                apply_plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("##### 🔑 各话题阵营高频语义特征")
                cluster_colors = px.colors.qualitative.Pastel
                for i in range(n_clusters):
                    topic_name = f"Topic {i + 1}"
                    kw_list = cluster_keywords[topic_name]
                    kw_tags_html = " ".join([
                        f"<span style='background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); "
                        f"border-radius: 6px; padding: 2px 8px; margin-right: 6px; display: inline-block; "
                        f"margin-bottom: 6px; font-size:12px; color:#cbd5e1;'>🏷️ {kw}</span>"
                        for kw in kw_list
                    ])

                    topic_subset = plot_data[plot_data["cluster"] == topic_name]
                    avg_score = topic_subset["sentiment_score"].mean()
                    total_pct = len(topic_subset) / len(plot_data) * 100
                    score_color = "#10b981" if avg_score >= 0.55 else ("#ef4444" if avg_score <= 0.45 else "#64748b")

                    st.markdown(
                        f"""
                        <div class="metric-card" style="padding: 16px; border-left: 4px solid {cluster_colors[i % len(cluster_colors)]}; margin-bottom: 12px;">
                            <div class="metric-title" style="font-size:12px; color:#cbd5e1; font-weight:700;">🗣️ 话题阵营 {i + 1} ({total_pct:.1f}%)</div>
                            <div style="margin-top: 8px; margin-bottom: 10px;">
                                {kw_tags_html}
                            </div>
                            <div style="font-size: 11px; color:#94a3b8;">
                                情感倾向度均值:<b style="color: {score_color}">{avg_score:.2f}</b> (0代表极端消极, 1代表极端积极)
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.divider()
            st.markdown("##### 📖 各话题阵营代表性网民发言追踪")
            topic_tabs = st.tabs([f"Topic {i+1} 语料样本" for i in range(n_clusters)])
            for i, t_tab in enumerate(topic_tabs):
                with t_tab:
                    topic_name = f"Topic {i + 1}"
                    subset = plot_data[plot_data["cluster"] == topic_name].sort_values(by="like_count", ascending=False).head(4)

                    if subset.empty:
                        st.info("该话题阵营下暂无发言数据")
                    else:
                        c_left, c_right = st.columns(2)
                        for idx_col, (_, row) in enumerate(subset.iterrows()):
                            col_to_use = c_left if idx_col % 2 == 0 else c_right
                            with col_to_use:
                                render_quote_card(
                                    author=row["author"],
                                    text=row["comment_text"],
                                    meta=f"情感得分: {row['sentiment_score']:.2f} | 话题划分: {topic_name}",
                                    sentiment=row["sentiment"],
                                    like_count=int(row["like_count"]),
                                )

        except Exception as e:
            st.error(f"聚类分析过程中发生异常:{e}")
            st.info("提示:这通常是由于评论中没有足够的词汇建立特征矩阵导致,请尝试增大采样评论数量。")


# ============================================================
# 词云
# ============================================================
def build_wordcloud_image(df: pd.DataFrame):
    """构建高对比度词云图片对象(支持中英文分词)。"""
    text_blob = " ".join(df["comment_text"].dropna().astype(str).tolist()).strip()
    if not text_blob:
        return None

    if contains_chinese(text_blob):
        try:
            import jieba
            text_blob = " ".join(jieba.cut(text_blob))
        except Exception:
            pass

    # 中文字体兼容性设计
    font_candidates = [
        "C:\\Windows\\Fonts\\msyh.ttc",  # Windows 微软雅黑
        "C:\\Windows\\Fonts\\simhei.ttf",  # Windows 黑体
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    font_path = next((f for f in font_candidates if os.path.exists(f)), None)

    from wordcloud import WordCloud
    wc = WordCloud(
        width=1200,
        height=500,
        background_color="#0b0d12",
        max_words=200,
        collocations=False,
        font_path=font_path,
        colormap="plasma",
    ).generate(text_blob)
    return wc.to_image()


# ============================================================
# 高赞评论引用卡片
# ============================================================
def render_extreme_quotes(df: pd.DataFrame) -> None:
    """深度透视页面中,提取用户高权重(Like 高)评论。"""
    render_section_title("🔍 核心舆论风向标:高赞观点追踪")

    c1, c2 = st.columns(2)

    pos_df = df[df["sentiment"].isin(["喜悦", "惊讶", "positive"])].sort_values(by="like_count", ascending=False).head(5)
    with c1:
        st.markdown("##### 🟢 典型正面回响 (Top 5 热门正面意见)")
        if pos_df.empty:
            st.info("暂无正面高赞意见。")
        else:
            for _, row in pos_df.iterrows():
                render_quote_card(
                    author=row["author"],
                    text=row["comment_text"],
                    meta=f"来自视频:{row['video_title'][:40]}... | 情绪分类: {row['sentiment']} | 评分: {row['sentiment_score']:.2f}",
                    sentiment=row["sentiment"],
                    like_count=int(row["like_count"]),
                    like_color="#10b981",
                )

    neg_df = df[df["sentiment"].isin(["愤怒", "悲伤", "恐惧", "厌恶", "negative"])].sort_values(by="like_count", ascending=False).head(5)
    with c2:
        st.markdown("##### 🔴 关键负面投诉 (Top 5 热门警示言论)")
        if neg_df.empty:
            st.info("健康度极高!未检测到明显的负面批评言论。")
        else:
            for _, row in neg_df.iterrows():
                render_quote_card(
                    author=row["author"],
                    text=row["comment_text"],
                    meta=f"来自视频:{row['video_title'][:40]}... | 情绪分类: {row['sentiment']} | 评分: {row['sentiment_score']:.2f}",
                    sentiment=row["sentiment"],
                    like_count=int(row["like_count"]),
                    like_color="#ef4444",
                )
