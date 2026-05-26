import io
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from wordcloud import WordCloud

# Set modern page config
st.set_page_config(
    page_title="YouTube 舆情智能化分析与 SCCT 危机决策系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom premium CSS injection (Outfit typography, Glassmorphism, Neon glow borders)
st.markdown(
    """
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
    """,
    unsafe_allow_html=True,
)


def contains_chinese(text: str) -> bool:
    """判断文本是否包含中文字符。"""
    if not text:
        return False
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def classify_emotion_fallback_pure_python(text: str) -> Tuple[str, float, str]:
    """
    轻量级纯 Python 规则情感打标（无任何第三方库依赖，作为 API 无法连接时的纯本地安全兜底）。
    """
    if not text or not text.strip():
        return "中立", 0.5, "纯Python兜底"
        
    text_lower = text.lower()
    
    # 情绪指标分类特征词库（支持中英双语）
    # 喜悦词表
    joy_indicators = ["good", "love", "like", "great", "awesome", "perfect", "nice", "best", "wonderful", "cool", "happy", "棒", "赞", "喜悦", "喜欢", "支持", "不错", "好评", "优秀", "牛逼", "厉害", "给力"]
    # 悲伤词表
    sadness_indicators = ["sad", "cry", "sorry", "pain", "unfortunate", "disappointed", "regret", "难过", "伤心", "悲伤", "遗憾", "可怜", "哭", "痛", "失望", "委屈"]
    # 愤怒词表
    anger_indicators = ["angry", "hate", "mad", "shit", "fuck", "damn", "annoyed", "垃圾", "恶心", "愤怒", "生气", "差评", "退货", "骂", "傻", "极其恶劣", "滚", "无耻", "混蛋"]
    # 恐惧词表
    fear_indicators = ["fear", "scared", "afraid", "worry", "panic", "terror", "anxious", "害怕", "担心", "恐惧", "恐慌", "吓人", "可怕", "焦虑", "担忧", "忧虑"]
    # 厌恶词表
    disgust_indicators = ["disgust", "nasty", "gross", "garbage", "sick", "recoil", "厌恶", "反感", "恶劣", "鄙视", "唾弃", "抵制", "下作"]
    # 惊讶词表
    surprise_indicators = ["?!", "!?", "！", "？", "oh", "wow", "surprise", "amazed", "shocked", "惊讶", "意外", "居然", "竟然", "吃惊", "天哪"]
    
    joy_hits = sum(1 for w in joy_indicators if w in text_lower)
    sad_hits = sum(1 for w in sadness_indicators if w in text_lower)
    ang_hits = sum(1 for w in anger_indicators if w in text_lower)
    fear_hits = sum(1 for w in fear_indicators if w in text_lower)
    dis_hits = sum(1 for w in disgust_indicators if w in text_lower)
    sur_hits = sum(1 for w in surprise_indicators if w in text_lower)
    
    hits = {
        "喜悦": joy_hits,
        "悲伤": sad_hits,
        "愤怒": ang_hits,
        "恐惧": fear_hits,
        "厌恶": dis_hits,
        "惊讶": sur_hits
    }
    
    max_emotion = max(hits, key=hits.get)
    if hits[max_emotion] == 0:
        return "中立", 0.5, "纯Python兜底"
        
    if max_emotion == "喜悦":
        score = 0.8
    elif max_emotion == "惊讶":
        score = 0.65
    elif max_emotion in ["悲伤", "恐惧"]:
        score = 0.3
    elif max_emotion in ["愤怒", "厌恶"]:
        score = 0.15
    else:
        score = 0.5
        
    return max_emotion, score, "纯Python兜底"


def batch_analyze_sentiment_with_gemini(comments: List[str], api_key: str, model_name: str = "gemini-1.5-flash") -> List[Tuple[str, float, str]]:
    """
    【AI双引擎高级功能】批量使用 Gemini 对评论进行情感打标，支持多模型自动弹性回退。
    """
    results = []
    batch_size = 20  # 每次并行分析 20 条，减少 API 握手次数
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Gemini 客户端配置失败，自动退化为纯 Python 规则模型: {e}")
        return [classify_emotion_fallback_pure_python(c) for c in comments]
 
    # 声明候选模型列表，优先尝试用户所选的模型
    candidate_models = [model_name] if model_name else []
    candidate_models.extend(["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"])
    # 去重保留顺序
    seen = set()
    candidate_models = [x for x in candidate_models if not (x in seen or seen.add(x))]
    active_model_name = None
 
    for i in range(0, len(comments), batch_size):
        batch = comments[i : i + batch_size]
        
        # 结构化输入，限制长度避免大段评论溢出
        inputs = []
        for idx, text in enumerate(batch):
            inputs.append({"id": idx, "text": text[:200]})
 
        prompt = f"""
你是一名专业的高级社交媒体与传播学数据分析师。请对以下评论列表进行精细的情感维度分类。
你必须对每条评论进行情绪维度分类，必须是以下七类之一（选择最贴切的一项作为情绪标签）：
1. "喜悦" (高兴、赞赏、支持、幽默、热烈期盼等积极向上的态度)
2. "悲伤" (遗憾、伤心、失望、同情、无奈等消极倾向的态度)
3. "愤怒" (生气、谴责、怒骂、剧烈抗议等极其激烈的敌对态度)
4. "恐惧" (担忧、害怕、恐慌、顾虑、忧心忡忡等缺乏安全感的态度)
5. "厌恶" (反感、恶心、鄙视、嫌弃、唾弃、抵制等拒绝认同的态度)
6. "惊讶" (吃惊、意外、出乎意料、难以置信等被震惊的态度)
7. "中立" (平静、客观叙事、无明显情绪波动的客观事实陈述)
 
另外，请给出一个在 0.0 到 1.0 之间的小数作为情绪极性得分（0.0代表极度消极，0.5代表中立，1.0代表极度积极）。
 
待分类评论列表:
```json
{json.dumps(inputs, ensure_ascii=False)}
```
 
请严格返回符合以下 JSON 格式的数组，不要包含任何额外的 markdown 格式或多余的文字，只需返回纯 JSON：
[
  {{"id": 0, "sentiment": "喜悦", "score": 0.85}},
  ...
]
"""
        response = None
        last_err = ""
        # 优先使用已经验证成功的可用模型，否则逐个尝试
        models_to_try = [active_model_name] if active_model_name else candidate_models
 
        for m_name in models_to_try:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt)
                active_model_name = m_name  # 锁定可用模型
                break
            except Exception as e:
                last_err = str(e)
                # 只有遇到模型名称不匹配或API版本/型号不支持报错时才继续尝试候选模型
                if not active_model_name and ("404" in last_err or "not found" in last_err.lower() or "not supported" in last_err.lower() or "not_found" in last_err.lower()):
                    continue
                else:
                    break
 
        if response is None:
            # 批次失败降级
            for text in batch:
                label, score, model_used = classify_emotion_fallback_pure_python(text)
                results.append((label, score, f"{model_used}(LLM失败降级)"))
            continue
 
        try:
            res_text = response.text.strip()
            
            # 清理可能被大语言模型包裹的代码块标签
            if res_text.startswith("```json"):
                res_text = res_text[7:]
            if res_text.endswith("```"):
                res_text = res_text[:-3]
            res_text = res_text.strip()
            
            items = json.loads(res_text)
            items_sorted = sorted(items, key=lambda x: x["id"])
            
            for idx, item in enumerate(items_sorted):
                label = item.get("sentiment", "中立")
                score = float(item.get("score", 0.5))
                results.append((label, score, f"Gemini ({active_model_name})"))
                
        except Exception as e:
            # 解析失败降级
            for text in batch:
                label, score, model_used = classify_emotion_fallback_pure_python(text)
                results.append((label, score, f"{model_used}(解析失败降级)"))
                
    return results


