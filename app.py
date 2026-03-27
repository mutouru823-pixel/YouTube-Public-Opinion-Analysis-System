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


st.set_page_config(
    page_title="YouTube 舆情自动化分析与可视化系统",
    page_icon="📊",
    layout="wide",
)


def contains_chinese(text: str) -> bool:
    """判断文本是否包含中文字符。"""
    if not text:
        return False
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def classify_sentiment_with_ext_api(text: str) -> Optional[Dict]:
    """
    预留接口：后续可在此接入 DeepSeek API 或其他模型服务，返回多维情绪结果。

    预期返回示例：
    {
        "label": "positive|neutral|negative|anger|disgust|...",
        "score": 0.87,
        "raw": {...}
    }
    """
    # TODO: 接入 DeepSeek API
    return None


def analyze_sentiment(text: str) -> Tuple[str, float, str]:
    """
    对单条评论做基础情绪分析。
    返回: (sentiment_label, sentiment_score, model_used)
    sentiment_label ∈ {positive, neutral, negative}
    """
    if not text or not text.strip():
        return "neutral", 0.5, "none"

    # 先尝试外部模型接口（若未来接入）
    ext_result = classify_sentiment_with_ext_api(text)
    if ext_result and "label" in ext_result:
        label = ext_result.get("label", "neutral")
        score = float(ext_result.get("score", 0.5))
        if label not in {"positive", "neutral", "negative"}:
            # 对多维情绪先做一个映射，后续可按业务细化
            mapping = {
                "joy": "positive",
                "anger": "negative",
                "disgust": "negative",
                "fear": "negative",
                "sadness": "negative",
            }
            label = mapping.get(label, "neutral")
        return label, score, "external"

    try:
        if contains_chinese(text):
            from snownlp import SnowNLP

            score = SnowNLP(text).sentiments  # 0~1
            if score >= 0.6:
                return "positive", float(score), "SnowNLP"
            if score <= 0.4:
                return "negative", float(score), "SnowNLP"
            return "neutral", float(score), "SnowNLP"

        # 英文默认用 VADER
        import nltk
        from nltk.sentiment.vader import SentimentIntensityAnalyzer

        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)

        analyzer = SentimentIntensityAnalyzer()
        score_map = analyzer.polarity_scores(text)
        compound = score_map["compound"]  # -1~1

        if compound >= 0.05:
            return "positive", float((compound + 1) / 2), "VADER"
        if compound <= -0.05:
            return "negative", float((compound + 1) / 2), "VADER"
        return "neutral", 0.5, "VADER"

    except Exception:
        # 兜底，避免单条评论分析失败中断全流程
        return "neutral", 0.5, "fallback"


def parse_keywords(keyword_text: str) -> List[str]:
    """解析多关键词输入，支持中英文逗号和空格分隔。"""
    if not keyword_text or not keyword_text.strip():
        return []

    # 支持: "华为 小米 AI", "Apple, Tesla", "华为，苹果, OpenAI"
    tokens = re.split(r"[\s,，]+", keyword_text.strip())
    return [k.strip() for k in tokens if k.strip()]


def _extract_http_error_info(err: HttpError) -> Tuple[Optional[int], str, str]:
    """
    提取 HttpError 中的核心信息，尽量标准化为:
    - status_code: HTTP 状态码
    - reason: 错误原因（如 quotaExceeded / commentsDisabled）
    - message: 服务端错误描述
    """
    status_code = getattr(getattr(err, "resp", None), "status", None)
    reason = ""
    message = ""

    try:
        # err.content 常见类型是 bytes
        payload = err.content.decode("utf-8") if isinstance(err.content, bytes) else str(err.content)
        body = json.loads(payload)
        err_obj = body.get("error", {}) if isinstance(body, dict) else {}

        if isinstance(err_obj.get("errors"), list) and err_obj["errors"]:
            reason = str(err_obj["errors"][0].get("reason", ""))

        message = str(err_obj.get("message", ""))
    except Exception:
        # 解不出结构化数据时，后续将退化到 str(err) 进行判断
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
    return "keyinvalid" in text or "api key not valid" in text or "forbidden" in text and "key" in text


