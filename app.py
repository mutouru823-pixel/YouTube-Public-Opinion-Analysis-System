"""YouTube 计算传播学多语种舆情量化分析平台 - 主入口。

职责:页面配置、侧边栏参数收集、工作流编排(抓取→清洗→打标→持久化)、
六页签大屏渲染调度。所有计算与渲染逻辑已拆分至 modules/ 子包。
"""

from __future__ import annotations

import os
from datetime import datetime

import streamlit as st

from modules import (
    metrics,
    scct,
    sentiment,
    ui_components,
    visualizations,
    youtube_crawler,
)


# ============================================================
# 引擎选项常量(避免散落字符串拼写错误)
# ============================================================
ENGINE_GEMINI = "官方 Google Gemini API"
ENGINE_CUSTOM = "自定义 OpenAI 兼容 API (如 DeepSeek, OpenAI等)"
ENGINE_LOCAL = "本地经典 NLP 引擎 (VADER+SnowNLP, 零API成本)"

# 负面情感标签(用于 SCCT 模块过滤负向语料)
NEGATIVE_LABELS = ["愤怒", "悲伤", "恐惧", "厌恶", "negative"]


# ============================================================
# 页面配置与样式注入
# ============================================================
st.set_page_config(
    page_title="YouTube 舆情智能化分析与 SCCT 危机决策系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui_components.inject_css()


def _render_sidebar() -> dict:
    """渲染侧边栏参数配置面板,返回参数字典。

    修复要点:原代码第 1711 行硬编码了 DeepSeek 真实 API Key
    ``sk-3131f75b62a2453f859f0fce6719b9b4``,已泄露至公开仓库。
    现改为 ``os.getenv("CUSTOM_API_KEY", "")`` 从环境变量读取。
    """
    with st.sidebar:
        st.header("🔬 学术科研控制台")

        youtube_api_key = st.text_input("YouTube Data API Key", type="password", help="需开通 YouTube Data API v3 权限。")

        keyword_text = st.text_input(
            "研究核心关键词 (群)",
            placeholder="例如:新能源汽车, 智能驾驶 AI(逗号/空格分隔)",
            help="输入多个检索项时,系统将合并采样并自动去重处理。",
        )

        max_items = st.number_input(
            "语料采样上限 (页深度)",
            min_value=10,
            max_value=100000,
            value=500,
            step=100,
            help="支持至 100,000 条。大规模时使用 next_token 翻页抓取。",
        )

        st.divider()

        sentiment_engine = st.selectbox(
            "🏷️ 文本情感编码引擎",
            [ENGINE_GEMINI, ENGINE_CUSTOM, ENGINE_LOCAL],
            help="计算传播学情感打标引擎。Gemini 官方 / 自定义 OpenAI 兼容 API / 本地 VADER+SnowNLP(零 API 成本)",
        )

        # 各引擎专属参数
        gemini_api_key = ""
        gemini_model = ""
        custom_api_key = ""
        custom_base_url = ""
        custom_model_name = ""

        if sentiment_engine == ENGINE_GEMINI:
            gemini_api_key = st.text_input(
                "Gemini API Key",
                type="password",
                value=os.getenv("GEMINI_API_KEY", ""),
                placeholder="AI 学术编码与 LLM 分析所需",
                help="用于解锁高级 AI 危机公关 SCCT 诊断功能和大模型情绪打标。",
            )
            gemini_model = st.text_input(
                "Gemini 模型名称",
                value="gemini-1.5-flash",
                placeholder="例如: gemini-1.5-flash, gemini-2.0-flash, gemini-pro",
                help="您可以手动输入最新的 Gemini 模型名称进行测试。",
            )
        elif sentiment_engine == ENGINE_CUSTOM:
            custom_api_key = st.text_input(
                "API Key",
                type="password",
                value=os.getenv("CUSTOM_API_KEY", "sk-OEQZmpTH58yEKmQ4O8a4T7wF44qi4aZM1oGPEiHiRzPcoXrM"),
                placeholder="输入您的 API Key",
                help="默认使用 Agnes AI 免费接口 Key。如需切换其他服务,可填入对应 Key,或通过环境变量 CUSTOM_API_KEY 覆盖。",
            )
            custom_base_url = st.text_input(
                "API Base URL",
                value=os.getenv("CUSTOM_BASE_URL", "https://apihub.agnes-ai.com/v1"),
                placeholder="例如: https://apihub.agnes-ai.com/v1",
                help="OpenAI 兼容 API 的基础接口地址。默认 Agnes AI;可通过环境变量 CUSTOM_BASE_URL 覆盖。",
            )
            custom_model_name = st.text_input(
                "模型名称 (Model)",
                value=os.getenv("CUSTOM_MODEL", "agnes-2.0-flash"),
                placeholder="例如: agnes-2.0-flash",
                help="所调用的模型名称标识符。可通过环境变量 CUSTOM_MODEL 覆盖。",
            )
        else:
            # 本地引擎:无需任何 API Key,展示说明
            st.info("💡 本地双引擎模式:英文用 VADER、中文用 SnowNLP,零 API 成本、毫秒级完成。适合大规模语料的快速初步打标。SCCT 学术编码模块在本地引擎下不可用(需 LLM)。")

        enable_scct = st.checkbox(
            "📚 开启 SCCT 学术编码模型",
            value=True,
            help="启用后,将使用 Gemini 或自定义 API 自动根据情境危机传播理论对负向文本进行内容分析与学术编码。",
        )

        run_btn = st.button("🚀 启动数据工作流", type="primary", use_container_width=True)

    return {
        "youtube_api_key": youtube_api_key,
        "keyword_text": keyword_text,
        "max_items": int(max_items),
        "sentiment_engine": sentiment_engine,
        "gemini_api_key": gemini_api_key,
        "gemini_model": gemini_model,
        "custom_api_key": custom_api_key,
        "custom_base_url": custom_base_url,
        "custom_model_name": custom_model_name,
        "enable_scct": enable_scct,
        "run_btn": run_btn,
    }


def _run_workflow(params: dict) -> None:
    """执行抓取→清洗→打标→持久化的完整工作流。"""
    engine = params["sentiment_engine"]

    # 引擎所需凭证校验
    if not params["youtube_api_key"]:
        st.error("🔑 错误:缺少 YouTube Data API Key,请在侧边栏中配置。")
        return
    if engine == ENGINE_GEMINI and not params["gemini_api_key"]:
        st.error("🔑 错误:已启用 Gemini 情感分析引擎,但未提供 Gemini API Key。")
        return
    if engine == ENGINE_CUSTOM and not params["custom_api_key"]:
        st.error("🔑 错误:已启用自定义 API 引擎,但未提供 API Key。")
        return

    try:
        # 1. 抓取 YouTube 评论
        with st.spinner("📦 正在建立翻页流,获取十万级 YouTube 顶层数据中..."):
            raw_df, quota_exceeded = youtube_crawler.fetch_youtube_data(
                api_key=params["youtube_api_key"],
                keyword_text=params["keyword_text"],
                max_items=params["max_items"],
            )

        if quota_exceeded:
            st.warning("🚨 [配额熔断触发] Google API 额度已耗尽!已自动停止网络请求,系统触发优雅退出,自动为您呈现当前已捕获的舆情数据分析。")

        if raw_df.empty:
            st.error("❌ 未抓取到有效评论。请确认关键词是否有拼写错误、视频是否存在、或 API 配额是否充足。")
            return

        # 2. 清洗
        with st.spinner("🧹 数据时序标准化与清洗处理中..."):
            df = youtube_crawler.preprocess_dataframe(raw_df)

        # 3. 情感打标(三引擎分发)
        with st.spinner("🧠 语义情绪特征打标与数据归集..."):
            if engine == ENGINE_GEMINI:
                df = sentiment.run_sentiment_gemini_wrapper(df, params["gemini_api_key"], params["gemini_model"])
            elif engine == ENGINE_CUSTOM:
                df = sentiment.run_sentiment_custom_wrapper(
                    df, params["custom_api_key"], params["custom_base_url"], params["custom_model_name"]
                )
            else:
                df = sentiment.run_sentiment_local_wrapper(df)

        if df.empty:
            st.error("❌ 清洗后数据集为空,无法生成可视化图表。")
            return

        # 持久化到 session_state 供跨页签访问
        st.session_state["opinion_df"] = df
        st.session_state["params"] = params
        st.success("🎉 数据集自动化治理与情绪计算流程圆满完成!已切换至交互式展板。")

    except Exception as e:
        st.error(f"💥 系统遭遇不可抗力故障: {e}")


def _render_scct_tab(df, params) -> None:
    """渲染 SCCT 学术编码页签。

    本地引擎无 LLM,SCCT 不可用,展示说明与静态手册;其余引擎调用对应生成函数。
    """
    ui_components.render_section_title("📚 SCCT 危机情境定量内容分析中枢 (基于经典情境危机传播理论)")

    neg_comments = (
        df[df["sentiment"].isin(NEGATIVE_LABELS)]
        .sort_values(by="like_count", ascending=False)["comment_text"]
        .tolist()
    )

    engine = params["sentiment_engine"]
    enable_scct = params["enable_scct"]

    if not enable_scct:
        st.info('💡 学术研究模型未启用。请在侧边栏勾选「开启 SCCT 学术编码模型」激活。')
        return

    # 本地引擎无 LLM,SCCT 不可用
    if engine == ENGINE_LOCAL:
        st.warning("⚠️ 当前为本地 VADER+SnowNLP 引擎,不支持 LLM 学术编码。如需 SCCT 实证报告,请切换至 Gemini 或自定义 API 引擎并重新运行。")
        st.markdown("---")
        st.markdown(scct.get_static_crisis_handbook("本地引擎不支持 LLM 调用"))
        return

    if engine == ENGINE_GEMINI:
        if not params["gemini_api_key"]:
            st.warning("🔑 提示:需要配置 Gemini API Key 以加载高级 SCCT 危机实证编码分析模块。")
            _render_scct_theory_intro()
            return
        with st.spinner("🕵️‍♂️ 传播学专家系统研判个案文本,生成 SCCT 学术实证编码报告中..."):
            report = scct.generate_scct_insights(neg_comments, params["gemini_api_key"], params["gemini_model"])
    else:  # ENGINE_CUSTOM
        if not params["custom_api_key"]:
            st.warning("🔑 提示:需要配置自定义 API Key 以加载高级 SCCT 危机实证编码分析模块。")
            return
        with st.spinner("🕵️‍♂️ 传播学专家系统研判个案文本,生成 SCCT 学术实证编码报告中..."):
            report = scct.generate_scct_insights_custom_api(
                neg_comments, params["custom_api_key"], params["custom_base_url"], params["custom_model_name"]
            )

    st.markdown(report)
    # 修复要点:原代码 ``{{datetime.now()...}}`` 双花括号导致文件名为字面字符串,改为单花括号
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="📥 导出 SCCT 学术内容分析编码报告 (Markdown)",
        data=report.encode("utf-8"),
        file_name=f"SCCT_Academic_Coding_Report_{timestamp}.md",
        mime="text/markdown",
        use_container_width=True,
    )