def batch_analyze_sentiment_with_custom_api(comments: List[str], api_key: str, base_url: str, model_name: str) -> List[Tuple[str, float, str]]:
    """
    【AI自定义API高级功能】使用自定义 OpenAI 兼容接口（如 DeepSeek、OpenAI）对评论进行 7 维情绪打标。
    """
    results = []
    batch_size = 20  # 每次分析 20 条，平衡交互速率与大模型请求限制
    
    # 规范化 URL 地址
    url = base_url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    if not url.rstrip("/").endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
 
    for i in range(0, len(comments), batch_size):
        batch = comments[i : i + batch_size]
        inputs = []
        for idx, text in enumerate(batch):
            inputs.append({"id": idx, "text": text[:200]})
 
        prompt = f"""
你是一名专业的高级社交媒体与传播学数据分析师。请对以下评论列表进行精细的情感维度分类。
你必须对每条评论进行情绪维度分类，必须是以下七类之一（选择最贴切的一项作为情绪标签）：
1. "喜悦" (高兴、赞赏、支持、幽默、热烈期盼等积极向上的态度)
2. "悲伤" (遗憾、伤心、失望、同情、无奈等消极倾向的态度)
3. "愤怒" (生气、谴责、怒骂、剧烈抗议等极其激烈的敌对态度)
4. "恐惧" (担忧、害怕、恐慌、顾虑、忧心忡忡等缺乏安全感的态度)
5. "厌恶" (反感、恶心、鄙视、嫌弃、唾弃、抵制等拒绝认同的态度)
6. "惊讶" (吃吃惊、意外、出乎意料、难以置信等被震惊的态度)
7. "中立" (平静、客观叙事、无明显情绪波动的客观事实陈述)
 
另外，请给出一个在 0.0 到 1.0 之间的小数作为情绪极性得分（0.0代表极度消极，0.5代表中立，1.0代表极度积极）。
 
待分类评论列表:
```json
{json.dumps(inputs, ensure_ascii=False)}
```
 
请严格返回符合以下 JSON 格式的数组，不要包含任何额外的 markdown 格式或多余的文字，只需返回纯 JSON：
[
  {{"id": 0, "sentiment": "喜悦", "score": 0.85}},
  ...
]
"""
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
 
        try:
            import requests
            res = requests.post(url, headers=headers, json=payload, timeout=45)
            res.raise_for_status()
            data = res.json()
            res_text = data["choices"][0]["message"]["content"].strip()
            
            # 清理 Markdown 代码块
            if res_text.startswith("```json"):
                res_text = res_text[7:]
            if res_text.endswith("```"):
                res_text = res_text[:-3]
            res_text = res_text.strip()
            
            # 提取 JSON 数组
            match = re.search(r"\[\s*\{.*\}\s*\]", res_text, re.DOTALL)
            if match:
                res_text = match.group(0)
                
            items = json.loads(res_text)
            items_sorted = sorted(items, key=lambda x: x["id"])
            
            for item in items_sorted:
                label = item.get("sentiment", "中立")
                score = float(item.get("score", 0.5))
                results.append((label, score, f"Custom ({model_name})"))
                
        except Exception as e:
            # 失败后降级为纯 Python 本地兜底
            for text in batch:
                label, score, model_used = classify_emotion_fallback_pure_python(text)
                results.append((label, score, f"{model_used}(API连接或解析异常兜底)"))
                
    return results


def generate_scct_insights(negative_comments: List[str], api_key: str, model_name: str = "gemini-1.5-flash") -> str:
    """
    【商业危机管理模块】使用 Google Gemini API 基于 Coombs 的 SCCT（情境危机传播理论）提供系统公关策略。
    """
    if not api_key:
        return "⚠️ 请在左侧参数配置面板输入 API Key 以激活 SCCT 公关战略模块。"
        
    if not negative_comments:
        return "💡 暂未检测到明显的负面言论，品牌声誉安全，无需触发 SCCT 危机预案。"

    sample_comments = negative_comments[:40]
    comments_text = "\n".join([f"- {c}" for c in sample_comments])

    prompt = f'''
你是一名资深传播学学者和计算社会学（Computational Social Science）科研专家。请根据 Coombs 的 **情境危机传播理论 (Situational Crisis Communication Theory, SCCT)**，对以下 YouTube 视频语料中的负面抗议意见进行严格的学术定量内容分析与个案编码。
 
负面评论样本：
"""
{comments_text}
"""
 
请生成一份专业、符合国际核心学术期刊发表标准、高度结构化的【SCCT 学术定量内容分析与危机个案编码报告】。报告应包含以下核心板块，并以精美专业的 Markdown 格式输出：
 
### 🔬 1. 舆论文本议题编码与情绪特征 (Topic Coding & Emotional Profiles)
- **公众舆论核心痛点与编码（Top 3 Issues）**：提取网民最强烈的不满、质疑和诉求，进行语义主题编码，并剖析其深层社会心理动因。
- **情感危机烈度与声誉危害评估 (Reputational Threat Assessment)**：评估负向情感倾斜严重度，量化网民情绪对抗烈度，分析其对品牌象征性社会资本与媒介声誉的短期与长期危害。
 
### 📚 2. SCCT 危机情境学术编码 (SCCT Academic Case-Study Coding)
基于 Coombs 的 SCCT 理论，判断该事件属于以下哪类危机集群（进行严密的学术理论论证，给出具体编码理由及责任归因强度的研判）：
- **受害者集群 (Victim Cluster)**：组织被视为外部被侵害方（如自然灾害、谣言抹黑、外部恶意入侵）。归因责任：极低 (Minimal Attribution)。
- **事故集群 (Accidental Cluster)**：组织非蓄意但因技术、操作故障诱发（如意外设备故障、非恶意产品缺陷）。归因责任：中等 (Moderate Attribution)。
- **可防范集群 (Preventable Cluster)**：组织故意违法违规或管理严重失职、知情隐瞒不报导致。归因责任：极高 (Severe Attribution)。
 
### 📈 3. 基于 SCCT 模型的理论化应对策略矩阵 (Theoretical Strategy Matrix)
根据前面的危机编码，推荐采取何种危机沟通响应策略（提供符合 Coombs 理论框架的策略配比建议，并给出学术性话术要点指导）：
- **否认策略 (Denial)**：划清界限、驳斥谣言或强调组织无辜。（适用受害者集群，低归因责任）
- **淡化策略 (Diminish)**：强调外部客观因素，重申损害可控，降低公众对危机严重性的感知。（适用事故集群，中等归因责任）
- **重塑策略 (Rebuild)**：诚恳道歉，承担全部责任，并提供实质性补偿（Compensation）与纠正措施（Corrective Action）。（适用可防范/严重事故集群，高归因责任）
- **迎合/强化策略 (Bolstering)**：提醒公众组织过去的良好记录，对支持者表示感谢，重建信任纽带。
 
### 📝 4. 危机响应个案研究双语示范文本设计 (Bilingual Narrative Research Design)
提供一版用于本案例实证研究参考官方声明/道歉信学术模型样本：
- **中文版本 (Chinese Empirical Template)**
- **英文版本 (English Empirical Template)**
- **文本修辞学与叙事要点解析**：从叙事学和修辞学角度，阐明该文本设计如何有效对应危机责任规避或公众情感修复（例如：优先关注受害人利益、展现主动纠错担当、承诺具体的后续整改路线）。
 
### 📖 5. 学术参考文献 (APA 7th Edition References)
列出报告中引用的主要 SCCT 理论与计算传播学核心学术文献列表，必须采用严格的 **APA 第 7 版标准学术参考文献格式**。至少包含 Timothy Coombs 的经典论文与专著。
'''
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # 弹性候选模型列表
        candidate_models = [model_name] if model_name else []
        candidate_models.extend(["gemini-1.5-flash", "gemini-2.0-flash", "gemini-pro"])
        seen = set()
        candidate_models = [x for x in candidate_models if not (x in seen or seen.add(x))]
        
        response = None
        last_err = ""
        
        for m_name in candidate_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt)
                break  # 成功生成即跳出循环
            except Exception as e:
                last_err = str(e)
                # 只有遇到模型名称不匹配或API版本/型号不支持报错时才继续尝试候选模型
                if "404" in last_err or "not found" in last_err.lower() or "not supported" in last_err.lower() or "not_found" in last_err.lower():
                    continue
                else:
                    raise e # 其它关键错误（如 API Key 校验/Quota限流）直接抛出
                    
        if response is None:
            raise RuntimeError(f"已尝试所有候选模型 {candidate_models}，均不可用。最后一次模型报错信息: {last_err}")
            
        return response.text
    except Exception as e:
        err_msg = str(e)
        return get_static_crisis_handbook(err_msg)


