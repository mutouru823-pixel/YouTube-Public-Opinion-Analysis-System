# 📊 YouTube Public Opinion Analysis System (跨文化危机舆情自动化分析 SaaS)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-red)
![NLP](https://img.shields.io/badge/NLP-SnowNLP%20%7C%20VADER-brightgreen)

> **👤 开发者:** Mutou
> **🎯 核心定位:** 一个开箱即用、具有极高容错率的 YouTube 多语种舆情监控与情绪演化分析的微型 SaaS 系统。

## 💡 项目背景与商业价值 (Business Value)
本项目旨在解决传统舆情分析中“数据获取繁琐、跨文化情绪感知迟钝、API配额极易引发系统崩溃”的三大痛点。
系统打通了从“数据抓取 -> 清洗 -> NLP情绪打标 -> 交互式BI展板”的端到端自动化工作流。通过抓取海量跨语种社交媒体评论，可直接为出海品牌声誉管理、跨区域危机公关（基于 SCCT 理论）提供**秒级的数据洞察与决策支撑**。

## 🚀 核心工程亮点 (Core Features)

- **♾️ 十万级高并发与分页突破：** 摒弃单次请求限制，利用 `nextPageToken` 深度循环翻页，单次任务支持最高 **100,000 条**评论的无缝抓取。
- **🛡️ 极致的容错与优雅熔断 (Graceful Shutdown)：** - **评论区关闭规避：** 智能捕获 `HttpError`，遇到关闭评论区的视频自动跳过，绝不阻塞主线程。
  - **API 配额熔断保护：** 在 Google API 每日配额耗尽 (Quota Exceeded) 时，系统不会崩溃，而是触发“优雅中断”，并**自动保存、渲染中断前已抓取的所有数据**。
- **🧠 跨语种情绪模型全局缓存：** 集成 `SnowNLP` (中文) 与 `VADER` (英文) 双引擎。通过 `@st.cache_resource` 实现 VADER 模型的全局单例加载，彻底消除十万级循环实例化带来的内存灾难与性能瓶颈。
- **📈 交互式数据展板 (Dashboard)：** 基于 `Streamlit` 与 `Plotly`，动态渲染舆情时间趋势折线图、情绪分布环形图及高频词云，并提供原始数据一键 CSV 导出。

## ⚙️ 快速部署与运行 (Quick Start)

### 1. 本地环境运行
```bash
# 1. 克隆仓库
git clone [https://github.com/mutouru823-pixel/YouTube-Public-Opinion-Analysis-System.git](https://github.com/mutouru823-pixel/YouTube-Public-Opinion-Analysis-System.git)
cd YouTube-Public-Opinion-Analysis-System

# 2. 安装依赖 (Dependencies)
pip install -r requirements.txt

# 3. 运行 Streamlit 应用
streamlit run app.py

### 2. 云端一键访问 (TODO)
👉 点击体验在线系统:https://youtube-public-opinion-analysis-system-cdqeuprjfnzn5vphc5cyrt.streamlit.app/

📂 核心依赖结构
google-api-python-client: 处理 YouTube Data API v3 核心抓取逻辑。

pandas: 海量结构化数据的高效清洗与时序聚合。

plotly: 商业级交互式图表渲染。

wordcloud & jieba: 中英双语文本高频词提取与可视化（自带跨平台字体兼容处理）。

🔮 架构延展性 (Extensibility)
系统内部已预留 classify_sentiment_with_ext_api 接口，支持未来无缝接入 DeepSeek 等大语言模型 (LLM)，以实现如“极度厌恶”、“轻微愤怒”等更细颗粒度的多维情绪分类。
