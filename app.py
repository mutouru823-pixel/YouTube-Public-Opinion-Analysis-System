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


# 🚀 Performance Engineering: Global Cache for NLTK VADER Analyzer
@st.cache_resource
def get_vader_analyzer():
    """
    单例模式缓存 VADER 分析器加载。
    避免每条评论循环中重复实例化、下载和字典解析的巨大性能开销。
    """
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon", quiet=True)

    return SentimentIntensityAnalyzer()


def analyze_sentiment_local(text: str) -> Tuple[str, float, str]:
    """
    本地轻量级 NLP 双语情感分析（SnowNLP + VADER）。
    返回: (sentiment_label, sentiment_score, model_used)
    """
    if not text or not text.strip():
        return "neutral", 0.5, "none"

    try:
        if contains_chinese(text):
            from snownlp import SnowNLP

            score = SnowNLP(text).sentiments  # 0~1
            if score >= 0.6:
                return "positive", float(score), "SnowNLP"
            if score <= 0.4:
                return "negative", float(score), "SnowNLP"
            return "neutral", float(score), "SnowNLP"

        # 英文情绪分析（使用全局缓存的 VADER）
        analyzer = get_vader_analyzer()
        score_map = analyzer.polarity_scores(text)
        compound = score_map["compound"]  # -1~1

        # 归一化到 0~1 区间以对齐 SnowNLP
        normalized_score = float((compound + 1) / 2)

        if compound >= 0.05:
            return "positive", normalized_score, "VADER"
        if compound <= -0.05:
            return "negative", normalized_score, "VADER"
        return "neutral", 0.5, "VADER"

    except Exception:
        # 极端异常兜底，防止分析单条数据崩溃
        return "neutral", 0.5, "fallback"


def batch_analyze_sentiment_with_gemini(comments: List[str], api_key: str) -> List[Tuple[str, float, str]]:
    """
    【AI双引擎高级功能】批量使用 Gemini 1.5 Flash 对评论进行情感打标，有效减少 HTTP 请求，保证效率与额度。
    """
    results = []
    batch_size = 20  # 每次并行分析 20 条，减少 API 握手次数
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"Gemini 客户端初始化失败，自动退化为本地 NLP 模型: {e}")
        return [analyze_sentiment_local(c) for c in comments]

    for i in range(0, len(comments), batch_size):
        batch = comments[i : i + batch_size]
        
        # 结构化输入，限制长度避免大段评论溢出
        inputs = []
        for idx, text in enumerate(batch):
            inputs.append({"id": idx, "text": text[:200]})

        prompt = f"""
你是一名专业的高级社交媒体数据分析师。请对以下评论列表进行细粒度的情绪分类。
你必须对每条评论进行情绪标签（positive, neutral, negative 之一）分类，并给出一个在 0.0 到 1.0 之间的小数作为得分（0.0代表极度消极/愤怒，0.5代表中立，1.0代表极度积极/支持）。

待分类评论列表:
```json
{json.dumps(inputs, ensure_ascii=False)}
```

请严格返回符合以下 JSON 格式的数组，不要包含任何额外的 markdown 格式或多余的文字，只需返回纯 JSON：
[
  {{"id": 0, "sentiment": "positive", "score": 0.85}},
  ...
]
"""
        try:
            response = model.generate_content(prompt)
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
                label = item.get("sentiment", "neutral")
                score = float(item.get("score", 0.5))
                results.append((label, score, "Gemini LLM"))
                
        except Exception as e:
            # 容错降级：本批次分析失败时自动滑向 VADER/SnowNLP
            for text in batch:
                label, score, model_used = analyze_sentiment_local(text)
                results.append((label, score, f"{model_used}(降级)"))
                
    return results