def generate_scct_insights_custom_api(negative_comments: List[str], api_key: str, base_url: str, model_name: str) -> str:
    """
    【商业危机管理模块】使用自定义 OpenAI 兼容 API 基于 Coombs 的 SCCT（情境危机传播理论）提供系统公关策略。
    """
    if not api_key:
        return "⚠️ 请在左侧参数配置面板输入 API Key 以激活 SCCT 公关战略模块。"
        
    if not negative_comments:
        return "💡 暂未检测到明显的负面言论，品牌声誉安全，无需触发 SCCT 危机预案。"
 
    sample_comments = negative_comments[:40]
    comments_text = "\n".join([f"- {c}" for c in sample_comments])
 
    prompt = f"""
你是一名资深传播学学者和计算社会学（Computational Social Science）科研专家。请根据 Coombs 的 **情境危机传播理论 (Situational Crisis Communication Theory, SCCT)**，对以下 YouTube 视频语料中的负面抗议意见进行严格的学术定量内容分析与个案编码。
 
负面评论样本：
\"\"\"
{comments_text}
\"\"\"
 
请生成一份专业、符合国际核心学术期刊发表标准、高度结构化的【SCCT 学术定量内容分析与危机个案编码报告】。报告应包含以下核心板块，并以精美专业的 Markdown 格式输出：
 
### 🔬 1. 舆论文本议题编码与情绪特征 (Topic Coding & Emotional Profiles)
- **公众舆论核心痛点与编码（Top 3 Issues）**：提取网民最强烈的不满、质疑和诉求，进行语义主题编码，并剖析其深层社会心理动因。
- **情感危机烈度与声誉危害评估 (Reputational Threat Assessment)**：评估负向情感倾斜严重度，量化网民情绪对抗烈度，分析其对品牌象征性社会资本与媒介声誉的短期与长期危害。
 
### 📚 2. SCCT 危机情境学术编码 (SCCT Academic Case-Study Coding)
基于 Coombs 的 SCCT 理论，判断该事件属于以下哪类危机集群（进行严密的学术理论论证，给出具体编码理由及责任归因强度的研判）：
- **受害者集群 (Victim Cluster)**：组织被视为外部被侵害方（如自然灾害、谣言抹黑、外部恶意入侵）。归因责任：极低 (Minimal Attribution)。
- **事故集群 (Accidental Cluster)**：组织非蓄意但因技术、操作故障诱发（如意外设备故障、非恶意产品缺陷）。归因责任：中等 (Moderate Attribution)。
- **可防范集群 (Preventable Cluster)**：组织故意违法违规或管理严重失职、知情隐瞒不报导致。归因责任：极高 (Severe Attribution)。
 
### 📈 3. 基于 SCCT 模型的理论化应对策略矩阵 (Theoretical Strategy Matrix)
根据前面的危机编码，推荐采取何种危机沟通响应策略（提供符合 Coombs 理论框架的策略配比建议，并给出学术性话术要点指导）：
- **否认策略 (Denial)**：划清界限、驳斥谣言或强调组织无辜。（适用受害者集群，低归因责任）
- **淡化策略 (Diminish)**：强调外部客观因素，重申损害可控，降低公众对危机严重性的感知。（适用事故集群，中等归因责任）
- **重塑策略 (Rebuild)**：诚恳道歉，承担全部责任，并提供实质性补偿（Compensation）与纠正措施（Corrective Action）。（适用可防范/严重事故集群，高归因责任）
- **迎合/强化策略 (Bolstering)**：提醒公众组织过去的良好记录，对支持者表示感谢，重建信任纽带。
 
### 📝 4. 危机响应个案研究双语示范文本设计 (Bilingual Narrative Research Design)
提供一版用于本案例实证研究参考的官方声明/道歉信学术模型样本：
- **中文版本 (Chinese Empirical Template)**
- **英文版本 (English Empirical Template)**
- **文本修辞学与叙事要点解析**：从叙事学和修辞学角度，阐明该文本设计如何有效对应危机责任规避或公众情感修复（例如：优先关注受害人利益、展现主动纠错担当、承诺具体的后续整改路线）。
 
### 📖 5. 学术参考文献 (APA 7th Edition References)
列出报告中引用的主要 SCCT 理论与计算传播学核心学术文献列表，必须采用严格的 **APA 第 7 版标准学术参考文献格式**。至少包含 Timothy Coombs 的经典论文与专著。
"""
    # 规范化 URL
    url = base_url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    if not url.rstrip("/").endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
 
    try:
        import requests
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        err_msg = str(e)
        return get_static_crisis_handbook(err_msg)


def get_static_crisis_handbook(err_msg: str) -> str:
    """
    提供标准跨区域危机公关应对指南与双语道歉大纲（离线公关自诊断中枢）
    """
    static_handbook = f"""
### 🚨 AI 决策引擎触发配额熔断 / 限流保护 (Rate Limit & Quota Exceeded)
 
> **⚠️ 提示**：检测到您的 AI 接口调用目前已达到额度限制、触发频率限流或连接异常（原始报错：{err_msg}）。
> 为了不影响您的决策，根据 **SCCT 危机公关理论防御性原则**，系统已自动启动**「离线危机公关自诊断中枢」**，为您提供标准的跨区域公关应对指南与双语通用道歉大纲。
 
---
 
# 📚 《出海企业标准 SCCT 危机沟通自诊断手册》
*(Timothy Coombs 教授情境危机传播理论标准版)*
 
在缺乏实时 AI 分析时，请依据本手册分步进行品牌舆情自诊断：
 
## 📌 第一步：舆情事件责任定性 (Attribution of Responsibility)
根据负面评论的爆发诱因，对照下表确定事件属于哪类 **SCCT 危机集群 (Crisis Cluster)**：
 
| 危机集群 (Cluster) | 现实场景实例 (Examples) | 网民责任归因 (Attribution) | 推荐核心公关态度 (Posture) |
| :--- | :--- | :--- | :--- |
| **受害者集群 (Victim)** | 谣言恶意抹黑、自然灾害、外部骇客攻击 | 极低 (Minimal) | **驳斥与澄清 (Denial)** / 划清界限 |
| **事故集群 (Accidental)** | 技术突发故障、非恶意产品设计缺陷、供应链延误 | 中等 (Moderate) | **淡化客观原因 (Diminish)** + 修正承诺 |
| **可防范集群 (Preventable)** | 故意违法违规、管理严重失职、知情隐瞒不报 | 极高 (Severe) | **彻底重塑信任 (Rebuild)** + 赔偿与整改 |
 
---
 
## 📈 第二步：公关战略响应矩阵 (SCCT Response Matrix)
请根据第一步的分类，针对性采取以下公关话术切入点：
 
### 1. 否认与澄清策略 (Denial Strategy) —— *适用于受害者集群*
- **核心切入点**：证明公司与起因无关，或指明恶意来源。
- **公关原则**：言简意赅，用客观数据说话，不激怒网民。
 
### 2. 淡化与隔离策略 (Diminish Strategy) —— *适用于事故集群*
- **核心切入点**：阐明这是小概率单点突发事故，强调公司已启动纠错，证明危害在可控范围内。
- **公关原则**：表达遗憾但不主动招揽无端指责。
 
### 3. 重塑与纠正策略 (Rebuild Strategy) —— *适用于可防范集群/严重事故*
- **核心切入点**：**“黄金24小时”内彻底道歉**。不推诿、不寻找客观借口。宣布成立专项小组，并公布具体的**赔偿计划 (Compensation)** 与 **纠正整改路线图 (Corrective Action)**。
- **公关原则**：坦诚是唯一的解药，整改动作必须可衡量。
 
---
 
## 📝 第三步：通用品牌公关响应双语模版 (Off-the-shelf Crisis Templates)
 
若您急需发布声明，请根据事件性质参考以下**模块化公关模版**进行措辞微调：
 
### 🟢 模版 A：技术突发与产品故障通用稿 (适用于事故集群)
```markdown
【中文声明】
我们深知，近日发生的 [填写事件，例如：服务短暂中断/部分产品出货延误] 给广大用户带来了极大的不便。对此，我们表示最诚挚的歉意。
经核查，本次事件由 [填写具体客观原因，例如：海外服务器瞬时网络波动] 导致。我们已于第一时间内完成技术修复，目前系统已全面恢复平稳。
作为一家负责任的企业，我们已启动服务保障机制，并将全力避免此类事故再次发生。
 
【English Version】
We sincerely apologize for the recent [e.g., service disruption / product delivery delay] that caused inconvenience to our valued users. 
Upon investigation, this was due to [e.g., unexpected regional server fluctuation]. Our engineering team resolved the issue immediately, and services are fully restored.
We take this matter seriously and are implementing additional safeguards to ensure systemic stability.
```
 
### 🔴 模版 B：管理失职与服务漏洞通用道歉信 (适用于可防范集群)
```markdown
【中文道歉信】
近日，关于 [填写曝光事件] 的报道引发了社会的广泛关注与网民批评。在此，我们不作任何辩解，郑重地向受影响的客户及公众致以最深的歉意。
这暴露出我们在 [填写管理漏洞，例如：海外售后响应/供应链质量把控] 上的严重缺失。我们已成立由 CEO 挂帅的专项整改小组，并承诺采取以下措施：
1. 立即开展全渠道服务审计与整改。
2. 对受影响用户提供 [填写具体补偿方案]。
3. 设立公开监督渠道，定期向公众汇报进展。
 
【English Version】
We deeply apologize for the recent events regarding [e.g., customer service oversight]. We accept full responsibility and make no excuses.
This incident exposed significant vulnerabilities in our [e.g., quality control / service response]. We have established an immediate task force led by our CEO to implement the following actions:
1. Conduct an immediate channel-wide operational audit.
2. Provide [e.g., compensation / refunds] to affected users.
3. Establish a transparent communication line to report our progress.
```
 
---
*(若需恢复高精度 AI 舆情研判与定制化道歉声明，请确认您的 API 额度充足或更换高可用的 API Key / 基础端点。)*
"""
    return static_handbook
 
def parse_keywords(keyword_text: str) -> List[str]:
    """解析多关键词输入，支持中英文逗号和空格分隔。"""
    if not keyword_text or not keyword_text.strip():
        return []
    tokens = re.split(r"[\s,，]+", keyword_text.strip())
    return [k.strip() for k in tokens if k.strip()]