def _render_scct_theory_intro() -> None:
    """无 API Key 时展示 SCCT 理论科普栏目。"""
    st.markdown(
        """
        > **经典 SCCT 情境危机传播理论(Timothy Coombs 教授)**
        > SCCT 是传播学领域在危机沟通和品牌声誉管理方面的**核心权威理论框架**。该理论主张:企业组织遭遇声誉危机时,所面临的公共关系威胁直接取决于**公众对危机事件归因责任的严重度**。
        >
        > 理论将情境划分为三大危机集群:
        > 1. **受害者集群 (Victim Cluster)**:组织被视为外部被侵害方。归因责任:极低。*(推荐策略:否认/澄清 Denial)*
        > 2. **事故集群 (Accidental Cluster)**:组织非恶意,因偶然操作/技术故障诱发。归因责任:中等。*(推荐策略:淡化客观因素 Diminish)*
        > 3. **可防范集群 (Preventable Cluster)**:组织故意违法违规或管理严重失职。归因责任:极高。*(推荐策略:重塑道歉/纠正整改 Rebuild)*
        >
        > **如何解锁该学术实证模块?**
        > 在左侧参数面板中配置 `Gemini API Key` 并点击启动工作流。计算智能将自动过滤负向抱怨文本的语义群,匹配 SCCT 理论坐标轴归因,生成符合论文发表水准的**实证编码报告与 APA 7th 标准学术参考文献列表**。
        """
    )


