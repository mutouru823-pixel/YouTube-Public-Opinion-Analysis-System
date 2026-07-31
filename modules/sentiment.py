"""情感分析引擎模块。

提供四种可互换的情感打标引擎,统一返回 ``(label, score, model_used)`` 三元组:

1. ``classify_emotion_fallback_pure_python`` —— 纯 Python 规则兜底(零依赖)
2. ``batch_analyze_sentiment_with_local_nlp`` —— VADER(英) + SnowNLP(中) 本地双引擎
3. ``batch_analyze_sentiment_with_gemini`` —— Google Gemini 批量打标
4. ``batch_analyze_sentiment_with_custom_api`` —— OpenAI 兼容接口(DeepSeek 等)

VADER 分析器通过 ``@st.cache_resource`` 全局单例缓存,避免重复下载词典与实例化。
"""

from __future__ import annotations

import json
import re
from typing import List, Tuple

import pandas as pd
import streamlit as st


# ============================================================
# 统一的 LLM Prompt(消除 Gemini / Custom API 两处的重复)
# ============================================================
SENTIMENT_LABELS_DESC = """1. "喜悦" (高兴、赞赏、支持、幽默、热烈期盼等积极向上的态度)
2. "悲伤" (遗憾、伤心、失望、同情、无奈等消极倾向的态度)
3. "愤怒" (生气、谴责、怒骂、剧烈抗议等极其激烈的敌对态度)
4. "恐惧" (担忧、害怕、恐慌、顾虑、忧心忡忡等缺乏安全感的态度)
5. "厌恶" (反感、恶心、鄙视、嫌弃、唾弃、抵制等拒绝认同的态度)
6. "惊讶" (吃惊、意外、出乎意料、难以置信等被震惊的态度)
7. "中立" (平静、客观叙事、无明显情绪波动的客观事实陈述)"""


def _build_sentiment_prompt(inputs: list[dict]) -> str:
    """构造统一的七维情感分类 prompt(供 Gemini 与自定义 API 共用)。"""
    return f"""
你是一名专业的高级社交媒体与传播学数据分析师。请对以下评论列表进行精细的情感维度分类。
你必须对每条评论进行情绪维度分类,必须是以下七类之一(选择最贴切的一项作为情绪标签):
{SENTIMENT_LABELS_DESC}

另外,请给出一个在 0.0 到 1.0 之间的小数作为情绪极性得分(0.0代表极度消极,0.5代表中立,1.0代表极度积极)。

待分类评论列表:
```json
{json.dumps(inputs, ensure_ascii=False)}
```

请严格返回符合以下 JSON 格式的数组,不要包含任何额外的 markdown 格式或多余的文字,只需返回纯 JSON:
[
  {{"id": 0, "sentiment": "喜悦", "score": 0.85}},
  ...
]
"""