def _extract_http_error_info(err: HttpError) -> Tuple[Optional[int], str, str]:
    """提取 HttpError 中的核心信息。"""
    status_code = getattr(getattr(err, "resp", None), "status", None)
    reason = ""
    message = ""
    try:
        payload = err.content.decode("utf-8") if isinstance(err.content, bytes) else str(err.content)
        body = json.loads(payload)
        err_obj = body.get("error", {}) if isinstance(body, dict) else {}
        if isinstance(err_obj.get("errors"), list) and err_obj["errors"]:
            reason = str(err_obj["errors"][0].get("reason", ""))
        message = str(err_obj.get("message", ""))
    except Exception:
        pass
    if not message:
        message = str(err)
    return status_code, reason, message


def _is_quota_exceeded(err: HttpError) -> bool:
    """判断是否为 API 配额耗尽。"""
    status_code, reason, message = _extract_http_error_info(err)
    text = f"{reason} {message} {err}".lower()
    return bool(status_code == 403 and ("quotaexceeded" in text or "quota" in text))


def _is_comments_disabled(err: HttpError) -> bool:
    """判断是否为视频评论区关闭。"""
    _, reason, message = _extract_http_error_info(err)
    text = f"{reason} {message} {err}".lower()
    return "commentsdisabled" in text


def _is_invalid_api_key(err: HttpError) -> bool:
    """判断是否为无效 API Key。"""
    _, reason, message = _extract_http_error_info(err)
    text = f"{reason} {message} {err}".lower()
    return "keyinvalid" in text or "api key not valid" in text or ("forbidden" in text and "key" in text)


def fetch_youtube_data(api_key: str, keyword_text: str, max_items: int) -> Tuple[pd.DataFrame, bool]:
    """
    根据多关键词抓取 YouTube 相关视频的顶层评论。
    支持自动关闭评论视频跳过、配额耗尽熔断等极高容错设计。
    """
    if not api_key:
        raise ValueError("请先输入 YouTube API Key。")

    keywords = parse_keywords(keyword_text)
    if not keywords:
        raise ValueError("请输入至少一个关键词，并用逗号或空格分隔。")

    try:
        youtube = build("youtube", "v3", developerKey=api_key)
    except Exception as exc:
        raise RuntimeError("YouTube API 客户端初始化失败，请检查 API Key。") from exc

    all_rows: List[Dict] = []
    quota_exceeded = False
    seen_video_ids = set()

    empty_df = pd.DataFrame(columns=[
        "video_id",
        "video_title",
        "keyword",
        "comment_id",
        "comment_text",
        "published_at",
        "like_count",
        "author",
    ])

    try:
        for keyword in keywords:
            if len(all_rows) >= max_items or quota_exceeded:
                break

            search_token = None

            while len(all_rows) < max_items and not quota_exceeded:
                try:
                    search_request = youtube.search().list(
                        q=keyword,
                        part="snippet",
                        type="video",
                        maxResults=50,
                        pageToken=search_token,
                        order="relevance",
                    )
                    search_response = search_request.execute()
                except HttpError as err:
                    if _is_quota_exceeded(err):
                        quota_exceeded = True
                        break
                    if _is_invalid_api_key(err):
                        raise RuntimeError("YouTube API Key 无效，请检查输入。") from err
                    raise RuntimeError(f"搜索视频失败: {err}") from err

                video_items = search_response.get("items", [])
                if not video_items:
                    break

                for video_item in video_items:
                    if len(all_rows) >= max_items or quota_exceeded:
                        break

                    vid = video_item.get("id", {}).get("videoId")
                    if not vid or vid in seen_video_ids:
                        continue

                    seen_video_ids.add(vid)
                    video_title = video_item.get("snippet", {}).get("title", "")
                    comments_token = None

                    while len(all_rows) < max_items:
                        try:
                            comments_req = youtube.commentThreads().list(
                                part="snippet",
                                videoId=vid,
                                maxResults=min(100, max_items - len(all_rows)),
                                pageToken=comments_token,
                                textFormat="plainText",
                                order="time",
                            )
                            comments_resp = comments_req.execute()
                        except HttpError as err:
                            if _is_comments_disabled(err):
                                st.warning(f"⚠️ [跳过关闭评论区的视频] ID: {vid} | Title: {video_title[:30]}...")
                                break

                            if _is_quota_exceeded(err):
                                quota_exceeded = True
                                break

                            if _is_invalid_api_key(err):
                                raise RuntimeError("YouTube API Key 无效，请检查。") from err

                            st.warning(f"⚠️ 视频 {vid} 评论抓取受阻: {err}")
                            break

                        comment_items = comments_resp.get("items", [])
                        if not comment_items:
                            break

                        for item in comment_items:
                            snippet = (
                                item.get("snippet", {})
                                .get("topLevelComment", {})
                                .get("snippet", {})
                            )

                            all_rows.append(
                                {
                                    "video_id": vid,
                                    "video_title": video_title,
                                    "keyword": keyword,
                                    "comment_id": item.get("id", ""),
                                    "comment_text": snippet.get("textDisplay", ""),
                                    "published_at": snippet.get("publishedAt", ""),
                                    "like_count": snippet.get("likeCount", 0),
                                    "author": snippet.get("authorDisplayName", ""),
                                }
                            )

                            if len(all_rows) >= max_items:
                                break

                        if quota_exceeded or len(all_rows) >= max_items:
                            break

                        comments_token = comments_resp.get("nextPageToken")
                        if not comments_token:
                            break

                if quota_exceeded:
                    break

                search_token = search_response.get("nextPageToken")
                if not search_token:
                    break

    except HttpError as err:
        if _is_quota_exceeded(err):
            quota_exceeded = True
        elif _is_invalid_api_key(err):
            raise RuntimeError("YouTube API Key 无效。") from err
        else:
            raise RuntimeError(f"YouTube 接口请求失败: {err}") from err
    except Exception as err:
        raise RuntimeError(f"舆情数据抓取中发生严重未知错误: {err}") from err

    if not all_rows:
        return empty_df, quota_exceeded

    return pd.DataFrame(all_rows), quota_exceeded


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """结构化字段清洗与时序转换。"""
    if df.empty:
        return df

    out = df.copy()
    out["published_at"] = pd.to_datetime(out["published_at"], errors="coerce", utc=True)
    out = out.dropna(subset=["published_at"])
    out["date"] = out["published_at"].dt.date.astype(str)
    out["month"] = out["published_at"].dt.to_period("M").astype(str)
    out["like_count"] = pd.to_numeric(out["like_count"], errors="coerce").fillna(0).astype(int)
    out["comment_text"] = out["comment_text"].fillna("").astype(str)
    out["author"] = out["author"].fillna("").astype(str)

    return out


def apply_plotly_theme(fig):
    """【UI/UX升级】统一 Plotly 交互图表的高级商业主题配色"""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color="#94a3b8"),
        title=dict(font=dict(size=15, color="#ffffff")),
        legend=dict(font=dict(size=11, color="#94a3b8")),
        margin=dict(l=40, r=40, t=50, b=40),
    )
    # 只有当图表包含 x/y 轴时才尝试更新，防止饼图等无轴图表在某些Plotly版本下崩溃
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



def build_wordcloud_image(df: pd.DataFrame):
    """构建高对比度词云图片对象（支持中英文分词）。"""
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
        "C:\\Windows\\Fonts\\simhei.ttf", # Windows 黑体
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    font_path = next((f for f in font_candidates if os.path.exists(f)), None)

    wc = WordCloud(
        width=1200,
        height=500,
        background_color="#0b0d12",
        max_words=200,
        collocations=False,
        font_path=font_path,
        colormap="plasma", # 使用高级色彩图
    ).generate(text_blob)
    return wc.to_image()


