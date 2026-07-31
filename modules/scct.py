"""SCCT 情境危机传播理论学术编码模块。

基于 Coombs 的 SCCT (Situational Crisis Communication Theory) 对负向语料
进行学术定量内容分析与个案编码,生成 APA 7th 标准参考文献报告。

提供三个入口:
- ``generate_scct_insights`` —— Google Gemini 引擎
- ``generate_scct_insights_custom_api`` —— OpenAI 兼容 API 引擎
- ``get_static_crisis_handbook`` —— API 不可用时的离线危机手册兜底
"""

from __future__ import annotations

from typing import List

import streamlit as st


# ============================================================
# 统一的 SCCT 学术编码 Prompt(消除两处重复)
# ============================================================
SCCT_PROMPT_TEMPLATE: str = """
你是一名资深传播学学者和计算社会学(Computational Social Science)科研专家。请根据 Coombs 的 **情境危机传播理论 (Situational Crisis Communication Theory, SCCT)**,对以下 YouTube 视频语料中的负面抗议意见进行严格的学术定量内容分析与个案编码。

负面评论样本:
\"\"\"
{comments_text}
\"\"\"

请生成一份专业、符合国际核心学术期刊发表标准、高度结构化的【SCCT 学术定量内容分析与危机个案编码报告】。报告应包含以下核心板块,并以精美专业的 Markdown 格式输出:

### 🔬 1. 舆论文本议题编码与情绪特征 (Topic Coding & Emotional Profiles)
- **公众舆论核心痛点与编码(Top 3 Issues)**:提取网民最强烈的不满、质疑和诉求,进行语义主题编码,并剖析其深层社会心理动因。
- **情感危机烈度与声誉危害评估 (Reputational Threat Assessment)**:评估负向情感倾斜严重度,量化网民情绪对抗烈度,分析其对品牌象征性社会资本与媒介声誉的短期与长期危害。

### 📚 2. SCCT 危机情境学术编码 (SCCT Academic Case-Study Coding)
基于 Coombs 的 SCCT 理论,判断该事件属于以下哪类危机集群(进行严密的学术理论论证,给出具体编码理由及责任归因强度的研判):
- **受害者集群 (Victim Cluster)**:组织被视为外部被侵害方(如自然灾害、谣言抹黑、外部恶意入侵)。归因责任:极低 (Minimal Attribution)。
- **事故集群 (Accidental Cluster)**:组织非蓄意但因技术、操作故障诱发(如意外设备故障、非恶意产品缺陷)。归因责任:中等 (Moderate Attribution)。
- **可防范集群 (Preventable Cluster)**:组织故意违法违规或管理严重失职、知情隐瞒不报导致。归因责任:极高 (Severe Attribution)。

### 📈 3. 基于 SCCT 模型的理论化应对策略矩阵 (Theoretical Strategy Matrix)
根据前面的危机编码,推荐采取何种危机沟通响应策略(提供符合 Coombs 理论框架的策略配比建议,并给出学术性话术要点指导):
- **否认策略 (Denial)**:划清界限、驳斥谣言或强调组织无辜。(适用受害者集群,低归因责任)
- **淡化策略 (Diminish)**:强调外部客观因素,重申损害可控,降低公众对危机严重性的感知。(适用事故集群,中等归因责任)
- **重塑策略 (Rebuild)**:诚恳道歉,承担全部责任,并提供实质性补偿(Compensation)与纠正措施(Corrective Action)。(适用可防范/严重事故集群,高归因责任)
- **迎合/强化策略 (Bolstering)**:提醒公众组织过去的良好记录,对支持者表示感谢,重建信任纽带。

### 📝 4. 危机响应个案研究双语示范文本设计 (Bilingual Narrative Research Design)
提供一版用于本案例实证研究参考的官方声明/道歉信学术模型样本:
- **中文版本 (Chinese Empirical Template)**
- **英文版本 (English Empirical Template)**
- **文本修辞学与叙事要点解析**:从叙事学和修辞学角度,阐明该文本设计如何有效对应危机责任规避或公众情感修复(例如:优先关注受害人利益、展现主动纠错担当、承诺具体的后续整改路线)。

### 📖 5. 学术参考文献 (APA 7th Edition References)
列出报告中引用的主要 SCCT 理论与计算传播学核心学术文献列表,必须采用严格的 **APA 第 7 版标准学术参考文献格式**。至少包含 Timothy Coombs 的经典论文与专著。
"""


