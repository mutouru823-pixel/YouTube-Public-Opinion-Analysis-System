"""YouTube Data API v3 抓取管道模块。

封装多关键词检索、翻页抓取、评论区关闭跳过、配额熔断等高容错逻辑。
所有函数与原 app.py 行为等价,仅做模块化拆分。
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def parse_keywords(keyword_text: str) -> List[str]:
    """解析多关键词输入,支持中英文逗号和空格分隔。"""
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


def fetch_youtube_data(api_key: str, keyword_text: str, max_items: int) -> Tuple[pd.DataFrame, bool]:
    """根据多关键词抓取 YouTube 相关视频的顶层评论。

    支持自动跳过关闭评论区的视频、配额耗尽时优雅熔断并持久化已抓取语料。

    Returns:
        (DataFrame, quota_exceeded) 二元组。DataFrame 含 video_id/video_title/
        keyword/comment_id/comment_text/published_at/like_count/author 字段。
    """
    if not api_key:
        raise ValueError("请先输入 YouTube API Key。")

    keywords = parse_keywords(keyword_text)
    if not keywords:
        raise ValueError("请输入至少一个关键词,并用逗号或空格分隔。")

    try:
        youtube = build("youtube", "v3", developerKey=api_key)
    except Exception as exc:
        raise RuntimeError("YouTube API 客户端初始化失败,请检查 API Key。") from exc

    all_rows: List[Dict] = []
    quota_exceeded = False
    seen_video_ids = set()

    empty_df = pd.DataFrame(columns=[
        "video_id", "video_title", "keyword", "comment_id",
        "comment_text", "published_at", "like_count", "author",
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
                        raise RuntimeError("YouTube API Key 无效,请检查输入。") from err
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
                                raise RuntimeError("YouTube API Key 无效,请检查。") from err
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
                            all_rows.append({
                                "video_id": vid,
                                "video_title": video_title,
                                "keyword": keyword,
                                "comment_id": item.get("id", ""),
                                "comment_text": snippet.get("textDisplay", ""),
                                "published_at": snippet.get("publishedAt", ""),
                                "like_count": snippet.get("likeCount", 0),
                                "author": snippet.get("authorDisplayName", ""),
                            })
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