def render_dashboard(df: pd.DataFrame):
    """舆情大屏分析页面的渲染"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="section-title">📈 舆情数量时序波动（日）</div>', unsafe_allow_html=True)
        trend_daily = df.groupby("date", as_index=False).size().rename(columns={"size": "comment_count"})
        
        # 渐变紫色折线设计
        fig_line = px.line(
            trend_daily,
            x="date",
            y="comment_count",
            markers=True,
            color_discrete_sequence=["#8b5cf6"]
        )
        fig_line.update_traces(line=dict(width=3), marker=dict(size=8, symbol="circle"))
        apply_plotly_theme(fig_line)
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col2:
        st.markdown('<div class="section-title">🍩 整体情绪分布占比</div>', unsafe_allow_html=True)
        sentiment_dist = (
            df.groupby("sentiment", as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )
        
        # 统一高级语义色系映射
        fig_pie = px.pie(
            sentiment_dist,
            names="sentiment",
            values="count",
            hole=0.55,
            color="sentiment",
            color_discrete_map={
                "喜悦": "#10b981", # Emerald
                "悲伤": "#3b82f6", # Blue
                "愤怒": "#ef4444", # Red
                "恐惧": "#8b5cf6", # Purple
                "厌恶": "#f59e0b", # Amber
                "惊讶": "#ec4899", # Pink
                "中立": "#64748b", # Slate
                "positive": "#10b981",
                "neutral": "#64748b",
                "negative": "#ef4444",
            },
        )
        apply_plotly_theme(fig_pie)
        st.plotly_chart(fig_pie, use_container_width=True)


# ==========================================
# 📊 PHASE 2: ADVANCED DATA ANALYSIS MODULES
# ==========================================

def plot_competitive_keywords(df: pd.DataFrame):
    """竞品与关键词维度多维对比分析。"""
    if "keyword" not in df.columns or df["keyword"].nunique() <= 1:
        st.markdown('<div class="section-title">⚔️ 多维竞品对比透视</div>', unsafe_allow_html=True)
        st.info("💡 竞品对比分析激活中：当前抓取任务仅包含单个关键词。若要激活本分析模块，请在侧边栏中配置多个关键词（如：'特斯拉, 比亚迪, 小米汽车' 逗号分隔）。")
        return
        
    st.markdown('<div class="section-title">⚔️ 多维竞品对比透视</div>', unsafe_allow_html=True)
    
    # 汇总竞品基本指标
    stats = df.groupby("keyword").agg(
        total_comments=("comment_id", "count"),
        avg_sentiment=("sentiment_score", "mean"),
        avg_likes=("like_count", "mean")
    ).reset_index()
    
    # 情感占比透视
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
            title="各竞品评论声量（柱高）与平均情绪指数（颜色偏黄表示积极）",
            labels={"total_comments": "评论总量", "avg_sentiment": "平均情绪得分"}
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
            color_discrete_map={
                "喜悦": "#10b981", # Emerald
                "悲伤": "#3b82f6", # Blue
                "愤怒": "#ef4444", # Red
                "恐惧": "#8b5cf6", # Purple
                "厌恶": "#f59e0b", # Amber
                "惊讶": "#ec4899", # Pink
                "中立": "#64748b", # Slate
                "positive": "#10b981",
                "neutral": "#64748b",
                "negative": "#ef4444",
            },
            labels={"percentage": "占比百分比 (%)", "sentiment": "情绪属性"}
        )
        apply_plotly_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)


def plot_engagement_correlation(df: pd.DataFrame):
    """用户点赞交互数与评论文本字数的相关性深度探针 (Pearson r)。"""
    st.markdown('<div class="section-title">🔍 用户点赞数与评论文本长度的相关性探针</div>', unsafe_allow_html=True)
    
    df_copy = df.copy()
    df_copy["comment_length"] = df_copy["comment_text"].str.len()
    
    # 计算 Pearson 皮尔逊相关系数
    corr = df_copy["comment_length"].corr(df_copy["like_count"])
    if pd.isna(corr):
        corr = 0.0
        
    # 相关性强度判定
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
                <div class="metric-subtitle" style="font-weight: 600; color: {color}; font-size:13px; margin-top:8px;">结论：{interpretation}</div>
                <p style="font-size: 12px; color: #64748b; margin-top: 15px; line-height: 1.6;">
                    皮尔逊相关系数用来衡量两个变量的线性关联强度，范围在 [-1, 1]：<br/>
                    • <b>r > 0</b>: 评论越长，获得点赞越多（可能长文更有逻辑）。<br/>
                    • <b>r < 0</b>: 评论越短，点赞数越多（可能短评梗词更吸睛）。<br/>
                    • <b>r 趋于 0</b>: 长度与点赞无显著关联。
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with c2:
        # 为了保证散点图不被极端大点赞数据挤压，限制散点展现至 98% 分位数
        q_like = df_copy["like_count"].quantile(0.98)
        scatter_data = df_copy[df_copy["like_count"] <= max(q_like, 15)]
        
        fig = px.scatter(
            scatter_data,
            x="comment_length",
            y="like_count",
            color="sentiment",
            size=scatter_data["like_count"].apply(lambda v: max(v, 3)),
            hover_data=["author", "comment_text"],
            title="评论字符字数 vs 获得点赞数（已剔除极端尖峰值）",
            color_discrete_map={
                "喜悦": "#10b981", # Emerald
                "悲伤": "#3b82f6", # Blue
                "愤怒": "#ef4444", # Red
                "恐惧": "#8b5cf6", # Purple
                "厌恶": "#f59e0b", # Amber
                "惊讶": "#ec4899", # Pink
                "中立": "#64748b", # Slate
                "positive": "#10b981",
                "neutral": "#64748b",
                "negative": "#ef4444",
            },
            labels={"comment_length": "评论字符长度 (Chars)", "like_count": "点赞数 (Likes)", "sentiment": "情感"}
        )
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)


def plot_temporal_heatmap(df: pd.DataFrame):
    """舆情时段密度活跃度热力图（周几 vs 一天的小时）。"""
    st.markdown('<div class="section-title">📅 舆情活动周/时密度热力透视</div>', unsafe_allow_html=True)
    
    df_copy = df.copy()
    df_copy["published_at"] = pd.to_datetime(df_copy["published_at"], utc=True)
    
    df_copy["hour"] = df_copy["published_at"].dt.hour
    df_copy["day_of_week"] = df_copy["published_at"].dt.day_name()
    
    # 星期排序列表
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_cn = {
        "Monday": "周一 (Mon)", "Tuesday": "周二 (Tue)", "Wednesday": "周三 (Wed)",
        "Thursday": "周四 (Thu)", "Friday": "周五 (Fri)", "Saturday": "周六 (Sat)", "Sunday": "周日 (Sun)"
    }
    
    # 透视表
    heatmap_data = df_copy.groupby(["day_of_week", "hour"]).size().unstack(fill_value=0)
    heatmap_data = heatmap_data.reindex(weekday_order, fill_value=0)
    heatmap_data.index = [weekday_cn[d] for d in heatmap_data.index]
    
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="一天中的小时 (Hour of Day)", y="星期 (Day of Week)", color="评论活跃数"),
        x=list(range(24)),
        y=heatmap_data.index.tolist(),
        color_continuous_scale="Viridis",
        title="舆情发帖活动密度分布（发现用户发声最密集的时间窗口）"
    )
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    
    # 计算波峰时段
    flat_data = df_copy.groupby(["day_of_week", "hour"]).size().reset_index(name="count")
    if not flat_data.empty:
        peak = flat_data.loc[flat_data["count"].idxmax()]
        day_cn = weekday_cn[peak['day_of_week']].split(' ')[0]
        st.markdown(
            f"""
            💡 **危机公关监控建议**：监测显示，本项任务中最密集的互动爆发时段位于 **{day_cn} 的 {peak['hour']}:00 - {peak['hour']+1}:00** (爆发了 **{peak['count']}** 条评论)。
            建议品牌公关团队在该活跃窗口期**增强巡检，对发帖高度集中的舆论倾向进行秒级防范**。
            """
        )


def plot_rolling_sentiment(df: pd.DataFrame):
    """情感时序移动平均衰减走势（舆情平息/复苏/恶化趋势）。"""
    st.markdown('<div class="section-title">📈 情感移动平均时序衰减线 (舆情恶化/修复曲线)</div>', unsafe_allow_html=True)
    
    # 按发帖时间升序排列
    df_sorted = df.sort_values("published_at").copy()
    
    # 动态平滑窗口大小（取总样本的 5%，但最小为 10 条）
    window_size = max(10, int(len(df_sorted) * 0.05))
    df_sorted["rolling_sentiment"] = df_sorted["sentiment_score"].rolling(window=window_size, min_periods=5).mean()
    
    fig = px.line(
        df_sorted,
        x="published_at",
        y="rolling_sentiment",
        title=f"时间轴平滑情感轨迹线 (滑动平均窗口：前 {window_size} 条评论)",
        color_discrete_sequence=["#8b5cf6"]
    )
    
    # 添加中立基准线
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
        font=dict(color="rgba(244,63,94,0.6)", size=10)
    )
    
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    
    # 趋势分析提示
    if len(df_sorted) > window_size * 2:
        start_sentiment = df_sorted["rolling_sentiment"].iloc[window_size : window_size*2].mean()
        end_sentiment = df_sorted["rolling_sentiment"].iloc[-window_size:].mean()
        delta = end_sentiment - start_sentiment
        
        if delta > 0.05:
            st.markdown("📈 **舆情态势研判：正向回暖！** 移动窗口中评论情感值呈现明确上扬趋势，说明负面情绪正在平息，公关危机得到阶段性控制。")
        elif delta < -0.05:
            st.markdown("📉 **舆情态势研判：负向恶化！** 近期情绪表现出明显的下滑趋势。网民负向情绪在淤积且无好转迹象，可能存在第二波舆情次生灾害风险，需紧急干预！")
        else:
            st.markdown("📊 **舆情态势研研：震荡僵持。** 滑动情感得分平稳，代表网民态度对立中和，舆论热点正处于稳步消耗阶段。")


def plot_semantic_clustering(df: pd.DataFrame):
    """【学术级机器学习新增功能】使用 TF-IDF + K-Means + PCA 进行评论的主题聚类与降维可视化"""
    st.markdown('<div class="section-title">🔮 评论语义聚类与学术话题阵营提炼</div>', unsafe_allow_html=True)
    
    # 提取评论文本并去重、清理空值
    comments = df["comment_text"].dropna().astype(str).tolist()
    if len(comments) < 15:
        st.info("💡 聚类分析激活条件：当前抓取的评论样本过少（少于 15 条），建议在侧边栏增大采样深度后再体验机器学习聚类功能。")
        return
        
    st.markdown(
        """
        利用机器学习非监督算法将网民评论转化为高维 TF-IDF 语义向量，通过 **K-Means** 聚类划分为不同的“话题阵营”，最后使用 **主成分分析 (PCA)** 将高维空间降维投影至二维，实现公众讨论焦点的科学聚类分布透视。
        """
    )
    
    # 侧边栏/小面板配置聚类数 K
    n_clusters = st.slider("选择话题聚类簇数 (K)", min_value=2, max_value=6, value=4, help="K 代表网民发言主要集中的对立或发散的话题阵营数")
    
    with st.spinner("正在进行 TF-IDF 向量化与 K-Means 聚类运算..."):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.cluster import KMeans
            from sklearn.decomposition import PCA
            import numpy as np
            import jieba
            
            # 对中文评论进行分词，以便 TF-IDF 向量化
            tokenized_comments = []
            for comment in comments:
                if contains_chinese(comment):
                    # 中文分词
                    words = jieba.cut(comment)
                    # 过滤停用词/短词
                    words_filtered = [w.strip() for w in words if len(w.strip()) > 1]
                    tokenized_comments.append(" ".join(words_filtered))
                else:
                    tokenized_comments.append(comment.lower())
                    
            # 建立 TF-IDF 矩阵
            vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(tokenized_comments)
            
            # K-Means 聚类
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # PCA 降维至 2D
            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(tfidf_matrix.toarray())
            
            # 构造可视化 DataFrame
            plot_data = df.copy()
            plot_data["x"] = coords[:, 0]
            plot_data["y"] = coords[:, 1]
            plot_data["cluster"] = [f"Topic {label + 1}" for label in cluster_labels]
            # 为了防止 hover 时内容过长影响显示，截取前 80 个字符
            plot_data["comment_preview"] = plot_data["comment_text"].apply(lambda t: t[:80] + "..." if len(t) > 80 else t)
            
            # 获取每个簇的 top keywords
            terms = vectorizer.get_feature_names_out()
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            
            cluster_keywords = {}
            for i in range(n_clusters):
                top_terms = [terms[ind] for ind in order_centroids[i, :5]]
                cluster_keywords[f"Topic {i + 1}"] = top_terms
                
            # 渲染图表
            col1, col2 = st.columns([2.5, 1])
            
            with col1:
                fig = px.scatter(
                    plot_data,
                    x="x",
                    y="y",
                    color="cluster",
                    size=plot_data["like_count"].apply(lambda v: max(v, 4)), # 点的大小取决于点赞数
                    hover_data=["author", "like_count", "comment_preview", "sentiment"],
                    title=f"评论语义高维映射与 PCA 2D 投影图 (聚类簇 K={n_clusters})",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_traces(marker=dict(opacity=0.75, line=dict(width=1, color="rgba(255,255,255,0.15)")))
                apply_plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.markdown("##### 🔑 各话题阵营高频语义特征")
                
                # 为每个聚类阵营渲染一个高雅的 Glassmorphic 话题特征卡片
                cluster_colors = px.colors.qualitative.Pastel
                for i in range(n_clusters):
                    topic_name = f"Topic {i + 1}"
                    kw_list = cluster_keywords[topic_name]
                    kw_tags_html = " ".join([f"<span style='background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 2px 8px; margin-right: 6px; display: inline-block; margin-bottom: 6px; font-size:12px; color:#cbd5e1;'>🏷️ {kw}</span>" for kw in kw_list])
                    
                    # 计算该 Topic 下评论的平均情感得分和占比
                    topic_subset = plot_data[plot_data["cluster"] == topic_name]
                    avg_score = topic_subset["sentiment_score"].mean()
                    total_pct = len(topic_subset) / len(plot_data) * 100
                    
                    st.markdown(
                        f"""
                        <div class="metric-card" style="padding: 16px; border-left: 4px solid {cluster_colors[i % len(cluster_colors)]}; margin-bottom: 12px;">
                            <div class="metric-title" style="font-size:12px; color:#cbd5e1; font-weight:700;">🗣️ 话题阵营 {i + 1} ({total_pct:.1f}%)</div>
                            <div style="margin-top: 8px; margin-bottom: 10px;">
                                {kw_tags_html}
                            </div>
                            <div style="font-size: 11px; color:#94a3b8;">
                                情感倾向度均值：<b style="color: { '#10b981' if avg_score >= 0.55 else '#ef4444' if avg_score <= 0.45 else '#64748b' }">{avg_score:.2f}</b> (0代表极端消极, 1代表极端积极)
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
            st.divider()
            
            # 展示各 Topic 的典型评论
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
                            sentiment_border = "quote-card-pos" if row["sentiment"] == "positive" else "quote-card-neg" if row["sentiment"] == "negative" else ""
                            with col_to_use:
                                st.markdown(
                                    f"""
                                    <div class="quote-card {sentiment_border}">
                                        <div class="quote-author">👤 {row['author']} <span style='float:right;'>👍 {row['like_count']} Likes</span></div>
                                        <div class="quote-text">“{row['comment_text']}”</div>
                                        <div class="quote-meta">情感得分: {row['sentiment_score']:.2f} | 话题划分: {topic_name}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
        except Exception as e:
            st.error(f"聚类分析过程中发生异常：{e}")
            st.info("提示：这通常是由于评论中没有足够的词汇建立特征矩阵导致，请尝试增大采样评论数量。")


# ==========================================
# 📋 CORE RENDER LOGIC
# ==========================================

def render_extreme_quotes(df: pd.DataFrame):
    """深度透视页面中，提取用户高权重（Like高）评论"""
    st.markdown('<div class="section-title">🔍 核心舆论风向标：高赞观点追踪</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    # 提取高赞的正面评论
    pos_df = df[df["sentiment"].isin(["喜悦", "惊讶", "positive"])].sort_values(by="like_count", ascending=False).head(5)
    with c1:
        st.markdown("##### 🟢 典型正面回响 (Top 5 热门正面意见)")
        if pos_df.empty:
            st.info("暂无正面高赞意见。")
        else:
            for _, row in pos_df.iterrows():
                st.markdown(
                    f"""
                    <div class="quote-card quote-card-pos">
                        <div class="quote-author">👤 {row['author']} <span style='float:right; color:#10b981;'>👍 {row['like_count']} Likes</span></div>
                        <div class="quote-text">“{row['comment_text']}”</div>
                        <div class="quote-meta">来自视频：{row['video_title'][:40]}... | 情绪分类: {row['sentiment']} | 评分: {row['sentiment_score']:.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
    # 提取高赞的负面评论
    neg_df = df[df["sentiment"].isin(["愤怒", "悲伤", "恐惧", "厌恶", "negative"])].sort_values(by="like_count", ascending=False).head(5)
    with c2:
        st.markdown("##### 🔴 关键负面投诉 (Top 5 热门警示言论)")
        if neg_df.empty:
            st.info("健康度极高！未检测到明显的负面批评言论。")
        else:
            for _, row in neg_df.iterrows():
                st.markdown(
                    f"""
                    <div class="quote-card quote-card-neg">
                        <div class="quote-author">👤 {row['author']} <span style='float:right; color:#ef4444;'>👍 {row['like_count']} Likes</span></div>
                        <div class="quote-text">“{row['comment_text']}”</div>
                        <div class="quote-meta">来自视频：{row['video_title'][:40]}... | 情绪分类: {row['sentiment']} | 评分: {row['sentiment_score']:.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )



def calculate_shannon_entropy(df: pd.DataFrame) -> float:
    """
    【学术级统计指标】计算词频的 Shannon 信息熵 (Shannon Entropy)。
    信息熵（H）用于量化文本讨论议题的语义复杂度与发散程度：
    - H 较高：公众讨论词汇丰富，讨论议题发散度高，体现去中心化的自发讨论。
    - H 较低：公众表达极度集中于少数特定词汇（通常伴随协同水军刷屏、情绪极化宣泄或单一核心诉求极度凸显）。
    """
    import collections
    import math
    
    text_list = df["comment_text"].dropna().astype(str).tolist()
    text_blob = " ".join(text_list).strip()
    if not text_blob:
        return 0.0
        
    words = []
    if contains_chinese(text_blob):
        try:
            import jieba
            words = [w for w in jieba.cut(text_blob) if len(w.strip()) > 1]
        except Exception:
            words = [w for w in text_blob.split() if len(w.strip()) > 1]
    else:
        # 英文过滤标点后拆分词汇
        cleaned_text = re.sub(r'[^\w\s]', '', text_blob.lower())
        words = [w for w in cleaned_text.split() if len(w.strip()) > 2]
        
    if not words:
        return 0.0
        
    # 计算词频概率分布
    counts = collections.Counter(words)
    total = len(words)
    
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
        
    return entropy


def calculate_polarization_index(df: pd.DataFrame) -> Tuple[float, str]:
    """
    【传播学极化指标】基于经典 Esteban-Ray 派生模型的舆论极化指数 (Polarization Index)。
    极化分值范围为 [0, 1]：
    - Polarization = 4 * P_pos * P_neg
    用于评估网络社群中正负情感态度的冲突对立烈度。极化值越接近1，表明社群彻底分裂为势均力敌的两大情绪对立阵营（如50/50对撕）。
    """
    total = len(df)
    if total == 0:
        return 0.0, "无数据"
        
    p_pos = df["sentiment"].isin(["喜悦", "惊讶", "positive"]).mean()
    p_neg = df["sentiment"].isin(["愤怒", "悲伤", "恐惧", "厌恶", "negative"]).mean()
    
    polarization = 4 * p_pos * p_neg
    
    if polarization < 0.2:
        desc = "高度共识 (Consensus) - 社区情感呈现显著的一边倒态势"
    elif polarization < 0.5:
        desc = "轻度对立 (Mild Division) - 社区内伴有小范围的异质偏离意见"
    elif polarization < 0.8:
        desc = "中度分裂 (Moderately Polarized) - 社区舆论场已呈现明显对立的两派阵营"
    else:
        desc = "高度极化 (Highly Polarized) - 网民情感极度极化分裂（红绿阵营势均力敌对抗）"
        
    return polarization, desc


def render_metrics(df: pd.DataFrame):
    """【学术级重构】渲染计算传播学与语料特征核心统计量"""
    total = len(df)
    
    # 计算非中立主观发言占比（Subjectivity Rate）
    if total == 0:
        sub_rate = 0.0
    else:
        sub_rate = (df["sentiment"] != "neutral").mean() * 100
        
    # 计算极化指数
    polarization, pol_desc = calculate_polarization_index(df)
    
    # 计算词汇 Shannon 信息熵
    entropy = calculate_shannon_entropy(df)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">📥 语料样本总量 (N)</div>
                <div class="metric-value">{total:,}</div>
                <div class="metric-subtitle">样本抓取层深度：Top-level comments</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🔬 态度主观性指数</div>
                <div class="metric-value" style="background: linear-gradient(135deg, #34d399 0%, #059669 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{sub_rate:.1f}%</div>
                <div class="metric-subtitle">非中立主观语义倾向的发言占比</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">⚖️ 极化指数 (Esteban-Ray)</div>
                <div class="metric-value" style="background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{polarization:.3f}}</div>
                <div class="metric-subtitle" style="font-size:10px; color:#fbbf24; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="{{pol_desc}}">{{pol_desc.split(' ')[0]}}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🌀 语义信息熵 (Shannon H)</div>
                <div class="metric-value" style="background: linear-gradient(135deg, #f87171 0%, #dc2626 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{entropy:.3f}}</div>
                <div class="metric-subtitle">数值越高代表论题语义越发散丰富</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    # Modern Academic Gradient Banner
    st.markdown(
        """
        <div class="header-panel">
            <h1>🔬 计算传播学多语种舆情量化分析平台</h1>
            <p>整合大规模自动采样语料、双算法分类引擎与经典情境危机传播理论（SCCT）的计算社会科学科研控制平台</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar parameters with Academic framing
    with st.sidebar:
        st.header("🔬 学术科研控制台")
        
        # API Keys configuration
        youtube_api_key = st.text_input("YouTube Data API Key", type="password", help="需开通 YouTube Data API v3 权限。")
        
        keyword_text = st.text_input(
            "研究核心关键词 (群)",
            placeholder="例如：新能源汽车, 智能驾驶 AI（逗号/空格分隔）",
            help="输入多个检索项时，系统将合并采样并自动去重处理。",
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
        
        # Engine selections
        sentiment_engine = st.selectbox(
            "🏷️ 文本情感编码引擎",
            ["官方 Google Gemini API", "自定义 OpenAI 兼容 API (如 DeepSeek, OpenAI等)"],
            help="计算传播学大语言模型情感打标引擎。Gemini 官方引擎或自定义 API（支持 DeepSeek 等各类 OpenAI 兼容接口）"
        )
        
        if sentiment_engine == "官方 Google Gemini API":
            gemini_api_key = st.text_input(
                "Gemini API Key",
                type="password",
                value=os.getenv("GEMINI_API_KEY", ""),
                placeholder="AI 学术编码与 LLM 分析所需",
                help="用于解锁高级 AI 危机公关 SCCT 诊断功能和大模型情绪打标。"
            )
            gemini_model = st.text_input(
                "Gemini 模型名称",
                value="gemini-1.5-flash",
                placeholder="例如: gemini-1.5-flash, gemini-2.0-flash, gemini-pro",
                help="您可以手动输入最新的 Gemini 模型名称进行测试。"
            )
            # Define placeholders for custom API variables to avoid NameError
            custom_api_key = ""
            custom_base_url = ""
            custom_model_name = ""
        else:
            custom_api_key = st.text_input(
                "API Key (如 DeepSeek SK)",
                type="password",
                value=os.getenv("CUSTOM_API_KEY", "sk-3131f75b62a2453f859f0fce6719b9b4"),
                placeholder="输入您的 API Key",
                help="例如您的 DeepSeek Key: sk-..."
            )
            custom_base_url = st.text_input(
                "API Base URL",
                value="https://api.deepseek.com",
                placeholder="例如: https://api.deepseek.com",
                help="第三方 OpenAI 兼容 API 的基础接口地址"
            )
            custom_model_name = st.text_input(
                "模型名称 (Model)",
                value="deepseek-chat",
                placeholder="例如: deepseek-chat, deepseek-v4-flash",
                help="所调用的模型名称标识符"
            )
            # Define placeholders for gemini variables to avoid NameError
            gemini_api_key = ""
            gemini_model = ""
        
        enable_scct = st.checkbox("📚 开启 SCCT 学术编码模型", value=True, help="启用后，将使用 Gemini 或自定义 API 自动根据情境危机传播理论对负向文本进行内容分析与学术编码。")
        
        run_btn = st.button("🚀 启动数据工作流", type="primary", use_container_width=True)

    # Main dashboard logic
    if run_btn:
        if not youtube_api_key:
            st.error("🔑 错误：缺少 YouTube Data API Key，请在侧边栏中配置。")
            return
            
        if sentiment_engine == "官方 Google Gemini API" and not gemini_api_key:
            st.error("🔑 错误：已启用 Gemini 情感分析引擎，但未提供 Gemini API Key。")
            return

        if sentiment_engine == "自定义 OpenAI 兼容 API (如 DeepSeek, OpenAI等)" and not custom_api_key:
            st.error("🔑 错误：已启用自定义 API 引擎，但未提供 API Key。")
            return

        try:
            # 1. Fetching YouTube Comments
            with st.spinner("📦 正在建立翻页流，获取十万级 YouTube 顶层数据中..."):
                raw_df, quota_exceeded = fetch_youtube_data(
                    api_key=youtube_api_key,
                    keyword_text=keyword_text,
                    max_items=int(max_items),
                )

            if quota_exceeded:
                st.warning("🚨 [配额熔断触发] Google API 额度已耗尽！已自动停止网络请求，系统触发优雅退出，自动为您呈现当前已捕获的舆情数据分析。")

            if raw_df.empty:
                st.error("❌ 未抓取到有效评论。请确认关键词是否有拼写错误、视频是否存在、或 API 配额是否充足。")
                return

            # 2. Cleanup
            with st.spinner("🧹 数据时序标准化与清洗处理中..."):
                df = preprocess_dataframe(raw_df)

            # 3. Sentiment tagging
            with st.spinner("🧠 语义情绪特征打标与数据归集..."):
                if sentiment_engine == "官方 Google Gemini API":
                    df = run_sentiment_gemini_wrapper(df, gemini_api_key, gemini_model)
                else:
                    df = run_sentiment_custom_wrapper(df, custom_api_key, custom_base_url, custom_model_name)

            if df.empty:
                st.error("❌ 清洗后数据集为空，无法生成可视化图表。")
                return

            # Store results in streamlit session state for cross-tab persistence
            st.session_state["opinion_df"] = df
            st.session_state["sentiment_engine"] = sentiment_engine
            st.session_state["gemini_key"] = gemini_api_key
            st.session_state["gemini_model"] = gemini_model
            st.session_state["custom_key"] = custom_api_key
            st.session_state["custom_base_url"] = custom_base_url
            st.session_state["custom_model"] = custom_model_name
            st.session_state["scct_enabled"] = enable_scct
            st.success("🎉 数据集自动化治理与情绪计算流程圆满完成！已切换至交互式展板。")

        except Exception as e:
            st.error(f"💥 系统遭遇不可抗力故障: {e}")

    # Display panel tabs if data is available
    # Display panel tabs if data is available
    if "opinion_df" in st.session_state:
        df = st.session_state["opinion_df"]
        sentiment_engine = st.session_state.get("sentiment_engine", "官方 Google Gemini API")
        gemini_api_key = st.session_state.get("gemini_key", "")
        gemini_model = st.session_state.get("gemini_model", "gemini-1.5-flash")
        custom_api_key = st.session_state.get("custom_key", "")
        custom_base_url = st.session_state.get("custom_base_url", "https://api.deepseek.com")
        custom_model_name = st.session_state.get("custom_model", "deepseek-chat")
        enable_scct = st.session_state["scct_enabled"]

        # Render Academic Metric Cards
        render_metrics(df)
        st.divider()

        # Six Tabs Layout (Academic Redesign)
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 舆情定量分析大屏 (Quantitative Metrics)", 
            "🧪 实证科研高级探针 (Empirical Analytics)",
            "🔮 学术语义聚类分析 (Semantic Clustering)",
            "📚 SCCT 学术编码研究 (Theoretical Coding)", 
            "🔍 词云与情感语义分布 (Semantic Mining)", 
            "💾 研究数据审计与导出 (Corpus Auditor)"
        ])

        with tab1:
            render_dashboard(df)

        with tab2:
            # 竞品/多关键词对比
            plot_competitive_keywords(df)
            st.divider()
            
            # 时序与热力图并排
            c1, c2 = st.columns(2)
            with c1:
                plot_temporal_heatmap(df)
            with c2:
                plot_rolling_sentiment(df)
            st.divider()
            
            # 相关性探针单独行展现
            plot_engagement_correlation(df)

        with tab3:
            plot_semantic_clustering(df)

        with tab4:
            st.markdown('<div class="section-title">📚 SCCT 危机情境定量内容分析中枢 (基于经典情境危机传播理论)</div>', unsafe_allow_html=True)
            
            # 过滤出所有消极评论
            neg_comments = df[df["sentiment"].isin(["愤怒", "悲伤", "恐惧", "厌恶", "negative"])].sort_values(by="like_count", ascending=False)["comment_text"].tolist()
            
            if not enable_scct:
                st.info("💡 学术研究模型未启用。请在侧边栏勾选“开启 SCCT 学术编码模型”激活。")
            else:
                if sentiment_engine == "官方 Google Gemini API":
                    if not gemini_api_key:
                        st.warning("🔑 提示：需要配置 Gemini API Key 以加载高级 SCCT 危机实证编码分析模块。")
                        
                        # 学术性科普栏目，在无 Key 时展示，彰显学术理论性
                        st.markdown(
                            """
                            > **经典 SCCT 情境危机传播理论（Timothy Coombs 教授）**
                            > SCCT 是传播学领域在危机沟通和品牌声誉管理方面的**核心权威理论框架**。该理论主张：企业组织遭遇声誉危机时，所面临的公共关系威胁直接取决于**公众对危机事件归因责任的严重度**。
                            > 
                            > 理论将情境划分为三大危机集群：
                            > 1. **受害者集群 (Victim Cluster)**：组织被视为外部被侵害方。归因责任：极低。*（推荐策略：否认/澄清 Denial）*
                            > 2. **事故集群 (Accidental Cluster)**：组织非恶意，因偶然操作/技术故障诱发。归因责任：中等。*（推荐策略：淡化客观因素 Diminish）*
                            > 3. **可防范集群 (Preventable Cluster)**：组织故意违法违规或管理严重失职。归因责任：极高。*（推荐策略：重塑道歉/纠正整改 Rebuild）*
                            > 
                            > **如何解锁该学术实证模块？**
                            > 在左侧参数面板中配置 `Gemini API Key` 并点击启动工作流。计算智能将自动过滤负向抱怨文本的语义群，匹配 SCCT 理论坐标轴归因，生成符合论文发表水准的**实证编码报告与 APA 7th 标准学术参考文献列表**。
                            """
                        )
                    else:
                        with st.spinner("🕵️‍♂️ 传播学专家系统研判个案文本，生成 SCCT 学术实证编码报告中..."):
                            report = generate_scct_insights(neg_comments, gemini_api_key, gemini_model)
                        
                        st.markdown(report)
                        
                        # 报告导出能力
                        st.download_button(
                            label="📥 导出 SCCT 学术内容分析编码报告 (Markdown)",
                            data=report.encode("utf-8"),
                            file_name=f"SCCT_Academic_Coding_Report_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                else:
                    if not custom_api_key:
                        st.warning("🔑 提示：需要配置自定义 API Key 以加载高级 SCCT 危机实证编码分析模块。")
                    else:
                        with st.spinner("🕵️‍♂️ 传播学专家系统研判个案文本，生成 SCCT 学术实证编码报告中..."):
                            report = generate_scct_insights_custom_api(neg_comments, custom_api_key, custom_base_url, custom_model_name)
                        
                        st.markdown(report)
                        
                        # 报告导出能力
                        st.download_button(
                            label="📥 导出 SCCT 学术内容分析编码报告 (Markdown)",
                            data=report.encode("utf-8"),
                            file_name=f"SCCT_Academic_Coding_Report_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )

        with tab5:
            render_extreme_quotes(df)
            st.divider()
            
            st.markdown('<div class="section-title">☁️ 语义核心词频云图</div>', unsafe_allow_html=True)
            try:
                img = build_wordcloud_image(df)
                if img is None:
                    st.info("评论内容为空，暂无法生成词云。")
                else:
                    st.image(img, use_container_width=True)
            except Exception as err:
                st.warning(f"词云生成失败: {{err}}")

        with tab5:
            st.markdown('<div class="section-title">💾 原始语料数据审计表</div>', unsafe_allow_html=True)
            
            # 添加关键词筛选
            search_query = st.text_input("🔍 输入关键词过滤审计数据...", "")
            filtered_df = df
            if search_query:
                filtered_df = df[df["comment_text"].str.contains(search_query, case=False, na=False)]
                
            st.dataframe(filtered_df, use_container_width=True)

            csv_bytes = filtered_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 导出过滤后的学术语料 corpus 为 CSV",
                data=csv_bytes,
                file_name=f"youtube_corpus_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.csv",
                mime="text/csv",
            )
    else:
        # Initial Landing view showing system details with Academic framing
        st.info("💡 请在侧边栏配置学术科研控制台，点击“启动数据工作流”开始自动进行语料采样与分析。")
        
        # Introduce features
        st.markdown('<div class="section-title">🔬 系统科学架构与计算传播学核心亮点</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                <div class="metric-card" style="min-height: 200px;">
                    <div class="metric-title" style="color: #a78bfa;">📥 自动采样多语种语料库</div>
                    <div style="font-size: 14px; color: #cbd5e1; margin-top: 10px; line-height: 1.6;">
                        基于 YouTube Data API v3 大大规模自动分页翻页算法，实现多检索项去重的顶层评论循环抓取，遇到评论关闭视频智能绕行，构建科学可信的公开媒介文本语料库。
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                """
                <div class="metric-card" style="min-height: 200px;">
                    <div class="metric-title" style="color: #34d399;">🧠 混合计算语言学分类算法</div>
                    <div style="font-size: 14px; color: #cbd5e1; margin-top: 10px; line-height: 1.6;">
                        整合高效的纯 Python 本地规则兜底算法与先进的大语言模型情感判定引擎，在大模型 API 调用受限或超额时提供秒级弹性退化兜底，保障计算实验流程零中断。
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                """
                <div class="metric-card" style="min-height: 200px;">
                    <div class="metric-title" style="color: #f87171;">📚 SCCT 经典传播模型实证</div>
                    <div style="font-size: 14px; color: #cbd5e1; margin-top: 10px; line-height: 1.6;">
                        融合经典危机公关 SCCT 归因模型。过滤负向抗议文本进行学术内容编码，动态研判责任归属集群，导出 APA 格式论文文献引用与个案实证报告。
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def run_sentiment_gemini_wrapper(df: pd.DataFrame, gemini_api_key: str, gemini_model: str = "gemini-1.5-flash") -> pd.DataFrame:
    """批量使用 Gemini 引擎的逻辑包装"""
    out = df.copy()
    results = batch_analyze_sentiment_with_gemini(out["comment_text"].tolist(), gemini_api_key, gemini_model)
    sentiment_labels = [r[0] for r in results]
    sentiment_scores = [r[1] for r in results]
    sentiment_models = [r[2] for r in results]
    
    out["sentiment"] = sentiment_labels
    out["sentiment_score"] = sentiment_scores
    out["sentiment_model"] = sentiment_models
    return out


def run_sentiment_custom_wrapper(df: pd.DataFrame, api_key: str, base_url: str, model_name: str) -> pd.DataFrame:
    """批量使用自定义 OpenAI 兼容 API 引擎的逻辑包装"""
    out = df.copy()
    results = batch_analyze_sentiment_with_custom_api(out["comment_text"].tolist(), api_key, base_url, model_name)
    sentiment_labels = [r[0] for r in results]
    sentiment_scores = [r[1] for r in results]
    sentiment_models = [r[2] for r in results]
    
    out["sentiment"] = sentiment_labels
    out["sentiment_score"] = sentiment_scores
    out["sentiment_model"] = sentiment_models
    return out


if __name__ == "__main__":
    main()