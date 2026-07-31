"""计算传播学核心量化指标模块。

包含三个学术级统计量:
- Esteban-Ray 舆论极化指数
- Shannon 语义信息熵
- 态度主观性指数

并提供 ``render_metrics`` 统一渲染四张指标玻璃态卡片。
"""

from __future__ import annotations

import collections
import math
import re

import pandas as pd
import streamlit as st

from .sentiment import contains_chinese
from .ui_components import render_metric_card


# 正向 / 负向情感标签集合(中文 7 维 + 兼容旧版三分类)
POSITIVE_LABELS = {"喜悦", "惊讶", "positive"}
NEGATIVE_LABELS = {"愤怒", "悲伤", "恐惧", "厌恶", "negative"}
NEUTRAL_LABELS = {"中立", "neutral"}


def calculate_shannon_entropy(df: pd.DataFrame) -> float:
    """计算词频的 Shannon 信息熵 (Shannon Entropy)。

    H 较高:讨论词汇丰富,议题发散,体现去中心化的自发讨论。
    H 较低:表达极度集中于少数词汇(通常伴随水军刷屏或情绪极化宣泄)。
    """
    text_list = df["comment_text"].dropna().astype(str).tolist()
    text_blob = " ".join(text_list).strip()
    if not text_blob:
        return 0.0

    words: list[str] = []
    if contains_chinese(text_blob):
        try:
            import jieba
            words = [w for w in jieba.cut(text_blob) if len(w.strip()) > 1]
        except Exception:
            words = [w for w in text_blob.split() if len(w.strip()) > 1]
    else:
        cleaned_text = re.sub(r"[^\w\s]", "", text_blob.lower())
        words = [w for w in cleaned_text.split() if len(w.strip()) > 2]

    if not words:
        return 0.0

    counts = collections.Counter(words)
    total = len(words)

    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def calculate_polarization_index(df: pd.DataFrame) -> tuple[float, str]:
    """基于 Esteban-Ray 派生模型的舆论极化指数 (Polarization Index)。

    P = 4 * P_pos * P_neg,取值 [0, 1]。越接近 1 表示正负阵营势均力敌对抗。
    """
    total = len(df)
    if total == 0:
        return 0.0, "无数据"

    p_pos = df["sentiment"].isin(POSITIVE_LABELS).mean()
    p_neg = df["sentiment"].isin(NEGATIVE_LABELS).mean()

    polarization = 4 * p_pos * p_neg

    if polarization < 0.2:
        desc = "高度共识 (Consensus) - 社区情感呈现显著的一边倒态势"
    elif polarization < 0.5:
        desc = "轻度对立 (Mild Division) - 社区内伴有小范围的异质偏离意见"
    elif polarization < 0.8:
        desc = "中度分裂 (Moderately Polarized) - 社区舆论场已呈现明显对立的两派阵营"
    else:
        desc = "高度极化 (Highly Polarized) - 网民情感极度极化分裂(红绿阵营势均力敌对抗)"

    return polarization, desc


def calculate_subjectivity_rate(df: pd.DataFrame) -> float:
    """计算态度主观性指数:非中立主观发言占比 (%)。

    修复要点:实际情感标签为中文「中立」,而非英文 「neutral」,
    此前用 != "neutral" 判断会导致主观性指数永远接近 100%。
    """
    total = len(df)
    if total == 0:
        return 0.0
    # 排除所有「中立」语义标签(中文 + 兼容旧版)
    is_neutral = df["sentiment"].isin(NEUTRAL_LABELS)
    return (~is_neutral).mean() * 100


def render_metrics(df: pd.DataFrame) -> None:
    """渲染四张学术指标玻璃态卡片:样本量 / 主观性 / 极化指数 / 信息熵。

    修复要点:原代码在 f-string 中误用 ``{{polarization:.3f}}`` 双花括号,
    导致页面上直接显示字面字符串 ``{polarization:.3f}`` 而非实际数值。
    现改为预先格式化字符串,再传入卡片组件。
    """
    total = len(df)
    sub_rate = calculate_subjectivity_rate(df)
    polarization, pol_desc = calculate_polarization_index(df)
    entropy = calculate_shannon_entropy(df)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            title="📥 语料样本总量 (N)",
            value=f"{total:,}",
            subtitle="样本抓取层深度:Top-level comments",
        )
    with col2:
        render_metric_card(
            title="🔬 态度主观性指数",
            value=f"{sub_rate:.1f}%",
            subtitle="非中立主观语义倾向的发言占比",
            value_gradient="linear-gradient(135deg, #34d399 0%, #059669 100%)",
        )
    with col3:
        render_metric_card(
            title="⚖️ 极化指数 (Esteban-Ray)",
            value=f"{polarization:.3f}",
            subtitle=pol_desc,
            value_gradient="linear-gradient(135deg, #fbbf24 0%, #d97706 100%)",
        )
    with col4:
        render_metric_card(
            title="🌀 语义信息熵 (Shannon H)",
            value=f"{entropy:.3f}",
            subtitle="数值越高代表论题语义越发散丰富",
            value_gradient="linear-gradient(135deg, #f87171 0%, #dc2626 100%)",
        )