def _prepare_comments_text(negative_comments: List[str]) -> str:
    """取前 40 条负面评论,拼成 prompt 输入文本。"""
    sample_comments = negative_comments[:40]
    return "\n".join([f"- {c}" for c in sample_comments])


# ============================================================
# 离线危机手册兜底
# ============================================================
def get_static_crisis_handbook(err_msg: str) -> str:
    """提供标准跨区域危机公关应对指南与双语道歉大纲(离线公关自诊断中枢)。"""
    return f"""
### 🚨 AI 决策引擎触发配额熔断 / 限流保护 (Rate Limit & Quota Exceeded)

> **⚠️ 提示**:检测到您的 AI 接口调用目前已达到额度限制、触发频率限流或连接异常(原始报错:{err_msg})。
> 为了不影响您的决策,根据 **SCCT 危机公关理论防御性原则**,系统已自动启动**「离线危机公关自诊断中枢」**,为您提供标准的跨区域公关应对指南与双语通用道歉大纲。

---

# 📚 《出海企业标准 SCCT 危机沟通自诊断手册》
*(Timothy Coombs 教授情境危机传播理论标准版)*

在缺乏实时 AI 分析时,请依据本手册分步进行品牌舆情自诊断:

## 📌 第一步:舆情事件责任定性 (Attribution of Responsibility)
根据负面评论的爆发诱因,对照下表确定事件属于哪类 **SCCT 危机集群 (Crisis Cluster)**:

| 危机集群 (Cluster) | 现实场景实例 (Examples) | 网民责任归因 (Attribution) | 推荐核心公关态度 (Posture) |
| :--- | :--- | :--- | :--- |
| **受害者集群 (Victim)** | 谣言恶意抹黑、自然灾害、外部骇客攻击 | 极低 (Minimal) | **驳斥与澄清 (Denial)** / 划清界限 |
| **事故集群 (Accidental)** | 技术突发故障、非恶意产品设计缺陷、供应链延误 | 中等 (Moderate) | **淡化客观原因 (Diminish)** + 修正承诺 |
| **可防范集群 (Preventable)** | 故意违法违规、管理严重失职、知情隐瞒不报 | 极高 (Severe) | **彻底重塑信任 (Rebuild)** + 赔偿与整改 |

---

## 📈 第二步:公关战略响应矩阵 (SCCT Response Matrix)
请根据第一步的分类,针对性采取以下公关话术切入点:

### 1. 否认与澄清策略 (Denial Strategy) —— *适用于受害者集群*
- **核心切入点**:证明公司与起因无关,或指明恶意来源。
- **公关原则**:言简意赅,用客观数据说话,不激怒网民。

### 2. 淡化与隔离策略 (Diminish Strategy) —— *适用于事故集群*
- **核心切入点**:阐明这是小概率单点突发事故,强调公司已启动纠错,证明危害在可控范围内。
- **公关原则**:表达遗憾但不主动招揽无端指责。

### 3. 重塑与纠正策略 (Rebuild Strategy) —— *适用于可防范集群/严重事故*
- **核心切入点**:**"黄金24小时"内彻底道歉**。不推诿、不寻找客观借口。宣布成立专项小组,并公布具体的**赔偿计划 (Compensation)** 与 **纠正整改路线图 (Corrective Action)**。
- **公关原则**:坦诚是唯一的解药,整改动作必须可衡量。

---

## 📝 第三步:通用品牌公关响应双语模版 (Off-the-shelf Crisis Templates)

若您急需发布声明,请根据事件性质参考以下**模块化公关模版**进行措辞微调:

### 🟢 模版 A:技术突发与产品故障通用稿 (适用于事故集群)
```markdown
【中文声明】
我们深知,近日发生的 [填写事件,例如:服务短暂中断/部分产品出货延误] 给广大用户带来了极大的不便。对此,我们表示最诚挚的歉意。
经核查,本次事件由 [填写具体客观原因,例如:海外服务器瞬时网络波动] 导致。我们已于第一时间内完成技术修复,目前系统已全面恢复平稳。
作为一家负责任的企业,我们已启动服务保障机制,并将全力避免此类事故再次发生。

【English Version】
We sincerely apologize for the recent [e.g., service disruption / product delivery delay] that caused inconvenience to our valued users.
Upon investigation, this was due to [e.g., unexpected regional server fluctuation]. Our engineering team resolved the issue immediately, and services are fully restored.
We take this matter seriously and are implementing additional safeguards to ensure systemic stability.
```

### 🔴 模版 B:管理失职与服务漏洞通用道歉信 (适用于可防范集群)
```markdown
【中文道歉信】
近日,关于 [填写曝光事件] 的报道引发了社会的广泛关注与网民批评。在此,我们不作任何辩解,郑重地向受影响的客户及公众致以最深的歉意。
这暴露出我们在 [填写管理漏洞,例如:海外售后响应/供应链质量把控] 上的严重缺失。我们已成立由 CEO 挂帅的专项整改小组,并承诺采取以下措施:
1. 立即开展全渠道服务审计与整改。
2. 对受影响用户提供 [填写具体补偿方案]。
3. 设立公开监督渠道,定期向公众汇报进展。

【English Version】
We deeply apologize for the recent events regarding [e.g., customer service oversight]. We accept full responsibility and make no excuses.
This incident exposed significant vulnerabilities in our [e.g., quality control / service response]. We have established an immediate task force led by our CEO to implement the following actions:
1. Conduct an immediate channel-wide operational audit.
2. Provide [e.g., compensation / refunds] to affected users.
3. Establish a transparent communication line to report our progress.
```

---
*(若需恢复高精度 AI 舆情研判与定制化道歉声明,请确认您的 API 额度充足或更换高可用的 API Key / 基础端点。)*
"""