def _strip_code_fences(text: str) -> str:
    """清理 LLM 输出中可能包裹的 ```json ... ``` 代码块标签。"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _parse_llm_json_batch(res_text: str, batch_len: int) -> List[Tuple[str, float, str]] | None:
    """解析 LLM 返回的 JSON 数组为三元组列表,失败返回 None。"""
    try:
        # 兜底提取首个 JSON 数组
        match = re.search(r"\[\s*\{.*\}\s*\]", res_text, re.DOTALL)
        if match:
            res_text = match.group(0)
        items = json.loads(res_text)
        items_sorted = sorted(items, key=lambda x: x["id"])
        out: List[Tuple[str, float, str]] = []
        for item in items_sorted:
            label = item.get("sentiment", "中立")
            score = float(item.get("score", 0.5))
            out.append((label, score, ""))
        # 长度对齐保护
        while len(out) < batch_len:
            out.append(("中立", 0.5, ""))
        return out[:batch_len]
    except Exception:
        return None


# ============================================================
# 1. 纯 Python 规则兜底(零依赖)
# ============================================================
def classify_emotion_fallback_pure_python(text: str) -> Tuple[str, float, str]:
    """轻量级纯 Python 规则情感打标(无任何第三方库依赖,作为兜底)。"""
    if not text or not text.strip():
        return "中立", 0.5, "纯Python兜底"

    text_lower = text.lower()

    joy_indicators = ["good", "love", "like", "great", "awesome", "perfect", "nice", "best", "wonderful", "cool", "happy", "棒", "赞", "喜悦", "喜欢", "支持", "不错", "好评", "优秀", "牛逼", "厉害", "给力"]
    sadness_indicators = ["sad", "cry", "sorry", "pain", "unfortunate", "disappointed", "regret", "难过", "伤心", "悲伤", "遗憾", "可怜", "哭", "痛", "失望", "委屈"]
    anger_indicators = ["angry", "hate", "mad", "shit", "fuck", "damn", "annoyed", "垃圾", "恶心", "愤怒", "生气", "差评", "退货", "骂", "傻", "极其恶劣", "滚", "无耻", "混蛋"]
    fear_indicators = ["fear", "scared", "afraid", "worry", "panic", "terror", "anxious", "害怕", "担心", "恐惧", "恐慌", "吓人", "可怕", "焦虑", "担忧", "忧虑"]
    disgust_indicators = ["disgust", "nasty", "gross", "garbage", "sick", "recoil", "厌恶", "反感", "恶劣", "鄙视", "唾弃", "抵制", "下作"]
    surprise_indicators = ["?!", "!?", "！", "？", "oh", "wow", "surprise", "amazed", "shocked", "惊讶", "意外", "居然", "竟然", "吃惊", "天哪"]

    hits = {
        "喜悦": sum(1 for w in joy_indicators if w in text_lower),
        "悲伤": sum(1 for w in sadness_indicators if w in text_lower),
        "愤怒": sum(1 for w in anger_indicators if w in text_lower),
        "恐惧": sum(1 for w in fear_indicators if w in text_lower),
        "厌恶": sum(1 for w in disgust_indicators if w in text_lower),
        "惊讶": sum(1 for w in surprise_indicators if w in text_lower),
    }

    max_emotion = max(hits, key=hits.get)
    if hits[max_emotion] == 0:
        return "中立", 0.5, "纯Python兜底"

    if max_emotion == "喜悦":
        score = 0.8
    elif max_emotion == "惊讶":
        score = 0.65
    elif max_emotion in ("悲伤", "恐惧"):
        score = 0.3
    elif max_emotion in ("愤怒", "厌恶"):
        score = 0.15
    else:
        score = 0.5

    return max_emotion, score, "纯Python兜底"


# ============================================================
# 2. VADER(英) + SnowNLP(中) 本地双引擎
# ============================================================
def contains_chinese(text: str) -> bool:
    """判断文本是否包含中文字符。"""
    if not text:
        return False
    return bool(re.search(r"[\u4e00-\u9fff]", text))


@st.cache_resource(show_spinner=False)
def _get_vader_analyzer():
    """全局单例缓存 VADER 分析器(避免每条评论重复下载词典/实例化)。

    首次调用会下载 vader_lexicon,失败时返回 None,上层降级为纯 Python 兜底。
    """
    try:
        import nltk
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)
        return SentimentIntensityAnalyzer()
    except Exception as e:
        st.warning(f"⚠️ VADER 初始化失败,英文评论将降级为纯 Python 规则打标: {e}")
        return None


def _vader_to_label_score(compound: float) -> Tuple[str, float]:
    """将 VADER compound ∈ [-1, 1] 映射到 7 维标签与 [0, 1] 分数。"""
    # compound → [0, 1]
    score = (compound + 1) / 2
    if compound >= 0.5:
        return "喜悦", score
    if compound <= -0.75:
        return "愤怒", score
    if compound <= -0.45:
        return "厌恶", score
    if compound <= -0.2:
        return "悲伤", score
    if -0.2 < compound < 0.2:
        return "中立", score
    return "喜悦", score  # 0.2 ~ 0.5 弱正面也归喜悦


def _snownlp_to_label_score(s: float) -> Tuple[str, float]:
    """将 SnowNLP sentiments ∈ [0, 1] 映射到 7 维标签与 [0, 1] 分数。"""
    if s >= 0.7:
        return "喜悦", s
    if s >= 0.55:
        return "喜悦", s  # 弱正面
    if s > 0.45:
        return "中立", s
    if s > 0.3:
        return "悲伤", s
    if s > 0.15:
        return "厌恶", s
    return "愤怒", s


def batch_analyze_sentiment_with_local_nlp(comments: List[str]) -> List[Tuple[str, float, str]]:
    """本地双引擎批量打标:中文用 SnowNLP,英文用 VADER,失败降级纯 Python。

    零 API 成本、毫秒级完成,适合大规模语料的快速初步打标。
    """
    vader = _get_vader_analyzer()
    results: List[Tuple[str, float, str]] = []

    for text in comments:
        if not text or not text.strip():
            results.append(("中立", 0.5, "本地引擎"))
            continue

        try:
            if contains_chinese(text):
                from snownlp import SnowNLP
                s = SnowNLP(text).sentiments
                label, score = _snownlp_to_label_score(s)
                results.append((label, score, "本地引擎(SnowNLP)"))
            elif vader is not None:
                compound = vader.polarity_scores(text)["compound"]
                label, score = _vader_to_label_score(compound)
                results.append((label, score, "本地引擎(VADER)"))
            else:
                results.append(classify_emotion_fallback_pure_python(text))
        except Exception:
            results.append(classify_emotion_fallback_pure_python(text))

    return results


# ============================================================
# 3. Google Gemini 批量打标
# ============================================================
def batch_analyze_sentiment_with_gemini(
    comments: List[str], api_key: str, model_name: str = "gemini-1.5-flash"
) -> List[Tuple[str, float, str]]:
    """批量使用 Gemini 对评论进行情感打标,支持多模型自动弹性回退。"""
    results: List[Tuple[str, float, str]] = []
    batch_size = 20

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Gemini 客户端配置失败,自动退化为纯 Python 规则模型: {e}")
        return [classify_emotion_fallback_pure_python(c) for c in comments]

    # 候选模型:优先用户所选,再尝试备用
    candidate_models = [model_name] if model_name else []
    candidate_models.extend(["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"])
    seen: set[str] = set()
    candidate_models = [x for x in candidate_models if not (x in seen or seen.add(x))]
    active_model_name: str | None = None

    for i in range(0, len(comments), batch_size):
        batch = comments[i: i + batch_size]
        inputs = [{"id": idx, "text": text[:200]} for idx, text in enumerate(batch)]
        prompt = _build_sentiment_prompt(inputs)

        response = None
        last_err = ""
        models_to_try = [active_model_name] if active_model_name else candidate_models

        for m_name in models_to_try:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt)
                active_model_name = m_name
                break
            except Exception as e:
                last_err = str(e)
                if not active_model_name and (
                    "404" in last_err
                    or "not found" in last_err.lower()
                    or "not supported" in last_err.lower()
                    or "not_found" in last_err.lower()
                ):
                    continue
                else:
                    break

        if response is None:
            for text in batch:
                label, score, model_used = classify_emotion_fallback_pure_python(text)
                results.append((label, score, f"{model_used}(LLM失败降级)"))
            continue

        parsed = _parse_llm_json_batch(response.text, len(batch))
        if parsed is None:
            for text in batch:
                label, score, model_used = classify_emotion_fallback_pure_python(text)
                results.append((label, score, f"{model_used}(解析失败降级)"))
            continue

        for label, score, _ in parsed:
            results.append((label, score, f"Gemini ({active_model_name})"))

    return results


# ============================================================
# 4. OpenAI 兼容 API 批量打标(DeepSeek 等)
# ============================================================
def batch_analyze_sentiment_with_custom_api(
    comments: List[str], api_key: str, base_url: str, model_name: str
) -> List[Tuple[str, float, str]]:
    """使用自定义 OpenAI 兼容接口对评论进行 7 维情绪打标。"""
    results: List[Tuple[str, float, str]] = []
    batch_size = 20

    url = base_url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    if not url.rstrip("/").endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for i in range(0, len(comments), batch_size):
        batch = comments[i: i + batch_size]
        inputs = [{"id": idx, "text": text[:200]} for idx, text in enumerate(batch)]
        prompt = _build_sentiment_prompt(inputs)

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        try:
            import requests
            res = requests.post(url, headers=headers, json=payload, timeout=45)
            res.raise_for_status()
            data = res.json()
            res_text = data["choices"][0]["message"]["content"].strip()
            res_text = _strip_code_fences(res_text)

            parsed = _parse_llm_json_batch(res_text, len(batch))
            if parsed is None:
                raise ValueError("JSON 解析失败")

            for label, score, _ in parsed:
                results.append((label, score, f"Custom ({model_name})"))
        except Exception:
            for text in batch:
                label, score, model_used = classify_emotion_fallback_pure_python(text)
                results.append((label, score, f"{model_used}(API异常兜底)"))

    return results


# ============================================================
# DataFrame 包装函数
# ============================================================
def _apply_results(
    df: pd.DataFrame, results: List[Tuple[str, float, str]]
) -> pd.DataFrame:
    """将三元组结果写回 DataFrame 的 sentiment / sentiment_score / sentiment_model 列。"""
    out = df.copy()
    sentiment_labels = [r[0] for r in results]
    sentiment_scores = [r[1] for r in results]
    sentiment_models = [r[2] for r in results]
    out["sentiment"] = sentiment_labels
    out["sentiment_score"] = sentiment_scores
    out["sentiment_model"] = sentiment_models
    return out


def run_sentiment_gemini_wrapper(
    df: pd.DataFrame, gemini_api_key: str, gemini_model: str = "gemini-1.5-flash"
) -> pd.DataFrame:
    """Gemini 引擎的 DataFrame 包装。"""
    results = batch_analyze_sentiment_with_gemini(
        df["comment_text"].tolist(), gemini_api_key, gemini_model
    )
    return _apply_results(df, results)


def run_sentiment_custom_wrapper(
    df: pd.DataFrame, api_key: str, base_url: str, model_name: str
) -> pd.DataFrame:
    """自定义 API 引擎的 DataFrame 包装。"""
    results = batch_analyze_sentiment_with_custom_api(
        df["comment_text"].tolist(), api_key, base_url, model_name
    )
    return _apply_results(df, results)


def run_sentiment_local_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    """本地 VADER+SnowNLP 双引擎的 DataFrame 包装(零 API 成本)。"""
    results = batch_analyze_sentiment_with_local_nlp(df["comment_text"].tolist())
    return _apply_results(df, results)