def generate_scct_insights(negative_comments: List[str], api_key: str) -> str:
    """
    【商业危机管理模块】基于 Coombs 的 SCCT（情境危机传播理论）提供系统公关策略。
    """
    if not api_key:
        return "⚠️ 请在左侧参数配置面板输入 Gemini API Key 以激活 SCCT 公关战略模块。"
        
    if not negative_comments:
        return "💡 暂未检测到明显的负面言论，品牌声誉安全，无需触发 SCCT 危机预案。"

    # 取高权重（如被点赞多）的负面言论样本，限制 token
    sample_comments = negative_comments[:40]
    comments_text = "\n".join([f"- {c}" for c in sample_comments])

    prompt = f"""
你是一名资深跨国企业危机公关专家和品牌声誉管理顾问。请根据 Coombs 的 **情境危机传播理论 (Situational Crisis Communication Theory, SCCT)**，对以下 YouTube 视频中的用户负面抗议意见进行深度分析。

负面评论样本：
\"\"\"
{comments_text}
\"\"\"

请生成一份专业、高度结构化、可直接呈报给企业高层决策的【AI 危机舆情与 SCCT 公关战略报告】。报告应包含以下核心板块，并以精美专业的 Markdown 格式输出：

### 🎯 1. 危机定性与核心诉求分析 (Crisis Diagnosis)
- **公众舆论核心痛点**：总结用户最强烈的不满、质疑和诉求（列出 Top 3 痛点并详细剖析）。
- **舆情风险等级评定**：定性评估公众情绪（如：失望、愤怒、抵制、讽刺等），并评估危机对品牌声誉的短期与长期危害。

### 🧠 2. SCCT 危机情境归类 (SCCT Crisis Clustering)
根据 SCCT 理论，判断该事件属于以下哪类危机集群（进行详细论证并给出归类理由）：
- **受害者集群 (Victim Cluster)**：企业被视为受害者（如自然灾害、谣言、外部蓄意破坏）。归因责任：极低。
- **事故集群 (Accidental Cluster)**：企业非蓄意但因技术、操作故障引发（如意外设备故障、非恶意产品缺陷）。归因责任：中等。
- **可防范集群 (Preventable Cluster)**：企业故意违法或管理严重失职、隐瞒事实导致（如故意安全违规、知情不报、欺诈行为）。归因责任：极高。

### 📈 3. 推荐公关响应策略 (Recommended PR Strategy Scorecard)
根据危机归类，推荐企业采取何种响应策略（提供百分比推荐，并说明具体公关话术切入点）：
- **否认策略 (Denial)**：划清界限、驳斥谣言或强调企业无辜。（适用受害者集群）
- **淡化策略 (Diminish)**：强调外部客观因素，重申损害可控，降低公众对危机严重性的感知。（适用事故集群）
- **重塑策略 (Rebuild)**：诚恳道歉，承担全部责任，并提供实质性补偿（Compensation）与纠正措施（Corrective Action）。（适用可防范/严重事故集群）
- **迎合/强化策略 (Bolstering)**：提醒公众企业过去的良好记录，对支持者表示感谢，重建信任。

### 📝 4. 危机响应双语官方声明草案 (Bilingual Press Release Draft)
提供一份符合企业级危机公关规范的**官方声明/道歉信草案**：
- **中文版本 (Chinese Version)**
- **英文版本 (English Version)**
- **声明写作要点解析**：解释为什么这样设计措辞（如：首要关注受害者、展现主动担当、具体的后续整改承诺）。
"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ AI 危机公关报告生成失败，错误信息: {str(e)}"


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
                "positive": "#10b981", # Emerald
                "neutral": "#64748b",  # Slate
                "negative": "#ef4444", # Red
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
            st.markdown("📊 **舆情态势研判：震荡僵持。** 滑动情感得分平稳，代表网民态度对立中和，舆论热点正处于稳步消耗阶段。")


# ==========================================
# 📋 CORE RENDER LOGIC
# ==========================================

def render_extreme_quotes(df: pd.DataFrame):
    """深度透视页面中，提取用户高权重（Like高）评论"""
    st.markdown('<div class="section-title">🔍 核心舆论风向标：高赞观点追踪</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    # 提取高赞的正面评论
    pos_df = df[df["sentiment"] == "positive"].sort_values(by="like_count", ascending=False).head(5)
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
                        <div class="quote-meta">来自视频：{row['video_title'][:40]}... | 情绪评分: {row['sentiment_score']:.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
    # 提取高赞的负面评论
    neg_df = df[df["sentiment"] == "negative"].sort_values(by="like_count", ascending=False).head(5)
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
                        <div class="quote-meta">来自视频：{row['video_title'][:40]}... | 情绪评分: {row['sentiment_score']:.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_metrics(df: pd.DataFrame):
    """渲染顶部指标卡。"""
    total = len(df)
    if total == 0:
        pos_ratio = 0.0
        neg_ratio = 0.0
        neu_ratio = 0.0
    else:
        pos_ratio = (df["sentiment"] == "positive").mean() * 100
        neg_ratio = (df["sentiment"] == "negative").mean() * 100
        neu_ratio = (df["sentiment"] == "neutral").mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">📊 总抓取舆情数</div>
                <div class="metric-value">{total:,}</div>
                <div class="metric-subtitle">来自顶层评论翻页抓取</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🟢 正向情绪占比</div>
                <div class="metric-value" style="background: linear-gradient(135deg, #34d399 0%, #059669 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{pos_ratio:.1f}%</div>
                <div class="metric-subtitle">正面反馈与支持声音</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🟡 中立情绪占比</div>
                <div class="metric-value" style="background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{neu_ratio:.1f}%</div>
                <div class="metric-subtitle">客观描述与常规内容</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🔴 负向情绪占比</div>
                <div class="metric-value" style="background: linear-gradient(135deg, #f87171 0%, #dc2626 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{neg_ratio:.1f}%</div>
                <div class="metric-subtitle">危机预警与主要客诉</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    # Modern Gradient Banner
    st.markdown(
        """
        <div class="header-panel">
            <h1>📊 YouTube 舆情智能化分析与 SCCT 决策系统</h1>
            <p>融合大规模自动分页抓取、双引擎情感打标与 SCCT 公关危机理论的微型商业 SaaS 智能面板</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar parameters
    with st.sidebar:
        st.header("⚙️ 系统控制中心")
        
        # API Keys configuration
        youtube_api_key = st.text_input("YouTube Data API Key", type="password", help="需开通 YouTube Data API v3 权限。")
        
        keyword_text = st.text_input(
            "舆情核心关键词",
            placeholder="例如：新能源汽车, 智能驾驶 AI（逗号/空格分隔）",
            help="输入多个词时，系统将并行搜索汇总并自动去重。",
        )
        
        max_items = st.number_input(
            "数据采样上限 (页深度)",
            min_value=10,
            max_value=100000,
            value=500,
            step=100,
            help="支持至 100,000 条。大规模时使用 next_token 并页抓取。",
        )
        
        st.divider()
        
        # Engine selections
        sentiment_engine = st.selectbox(
            "🏷️ 情感判定算法引擎",
            ["本地 NLP 轻量引擎 (VADER & SnowNLP)", "云端大语言模型引擎 (Gemini LLM)"],
            help="若选择 Gemini 引擎，需在下方提供 Gemini API Key；其支持超强语境和反讽语义判定。"
        )
        
        gemini_api_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            placeholder="AI 危机公关与 LLM 分析所需",
            help="可选。用于解锁高级 AI 危机公关 SCCT 诊断功能和大模型情绪打标。"
        )
        
        enable_scct = st.checkbox("🌟 启用 AI 危机公关 (SCCT)", value=True, help="启用后，将使用 Gemini 自动根据危机公关理论为负面言论生成建议报告。")
        
        run_btn = st.button("🚀 启动数据工作流", type="primary", use_container_width=True)

    # Main dashboard logic
    if run_btn:
        if not youtube_api_key:
            st.error("🔑 错误：缺少 YouTube Data API Key，请在侧边栏中配置。")
            return
            
        if sentiment_engine == "云端大语言模型引擎 (Gemini LLM)" and not gemini_api_key:
            st.error("🔑 错误：已启用 Gemini 情感分析引擎，但未提供 Gemini API Key。")
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
                # 如果选了本地 NLP 引擎
                if sentiment_engine == "本地 NLP 轻量引擎 (VADER & SnowNLP)":
                    sentiment_labels = []
                    sentiment_scores = []
                    sentiment_models = []
                    for text in df["comment_text"].tolist():
                        label, score, model = analyze_sentiment_local(text)
                        sentiment_labels.append(label)
                        sentiment_scores.append(score)
                        sentiment_models.append(model)
                    df["sentiment"] = sentiment_labels
                    df["sentiment_score"] = sentiment_scores
                    df["sentiment_model"] = sentiment_models
                else:
                    # 选了 Gemini 引擎，进行高吞吐量 Batching 分析
                    df = run_sentiment_gemini_wrapper(df, gemini_api_key)

            if df.empty:
                st.error("❌ 清洗后数据集为空，无法生成可视化图表。")
                return

            # Store results in streamlit session state for cross-tab persistence
            st.session_state["opinion_df"] = df
            st.session_state["gemini_key"] = gemini_api_key
            st.session_state["scct_enabled"] = enable_scct
            st.success("🎉 数据集自动化治理与情绪计算流程圆满完成！已切换至交互式展板。")

        except Exception as e:
            st.error(f"💥 系统遭遇不可抗力故障: {e}")

    # Display panel tabs if data is available
    if "opinion_df" in st.session_state:
        df = st.session_state["opinion_df"]
        gemini_api_key = st.session_state["gemini_key"]
        enable_scct = st.session_state["scct_enabled"]

        # Render Premium Metric Cards
        render_metrics(df)
        st.divider()

        # Five Tabs Layout (Phase 2 Upgrade)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 实时舆情分析看板 (Dashboard)", 
            "📈 高级数据探针 (Advanced Analytics)",
            "🧠 AI 危机公关与 SCCT 决策 (SCCT Advisory)", 
            "🔍 情绪词云与深度透视 (Semantic Analytics)", 
            "💾 数据探索与归档 (Data Explorer)"
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
            st.markdown('<div class="section-title">🧠 AI 危机公关中心 (基于 Coombs 情境危机传播理论)</div>', unsafe_allow_html=True)
            
            # 过滤出所有消极评论
            neg_comments = df[df["sentiment"] == "negative"].sort_values(by="like_count", ascending=False)["comment_text"].tolist()
            
            if not enable_scct:
                st.info("💡 危机公关功能未启用。请在左侧侧边栏勾选“启用 AI 危机公关 (SCCT)”并配置 API Key 激活。")
            elif not gemini_api_key:
                st.warning("🔑 提示：需要配置 Gemini API Key 以加载高级 SCCT 危机决策模块。")
                
                # 教育性科普栏目，在无 Key 时展示，彰显学术理论性
                st.markdown(
                    """
                    > **什么是 SCCT 危机公关理论？**
                    > 由危机公关学术权威 Coombs 提出。理论认为：企业在遭遇负面危机时，应先评估其负有责任的程度（受害者集群、事故集群、可防范集群），并对应选择“否认、淡化、重塑、强化”公关策略。
                    > 
                    > **如何解锁该高级功能？**
                    > 在左侧参数面板中配置 `Gemini API Key` 并点击启动工作流。系统将自动抓取负面批评意见的语义模式，映射理论坐标轴，自动生成企业中英文双语道歉信/新闻稿。
                    """
                )
            else:
                with st.spinner("🕵️‍♂️ 危机公关专家正研判舆情态势，编纂 SCCT 决策应对方案..."):
                    report = generate_scct_insights(neg_comments, gemini_api_key)
                
                st.markdown(report)
                
                # 报告导出能力
                st.download_button(
                    label="📥 导出 SCCT 危机公关决策报告 (Markdown)",
                    data=report.encode("utf-8"),
                    file_name=f"SCCT_Crisis_Advisory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

        with tab4:
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
                st.warning(f"词云生成失败: {err}")

        with tab5:
            st.markdown('<div class="section-title">💾 原始数据审计表</div>', unsafe_allow_html=True)
            
            # 添加关键词筛选
            search_query = st.text_input("🔍 输入关键词过滤审计数据...", "")
            filtered_df = df
            if search_query:
                filtered_df = df[df["comment_text"].str.contains(search_query, case=False, na=False)]
                
            st.dataframe(filtered_df, use_container_width=True)

            csv_bytes = filtered_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 导出过滤后的舆情数据为 CSV",
                data=csv_bytes,
                file_name=f"youtube_opinion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
    else:
        # Initial Landing view showing system details
        st.info("💡 请在左侧控制中心输入参数配置，点击“启动数据工作流”开始自动抓取与分析。")
        
        # Introduce features
        st.markdown('<div class="section-title">⚙️ 系统架构与核心亮点</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                <div class="metric-card" style="min-height: 200px;">
                    <div class="metric-title" style="color: #a78bfa;">📦 弹性高并发数据流</div>
                    <div style="font-size: 14px; color: #cbd5e1; margin-top: 10px; line-height: 1.6;">
                        利用 YouTube Data API v3 分页翻页机制，实现突破单页限制的十万级评论循环抓取；支持遇到关闭评论视频时智能路由跳过，极高容错。
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                """
                <div class="metric-card" style="min-height: 200px;">
                    <div class="metric-title" style="color: #34d399;">🧠 智能双算法引擎</div>
                    <div style="font-size: 14px; color: #cbd5e1; margin-top: 10px; line-height: 1.6;">
                        基于 Singleton Caching 优化的高性能本地 VADER & SnowNLP 双语情感计算；可无缝切换至 Gemini 批量大语言模型分析引擎，获取极高语义精度。
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                """
                <div class="metric-card" style="min-height: 200px;">
                    <div class="metric-title" style="color: #f87171;">💼 SCCT 公关智囊中心</div>
                    <div style="font-size: 14px; color: #cbd5e1; margin-top: 10px; line-height: 1.6;">
                        将前沿 AI 技术与权威 Coombs 情境危机传播理论（SCCT）融合，自动评估品牌声誉受损度，规划应对矩阵并撰写官方双语声明。
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def run_sentiment_gemini_wrapper(df: pd.DataFrame, gemini_api_key: str) -> pd.DataFrame:
    """批量使用 Gemini 引擎的逻辑包装"""
    out = df.copy()
    results = batch_analyze_sentiment_with_gemini(out["comment_text"].tolist(), gemini_api_key)
    sentiment_labels = [r[0] for r in results]
    sentiment_scores = [r[1] for r in results]
    sentiment_models = [r[2] for r in results]
    
    out["sentiment"] = sentiment_labels
    out["sentiment_score"] = sentiment_scores
    out["sentiment_model"] = sentiment_models
    return out


if __name__ == "__main__":
    main()