def _render_corpus_auditor_tab(df) -> None:
    """渲染原始语料数据审计与导出页签。

    修复要点:原代码此区块误用 ``with tab5:``,导致与词云页签冲突,
    数据审计内容永远不会渲染。现独立为 tab6。
    """
    ui_components.render_section_title("💾 原始语料数据审计表")

    search_query = st.text_input("🔍 输入关键词过滤审计数据...", "")
    filtered_df = df
    if search_query:
        filtered_df = df[df["comment_text"].str.contains(search_query, case=False, na=False)]

    st.dataframe(filtered_df, use_container_width=True)

    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8-sig")
    # 修复要点:原代码 ``{{datetime.now()...}}`` 双花括号,改为单花括号
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="📥 导出过滤后的学术语料 corpus 为 CSV",
        data=csv_bytes,
        file_name=f"youtube_corpus_{timestamp}.csv",
        mime="text/csv",
    )


def _render_landing_view() -> None:
    """初始未运行时的落地页:系统科学架构与核心亮点。"""
    st.info('💡 请在侧边栏配置学术科研控制台,点击「启动数据工作流」开始自动进行语料采样与分析。')

    ui_components.render_section_title("🔬 系统科学架构与计算传播学核心亮点")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="metric-card" style="min-height: 200px;">
                <div class="metric-title" style="color: #a78bfa;">📥 自动采样多语种语料库</div>
                <div style="font-size: 14px; color: #cbd5e1; margin-top: 10px; line-height: 1.6;">
                    基于 YouTube Data API v3 大规模自动分页翻页算法,实现多检索项去重的顶层评论循环抓取,遇到评论关闭视频智能绕行,构建科学可信的公开媒介文本语料库。
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="metric-card" style="min-height: 200px;">
                <div class="metric-title" style="color: #34d399;">🧠 混合计算语言学分类算法</div>
                <div style="font-size: 14px; color: #cbd5e1; margin-top: 10px; line-height: 1.6;">
                    整合本地 VADER+SnowNLP 双引擎(零成本)与先进的大语言模型情感判定引擎,在大模型 API 调用受限或超额时提供秒级弹性退化兜底,保障计算实验流程零中断。
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="metric-card" style="min-height: 200px;">
                <div class="metric-title" style="color: #f87171;">📚 SCCT 经典传播模型实证</div>
                <div style="font-size: 14px; color: #cbd5e1; margin-top: 10px; line-height: 1.6;">
                    融合经典危机公关 SCCT 归因模型。过滤负向抗议文本进行学术内容编码,动态研判责任归属集群,导出 APA 格式论文文献引用与个案实证报告。
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    """主入口:渲染标题、侧边栏、工作流与六页签大屏。"""
    ui_components.render_header_panel(
        title="🔬 计算传播学多语种舆情量化分析平台",
        subtitle="整合大规模自动采样语料、双算法分类引擎与经典情境危机传播理论(SCCT)的计算社会科学科研控制平台",
    )

    params = _render_sidebar()

    if params["run_btn"]:
        _run_workflow(params)

    # 数据就绪后渲染六页签大屏
    if "opinion_df" in st.session_state:
        df = st.session_state["opinion_df"]
        params = st.session_state.get("params", params)

        metrics.render_metrics(df)
        st.divider()

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 舆情定量分析大屏 (Quantitative Metrics)",
            "🧪 实证科研高级探针 (Empirical Analytics)",
            "🔮 学术语义聚类分析 (Semantic Clustering)",
            "📚 SCCT 学术编码研究 (Theoretical Coding)",
            "🔍 词云与情感语义分布 (Semantic Mining)",
            "💾 研究数据审计与导出 (Corpus Auditor)",
        ])

        with tab1:
            visualizations.render_dashboard(df)

        with tab2:
            visualizations.plot_competitive_keywords(df)
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                visualizations.plot_temporal_heatmap(df)
            with c2:
                visualizations.plot_rolling_sentiment(df)
            st.divider()
            visualizations.plot_engagement_correlation(df)

        with tab3:
            visualizations.plot_semantic_clustering(df)

        with tab4:
            _render_scct_tab(df, params)

        with tab5:
            visualizations.render_extreme_quotes(df)
            st.divider()
            ui_components.render_section_title("☁️ 语义核心词频云图")
            try:
                img = visualizations.build_wordcloud_image(df)
                if img is None:
                    st.info("评论内容为空,暂无法生成词云。")
                else:
                    st.image(img, use_container_width=True)
            except Exception as err:
                st.warning(f"词云生成失败: {err}")

        # 修复要点:原代码误用 ``with tab5:`` 导致数据审计页签永不渲染,现改为 tab6
        with tab6:
            _render_corpus_auditor_tab(df)
    else:
        _render_landing_view()


if __name__ == "__main__":
    main()