def fetch_youtube_data(api_key: str, keyword_text: str, max_items: int) -> Tuple[pd.DataFrame, bool]:
    """
    根据多关键词抓取 YouTube 相关视频的顶层评论。

    关键能力:
    1) 外层循环遍历多个关键词。
    2) 评论抓取使用 while + nextPageToken 连续翻页，突破单次 100 条限制。
    3) commentsDisabled 自动跳过，不影响整体流程。
    4) quotaExceeded 优雅中断，返回中断前已抓到的数据。

    返回字段:
    - video_id
    - video_title
    - keyword
    - comment_id
    - comment_text
    - published_at
    - like_count
    - author

    返回:
    - DataFrame: 抓取结果（可能是部分结果）
    - quota_exceeded: 是否触发了配额耗尽
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

    # 记录已处理视频，避免跨关键词重复抓取造成额度浪费。
    seen_video_ids = set()

    # 统一的空结构，保证前端在无数据时也能稳定渲染。
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
        # 外层循环：逐个关键词抓取，直到达到目标条数或配额耗尽。
        for keyword in keywords:
            if len(all_rows) >= max_items or quota_exceeded:
                break

            search_token = None

            # 视频搜索同样是分页接口，使用 nextPageToken 持续翻页。
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
                        raise RuntimeError("API Key 无效，请检查输入是否正确。") from err
                    raise RuntimeError(f"搜索视频失败: {err}") from err

                video_items = search_response.get("items", [])
                if not video_items:
                    break

                # 本页视频逐条处理评论。
                for video_item in video_items:
                    if len(all_rows) >= max_items or quota_exceeded:
                        break

                    vid = video_item.get("id", {}).get("videoId")
                    if not vid or vid in seen_video_ids:
                        continue

                    seen_video_ids.add(vid)
                    video_title = video_item.get("snippet", {}).get("title", "")

                    comments_token = None

                    # 评论分页循环：每次最多 100 条，持续翻页直到达到目标或评论耗尽。
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
                                # 最关键容错：评论区关闭时仅跳过该视频，绝不让系统崩溃。
                                skip_msg = f"[跳过] 视频 {vid} 已关闭评论区"
                                print(skip_msg)
                                st.warning(skip_msg)
                                break

                            if _is_quota_exceeded(err):
                                quota_exceeded = True
                                break

                            if _is_invalid_api_key(err):
                                raise RuntimeError("API Key 无效，请检查输入是否正确。") from err

                            # 其他视频级错误：记录后跳过该视频，避免全局任务失败。
                            st.warning(f"[跳过] 视频 {vid} 抓取失败: {err}")
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
            raise RuntimeError("API Key 无效，请检查输入是否正确。") from err
        else:
            raise RuntimeError(f"YouTube API 请求失败: {err}") from err
    except Exception as err:
        raise RuntimeError(f"数据抓取发生异常: {err}") from err

    if not all_rows:
        return empty_df, quota_exceeded

    return pd.DataFrame(all_rows), quota_exceeded


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """基础清洗和时间字段处理。"""
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


def run_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """批量情绪分析。"""
    if df.empty:
        return df

    out = df.copy()
    sentiment_labels = []
    sentiment_scores = []
    sentiment_models = []

    for text in out["comment_text"].tolist():
        label, score, model = analyze_sentiment(text)
        sentiment_labels.append(label)
        sentiment_scores.append(score)
        sentiment_models.append(model)

    out["sentiment"] = sentiment_labels
    out["sentiment_score"] = sentiment_scores
    out["sentiment_model"] = sentiment_models

    return out


def build_wordcloud_image(df: pd.DataFrame):
    """构建词云图片对象（PIL Image）。"""
    text_blob = " ".join(df["comment_text"].dropna().astype(str).tolist()).strip()
    if not text_blob:
        return None

    # 若含中文，尝试用 jieba 做分词。
    if contains_chinese(text_blob):
        try:
            import jieba

            text_blob = " ".join(jieba.cut(text_blob))
        except Exception:
            pass

    # Linux 常见字体路径，尽量避免中文词云乱码。
    font_candidates = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    font_path = next((f for f in font_candidates if os.path.exists(f)), None)

    wc = WordCloud(
        width=1200,
        height=500,
        background_color="white",
        max_words=200,
        collocations=False,
        font_path=font_path,
    ).generate(text_blob)
    return wc.to_image()


def plot_charts(df: pd.DataFrame):
    """绘制并展示图表。"""
    if df.empty:
        st.info("暂无可展示的数据，请先抓取评论。")
        return

    # 时间趋势（日）
    trend_daily = df.groupby("date", as_index=False).size().rename(columns={"size": "comment_count"})
    fig_line = px.line(
        trend_daily,
        x="date",
        y="comment_count",
        title="舆情时间趋势（日）",
        markers=True,
    )
    fig_line.update_layout(xaxis_title="日期", yaxis_title="评论数量", hovermode="x unified")

    # 情绪分布
    sentiment_dist = (
        df.groupby("sentiment", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )

    fig_pie = px.pie(
        sentiment_dist,
        names="sentiment",
        values="count",
        hole=0.45,
        title="整体情绪分布占比",
        color="sentiment",
        color_discrete_map={
            "positive": "#2ca02c",
            "neutral": "#9e9e9e",
            "negative": "#d62728",
        },
    )

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_line, use_container_width=True)
    with col2:
        st.plotly_chart(fig_pie, use_container_width=True)

    # 词云
    st.subheader("词云图（高频关键词）")
    try:
        img = build_wordcloud_image(df)
        if img is None:
            st.info("评论内容为空，暂无法生成词云。")
        else:
            st.image(img, use_container_width=True)
    except Exception as err:
        st.warning(f"词云生成失败: {err}")


def render_metrics(df: pd.DataFrame):
    """渲染顶部指标卡。"""
    total = len(df)
    if total == 0:
        pos_ratio = 0.0
        neg_ratio = 0.0
    else:
        pos_ratio = (df["sentiment"] == "positive").mean() * 100
        neg_ratio = (df["sentiment"] == "negative").mean() * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("总抓取评论数", f"{total}")
    c2.metric("正向情绪占比", f"{pos_ratio:.2f}%")
    c3.metric("负向情绪占比", f"{neg_ratio:.2f}%")


def main():
    st.title("YouTube 舆情自动化分析与可视化系统")
    st.caption("支持关键词抓取、情绪分析、趋势可视化与数据导出")

    with st.sidebar:
        st.header("参数配置")
        api_key = st.text_input("YouTube Data API v3 Key", type="password")
        keyword_text = st.text_input(
            "目标关键词（支持多关键词）",
            placeholder="例如：新能源汽车, 智能驾驶 AI（逗号或空格分隔）",
            help="可输入多个关键词，系统会逐个关键词搜索并汇总评论。",
        )
        max_items = st.number_input(
            "目标评论抓取总量",
            min_value=10,
            max_value=100000,
            value=1000,
            step=100,
            help="上限 100,000。系统会分页抓取评论，直到达到该数量或无更多评论。",
        )
        run_btn = st.button("开始抓取与分析", type="primary", use_container_width=True)

    if run_btn:
        try:
            with st.spinner("正在抓取 YouTube 评论数据，请稍候..."):
                raw_df, quota_exceeded = fetch_youtube_data(
                    api_key=api_key,
                    keyword_text=keyword_text,
                    max_items=int(max_items),
                )

            # 配额耗尽时必须优雅中断，并明确告知用户；但仍继续处理已抓取的数据。
            if quota_exceeded:
                st.error("🚨 Google API 额度已消耗殆尽！")

            if raw_df.empty:
                st.warning("未抓取到评论数据，请尝试更换关键词或提高抓取数量。")
                return

            with st.spinner("正在进行数据处理与情绪分析..."):
                df = preprocess_dataframe(raw_df)
                df = run_sentiment(df)

            if df.empty:
                st.warning("抓取成功，但时间字段解析后无有效记录。")
                return

            render_metrics(df)
            st.divider()
            plot_charts(df)
            st.divider()

            st.subheader("原始数据表")
            st.dataframe(df, use_container_width=True)

            csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="下载为 CSV",
                data=csv_bytes,
                file_name=f"youtube_opinion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

        except ValueError as err:
            st.error(str(err))
        except RuntimeError as err:
            st.error(str(err))
        except Exception as err:
            st.error(f"系统发生未预期错误: {err}")

    else:
        st.info("请在左侧输入参数后点击“开始抓取与分析”。")


if __name__ == "__main__":
    main()