# ============================================================
# Gemini SCCT 编码
# ============================================================
def generate_scct_insights(
    negative_comments: List[str], api_key: str, model_name: str = "gemini-1.5-flash"
) -> str:
    """使用 Google Gemini API 基于 Coombs 的 SCCT 提供学术公关策略报告。"""
    if not api_key:
        return "⚠️ 请在左侧参数配置面板输入 API Key 以激活 SCCT 公关战略模块。"

    if not negative_comments:
        return "💡 暂未检测到明显的负面言论,品牌声誉安全,无需触发 SCCT 危机预案。"

    comments_text = _prepare_comments_text(negative_comments)
    prompt = SCCT_PROMPT_TEMPLATE.format(comments_text=comments_text)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

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
                break
            except Exception as e:
                last_err = str(e)
                if "404" in last_err or "not found" in last_err.lower() or "not supported" in last_err.lower() or "not_found" in last_err.lower():
                    continue
                else:
                    raise e

        if response is None:
            raise RuntimeError(f"已尝试所有候选模型 {candidate_models},均不可用。最后一次模型报错信息: {last_err}")

        return response.text
    except Exception as e:
        return get_static_crisis_handbook(str(e))


# ============================================================
# 自定义 API SCCT 编码
# ============================================================
def generate_scct_insights_custom_api(
    negative_comments: List[str], api_key: str, base_url: str, model_name: str
) -> str:
    """使用自定义 OpenAI 兼容 API 基于 Coombs 的 SCCT 提供学术公关策略报告。"""
    if not api_key:
        return "⚠️ 请在左侧参数配置面板输入 API Key 以激活 SCCT 公关战略模块。"

    if not negative_comments:
        return "💡 暂未检测到明显的负面言论,品牌声誉安全,无需触发 SCCT 危机预案。"

    comments_text = _prepare_comments_text(negative_comments)
    prompt = SCCT_PROMPT_TEMPLATE.format(comments_text=comments_text)

    url = base_url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    if not url.rstrip("/").endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
    }

    try:
        import requests
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return get_static_crisis_handbook(str(e))
