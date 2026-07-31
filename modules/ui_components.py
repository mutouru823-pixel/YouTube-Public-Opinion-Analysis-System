"""UI 组件与样式注入模块。

封装全部 Streamlit 自定义 CSS、Plotly 主题、卡片组件,以及情感语义配色常量,
避免 app.py 中堆积大量 HTML/CSS 字符串。
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go


# ============================================================
# 情感语义配色映射 (全应用统一,中文 7 维标签 + 兼容旧版三分类)
# ============================================================
SENTIMENT_COLOR_MAP: dict[str, str] = {
    "喜悦": "#10b981",   # Emerald
    "悲伤": "#3b82f6",   # Blue
    "愤怒": "#ef4444",   # Red
    "恐惧": "#8b5cf6",   # Purple
    "厌恶": "#f59e0b",   # Amber
    "惊讶": "#ec4899",   # Pink
    "中立": "#64748b",   # Slate
    # 兼容旧版三分类标签
    "positive": "#10b981",
    "neutral": "#64748b",
    "negative": "#ef4444",
}


# ============================================================
# CSS 注入
# ============================================================
PREMIUM_CSS: str = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Global Typography and BG */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background-color: #0b0d12;
    color: #f1f5f9;
}

[data-testid="stHeader"] {
    background-color: rgba(11, 13, 18, 0.6) !important;
    backdrop-filter: blur(12px);
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: rgba(17, 22, 34, 0.95) !important;
    backdrop-filter: blur(15px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2 {
    color: #a78bfa !important;
    font-weight: 600;
    letter-spacing: 0.05em;
}

/* Premium Glassmorphic Cards */
.metric-card {
    background: rgba(22, 28, 45, 0.6);
    backdrop-filter: blur(16px);
    border-radius: 16px;
    padding: 22px;
    border: 1px solid rgba(255, 255, 255, 0.06);
    box-shadow: 0 10px 30px 0 rgba(0, 0, 0, 0.25);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 15px;
}

.metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(139, 92, 246, 0.4);
    box-shadow: 0 15px 35px 0 rgba(139, 92, 246, 0.15);
}

.metric-title {
    font-size: 13px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
    font-weight: 500;
}

.metric-value {
    font-size: 30px;
    font-weight: 700;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-subtitle {
    font-size: 11px;
    color: #64748b;
    margin-top: 4px;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    background-color: rgba(17, 22, 34, 0.5);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    margin-bottom: 24px;
}

.stTabs [data-baseweb="tab"] {
    height: 44px;
    white-space: nowrap;
    background-color: transparent;
    border-radius: 10px;
    color: #94a3b8 !important;
    font-weight: 500;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    border: none !important;
    padding: 0 20px !important;
}

.stTabs [aria-selected="true"] {
    background-color: #8b5cf6 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 15px 0 rgba(139, 92, 246, 0.35);
}

.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    color: #cbd5e1 !important;
    background-color: rgba(255, 255, 255, 0.03);
}

/* Gradient Header Panel */
.header-panel {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(236, 72, 153, 0.03) 100%);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 20px;
    padding: 26px 30px;
    margin-bottom: 28px;
    box-shadow: 0 8px 32px 0 rgba(139, 92, 246, 0.03);
}

.header-panel h1 {
    margin: 0;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(to right, #ffffff, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.header-panel p {
    margin: 8px 0 0 0;
    color: #94a3b8;
    font-size: 1.05rem;
}

/* Custom buttons */
div.stButton > button:first-child {
    background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 14px 0 rgba(124, 58, 237, 0.3) !important;
}

div.stButton > button:first-child:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px 0 rgba(124, 58, 237, 0.45) !important;
}

/* Subtitle dividers */
.section-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #f8fafc;
    border-left: 4px solid #8b5cf6;
    padding-left: 12px;
    margin-top: 25px;
    margin-bottom: 18px;
}

/* Quote Cards */
.quote-card {
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 12px;
    border-left: 4px solid #4b5563;
    background: rgba(255, 255, 255, 0.02);
}
.quote-card-neg {
    border-left-color: #f87171;
    background: rgba(248, 113, 113, 0.03);
}
.quote-card-pos {
    border-left-color: #34d399;
    background: rgba(52, 211, 153, 0.03);
}
.quote-author {
    font-size: 0.85rem;
    color: #94a3b8;
    margin-bottom: 6px;
    font-weight: 600;
}
.quote-text {
    font-size: 0.95rem;
    color: #e2e8f0;
}
.quote-meta {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 6px;
}
</style>
"""


def inject_css() -> None:
    """注入全套学术风高级 CSS 样式。应在页面顶部调用一次。"""
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


def render_header_panel(title: str, subtitle: str) -> None:
    """渲染顶部渐变标题面板。"""
    st.markdown(
        f"""
        <div class="header-panel">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(text: str) -> None:
    """渲染带紫色左边框的分节标题。"""
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def render_metric_card(
    title: str,
    value: str,
    subtitle: str = "",
    value_gradient: str | None = None,
) -> None:
    """渲染单个学术指标玻璃态卡片。

    Args:
        title: 指标标题(如 "语料样本总量")
        value: 已格式化的数值字符串(如 "1,234" 或 "0.567")
        subtitle: 副标题说明
        value_gradient: 可选,自定义数值渐变色 CSS(如 "linear-gradient(...)")
    """
    value_style = (
        f'style="background: {value_gradient}; -webkit-background-clip: text; '
        f'-webkit-text-fill-color: transparent;"'
        if value_gradient
        else ""
    )
    subtitle_html = (
        f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value" {value_style}>{value}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quote_card(
    author: str,
    text: str,
    meta: str,
    sentiment: str,
    like_count: int = 0,
    like_color: str = "#94a3b8",
) -> None:
    """渲染网民评论引用卡片(根据情感自动配色)。

    Args:
        author: 评论作者显示名
        text: 评论文本
        meta: 元信息(视频标题/情感/评分)
        sentiment: 情感标签,用于决定卡片边框色
        like_count: 点赞数
        like_color: 点赞数文字颜色
    """
    if sentiment in ("喜悦", "惊讶", "positive"):
        card_cls = "quote-card quote-card-pos"
    elif sentiment in ("愤怒", "悲伤", "恐惧", "厌恶", "negative"):
        card_cls = "quote-card quote-card-neg"
    else:
        card_cls = "quote-card"

    st.markdown(
        f"""
        <div class="{card_cls}">
            <div class="quote-author">👤 {author}
                <span style="float:right; color:{like_color};">👍 {like_count} Likes</span>
            </div>
            <div class="quote-text">“{text}”</div>
            <div class="quote-meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Plotly 统一主题
# ============================================================
def apply_plotly_theme(fig: go.Figure) -> None:
    """统一应用学术风暗色 Plotly 主题(原地修改图表)。"""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color="#94a3b8"),
        title=dict(font=dict(size=15, color="#ffffff")),
        legend=dict(font=dict(size=11, color="#94a3b8")),
        margin=dict(l=40, r=40, t=50, b=40),
    )
    # 饼图等无轴图表在某些 Plotly 版本下会报错,需兜底
    try:
        fig.update_xaxes(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.1)",
            tickfont=dict(color="#64748b"),
            titlefont=dict(color="#94a3b8"),
        )
    except Exception:
        pass
    try:
        fig.update_yaxes(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.1)",
            tickfont=dict(color="#64748b"),
            titlefont=dict(color="#94a3b8"),
        )
    except Exception:
        pass
