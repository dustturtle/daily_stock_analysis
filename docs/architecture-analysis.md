# Daily Stock Analysis — 技术架构分析与 MVP 复刻指南

> 本文档面向希望理解本项目架构并复刻最小化 MVP 的开发者。
> 基于 v3.9.0 版本分析，生成日期：2026-03-20。

---

## 目录

- [1. 项目定位与核心理念](#1-项目定位与核心理念)
- [2. 整体技术架构](#2-整体技术架构)
- [3. 分层架构详解](#3-分层架构详解)
- [4. 核心模块拆解](#4-核心模块拆解)
- [5. 数据流与执行流水线](#5-数据流与执行流水线)
- [6. 设计模式与设计原则](#6-设计模式与设计原则)
- [7. 技术栈总览](#7-技术栈总览)
- [8. MVP 核心功能提炼](#8-mvp-核心功能提炼)
- [9. MVP 实现路线图](#9-mvp-实现路线图)
- [10. 参考文件索引](#10-参考文件索引)

---

## 1. 项目定位与核心理念

### 1.1 项目定位

Daily Stock Analysis 是一个 **AI 驱动的股票智能分析系统**，覆盖 A 股、港股、美股三大市场。它将传统技术分析与大语言模型（LLM）深度融合，自动生成包含「决策仪表盘」的分析报告，并通过多渠道推送给用户。

### 1.2 设计理念

| 理念 | 体现 |
|------|------|
| **数据源容错** | 6 个数据源按优先级自动 fallback，单一数据源故障不影响整体 |
| **LLM 统一抽象** | 通过 LiteLLM 统一接入 Gemini/Claude/GPT/DeepSeek 等模型，支持多 key 轮转与 fallback |
| **流水线编排** | 将「取数据 → 技术分析 → LLM 分析 → 生成报告 → 推送通知」组织为可复用的 Pipeline |
| **多终端覆盖** | CLI / API Server / Web UI / Desktop App / Bot（钉钉/飞书/Discord）全覆盖 |
| **配置驱动** | 所有行为通过 `.env` 配置，不配置也可运行，配置后增强能力 |
| **渐进增强** | 核心流程（数据+分析+报告）始终可用，Agent、Bot、Portfolio 等为可选增强 |

### 1.3 核心价值链

```
股票代码 → 行情数据 → 技术指标计算 → LLM 智能分析 → 结构化报告 → 多渠道推送
```

这条价值链是整个系统的主干，所有其他功能（Agent、Portfolio、Backtest、Bot）都围绕它展开。

---

## 2. 整体技术架构

### 2.1 架构全景图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户接入层 (Presentation)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │  CLI      │  │ Web UI   │  │ Desktop  │  │ Bot      │  │ API  │ │
│  │ main.py   │  │ React    │  │ Electron │  │ 钉钉/飞书 │  │ REST │ │
│  └─────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──┬───┘ │
└────────┼─────────────┼─────────────┼─────────────┼────────────┼─────┘
         │             │             │             │            │
         └─────────────┴─────────────┴─────────────┴────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────┐
│                        API 网关层 (FastAPI)                          │
│                    api/v1/endpoints/*                                │
│             ┌───────────────────────────────┐                       │
│             │  认证 · 限流 · 错误处理 · CORS   │                       │
│             └───────────────────────────────┘                       │
└────────────────────────────────────┼────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────┐
│                        业务服务层 (Services)                          │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ AnalysisService│  │ TaskService   │  │ PortfolioService         │ │
│  │ HistoryService │  │ TaskQueue     │  │ BacktestService          │ │
│  │ StockService   │  │ ConfigService │  │ SocialSentimentService   │ │
│  └────────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘ │
└───────────┼─────────────────┼───────────────────────┼───────────────┘
            │                 │                       │
┌───────────┼─────────────────┼───────────────────────┼───────────────┐
│           │          核心引擎层 (Core)                │               │
│  ┌────────┴──────────────────────────────────────────┴──────────┐   │
│  │              StockAnalysisPipeline (流水线编排)                 │   │
│  │  ┌──────────────┐  ┌────────────┐  ┌────────────────────┐   │   │
│  │  │ 技术分析引擎   │  │ LLM 分析器  │  │ 搜索/新闻聚合引擎   │   │   │
│  │  │StockTrend     │  │Gemini       │  │SearchService       │   │   │
│  │  │Analyzer       │  │Analyzer     │  │(5 搜索源)           │   │   │
│  │  └──────────────┘  └────────────┘  └────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Multi-Agent 系统（可选增强）                        │   │
│  │  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │   │
│  │  │TechnicalAgt│ │IntelAgent│ │RiskAgent │ │DecisionAgent │  │   │
│  │  └────────────┘ └──────────┘ └──────────┘ └──────────────┘  │   │
│  │  工具注册表 · ReAct 循环 · Skill/Strategy 路由                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────┐
│                      数据访问层 (Repositories + Providers)           │
│  ┌──────────────────────────────┐  ┌────────────────────────────┐   │
│  │ Repositories (SQLite ORM)    │  │ DataFetcherManager          │   │
│  │ AnalysisRepo · StockRepo     │  │ 6 数据源 fallback 链          │   │
│  │ PortfolioRepo · BacktestRepo │  │ efinance → akshare → tushare │   │
│  └──────────────────────────────┘  │ → pytdx → baostock → yfinance│   │
│                                    └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────┐
│                      基础设施层 (Infrastructure)                      │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ SQLite DB│  │ Config单例  │  │ 通知分发      │  │ 日志系统     │  │
│  │ storage  │  │ .env 驱动   │  │ 11 个渠道     │  │ logging     │  │
│  └──────────┘  └────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构与职责映射

```
daily_stock_analysis/
├── main.py                 # CLI 入口：解析参数 → 调度 Pipeline → 定时任务
├── server.py               # API 入口：创建 FastAPI app → 启动 uvicorn
│
├── src/                    # 核心业务代码（~101 个 Python 文件）
│   ├── core/               #   流水线编排、配置管理、回测引擎、交易日历
│   ├── agent/              #   Multi-Agent 系统（4 个专家 Agent + 工具集）
│   ├── services/           #   业务服务层（20+ 服务类）
│   ├── repositories/       #   数据访问层（4 个 Repository）
│   ├── schemas/            #   数据结构定义（Pydantic Schema）
│   ├── notification_sender/#   11 个通知渠道发送器
│   ├── utils/              #   工具函数
│   ├── analyzer.py         #   LLM 分析器（GeminiAnalyzer）
│   ├── stock_analyzer.py   #   技术分析引擎（MA/MACD/RSI/乖离率）
│   ├── search_service.py   #   新闻搜索聚合（5 个搜索源）
│   ├── notification.py     #   通知分发中心
│   ├── storage.py          #   SQLAlchemy ORM 模型与数据库管理
│   └── config.py           #   配置单例（从 .env 读取）
│
├── data_provider/          # 行情数据源层（6 个 Fetcher + Fallback 管理）
├── api/                    # FastAPI REST API v1（10 个端点模块）
├── bot/                    # Bot 平台接入（钉钉/飞书/Discord）
│
├── apps/dsa-web/           # Web 前端（React 19 + TypeScript + Vite）
├── apps/dsa-desktop/       # 桌面端（Electron 31）
│
├── templates/              # 报告模板（Jinja2）
├── strategies/             # 自定义交易策略（YAML）
├── docker/                 # Docker 构建与编排
├── scripts/                # 构建与运维脚本
└── tests/                  # 测试套件（70+ 测试文件）
```

---

## 3. 分层架构详解

### 3.1 用户接入层

| 接入方式 | 入口文件 | 说明 |
|---------|---------|------|
| **CLI** | `main.py` | 支持单次运行、定时调度、市场综述、服务模式等多种模式 |
| **API Server** | `server.py` → `api/app.py` | FastAPI + uvicorn，提供 RESTful API |
| **Web UI** | `apps/dsa-web/` | React 19 SPA，通过 API 与后端交互 |
| **Desktop** | `apps/dsa-desktop/` | Electron 封装 Web UI，支持本地后端自启动 |
| **Bot** | `bot/` | Webhook/Stream 接入钉钉、飞书、Discord |

### 3.2 API 网关层

```
api/
├── app.py                    # FastAPI 应用工厂（create_app）
├── deps.py                   # 依赖注入
├── middlewares/
│   ├── auth.py               # JWT/Token 认证中间件
│   └── error_handler.py      # 全局异常处理
└── v1/
    ├── router.py             # 路由聚合
    └── endpoints/            # 10 个端点模块
        ├── analysis.py       #   分析触发（异步任务 + SSE 推送）
        ├── history.py        #   历史查询与导出
        ├── stocks.py         #   股票搜索与实时行情
        ├── portfolio.py      #   投资组合 CRUD
        ├── backtest.py       #   回测触发
        ├── agent.py          #   Agent 对话
        ├── system_config.py  #   系统配置读写
        ├── auth.py           #   登录/登出
        ├── health.py         #   健康检查
        └── usage.py          #   LLM 用量统计
```

关键设计：
- **异步任务队列**：分析请求不阻塞，返回 `task_id`，客户端通过 SSE 或轮询获取结果
- **依赖注入**：通过 `deps.py` 注入 Config、DB 等公共依赖
- **中间件链**：认证（可选） → 错误处理 → CORS

### 3.3 业务服务层

```python
# 服务层关键类（src/services/）
AnalysisService     # 分析编排服务 — 协调 Pipeline 执行
TaskService         # 任务管理服务 — CRUD + 状态机
TaskQueue           # 异步任务队列 — 去重 + 状态追踪 + SSE 推送
HistoryService      # 历史查询服务 — 分页 + 导出 + 对比
StockService        # 股票信息服务 — 代码解析 + 搜索
PortfolioService    # 投资组合服务 — 持仓管理 + 收益计算
BacktestService     # 回测服务 — 历史验证 + 准确率追踪
SystemConfigService # 系统配置服务 — 运行时配置 CRUD
SocialSentimentService # 社交情绪服务 — Reddit/X 舆情
NameToCodeResolver  # 名称→代码解析 — 拼音 + 模糊匹配
```

### 3.4 核心引擎层

这是项目最核心的部分，包含三个子引擎：

#### (1) 分析流水线 — `StockAnalysisPipeline`

```python
# src/core/pipeline.py — 流水线编排（69 KB，项目最大文件）
class StockAnalysisPipeline:
    """
    职责：
    1. 管理整个分析流程
    2. 协调数据获取、存储、搜索、分析、通知等模块
    3. 实现并发控制和异常处理（ThreadPoolExecutor）
    """
    def run(self, stock_codes: List[str]) -> List[AnalysisResult]:
        # 并发分析多只股票
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {executor.submit(self.analyze_stock, code): code for code in stock_codes}
            ...

    def analyze_stock(self, stock_code: str) -> AnalysisResult:
        # 单只股票分析全流程
        # 1. DataFetcherManager.get_historical_data()  → 行情数据
        # 2. StockTrendAnalyzer.analyze()              → 技术指标
        # 3. SearchService.search()                    → 新闻搜索
        # 4. GeminiAnalyzer.analyze()                  → LLM 分析
        # 5. DatabaseManager.save_analysis()           → 持久化
        # 6. 返回 AnalysisResult
```

#### (2) 技术分析引擎 — `StockTrendAnalyzer`

```python
# src/stock_analyzer.py
# 交易理念：严进策略 + 趋势交易 + 效率优先
class StockTrendAnalyzer:
    # 计算指标：MA5/MA10/MA20/MA60, MACD, RSI, 乖离率, 量能形态
    # 输出枚举：TrendStatus(7 级), VolumeStatus(5 级), BuySignal(6 级)
    def analyze(self, df: pd.DataFrame) -> TrendAnalysisResult
```

#### (3) LLM 分析器 — `GeminiAnalyzer`

```python
# src/analyzer.py
class GeminiAnalyzer:
    # 通过 LiteLLM 统一调用 Gemini/Claude/GPT/DeepSeek 等
    # 构建包含技术指标 + 新闻 + 行情的 Prompt
    # 输出结构化的 AnalysisResult（含决策仪表盘）
    def analyze(self, stock_code, stock_name, df, trend_result, news, ...) -> AnalysisResult
```

#### (4) Multi-Agent 系统（可选增强）

```
src/agent/
├── orchestrator.py    # 多 Agent 编排（quick/standard/full/specialist 模式）
├── executor.py        # 单 Agent ReAct 循环执行器
├── runner.py          # Agent 循环运行器
├── agents/            # 4 个专家 Agent
│   ├── technical_agent.py    # 技术面分析
│   ├── intel_agent.py        # 情报收集
│   ├── risk_agent.py         # 风险评估
│   └── decision_agent.py     # 综合决策
├── tools/             # Agent 可调用的工具
│   ├── analysis_tools.py     # 行情查询、趋势分析
│   ├── data_tools.py         # 筹码分布、资金流向
│   ├── search_tools.py       # 新闻搜索
│   └── market_tools.py       # 大盘指数、板块排名
└── skills/            # 11 个内置交易策略（技能）
```

### 3.5 数据访问层

#### 数据源管理 — `DataFetcherManager`

```python
# data_provider/base.py
# 策略模式 — 6 个数据源按优先级自动切换
#
# 优先级链（默认）：
#   efinance(P0) → akshare(P1) → tushare(P2) → pytdx(P2) → baostock(P3) → yfinance(P4)
#
# 关键特性：
# - 动态优先级：根据成功率自动调整
# - 线程安全：RLock 保护
# - 限流保护：内置 rate limiting
# - 反封禁：随机 User-Agent
```

#### 数据库访问 — `Repositories`

```python
# src/repositories/
AnalysisRepository    # 分析历史 CRUD
StockRepository       # 日行情数据 CRUD
PortfolioRepository   # 投资组合 CRUD
BacktestRepository    # 回测记录 CRUD
```

#### 数据库模型 — `storage.py`

```
SQLite 数据库表：
├── stock_daily        # 日 K 线 + 技术指标
├── analysis           # 分析结果 + 决策仪表盘 JSON
├── portfolio          # 投资组合
├── portfolio_holding  # 持仓明细
├── backtest           # 回测记录
├── backtest_daily     # 回测每日数据
└── llm_usage          # LLM Token 用量（计费追踪）
```

### 3.6 基础设施层

| 模块 | 文件 | 职责 |
|------|------|------|
| **配置中心** | `src/config.py` (~100 KB) | 环境变量解析、校验、单例访问 |
| **通知分发** | `src/notification.py` + `notification_sender/` | 11 个渠道（企业微信/飞书/Telegram/Discord/Slack/邮件/Pushover 等） |
| **数据库** | `src/storage.py` (~80 KB) | SQLAlchemy ORM + SQLite |
| **日志** | `src/logging_config.py` | 结构化日志配置 |
| **报告渲染** | `src/md2img.py` + `templates/` | Markdown → HTML → 图片 |
| **多语言** | `src/report_language.py` | 中/英文报告模板切换 |

---

## 4. 核心模块拆解

### 4.1 分析结果数据结构 — `AnalysisResult`

这是贯穿整个系统的核心数据结构：

```python
@dataclass
class AnalysisResult:
    code: str                        # 股票代码
    name: str                        # 股票名称

    # ---- 核心指标 ----
    sentiment_score: int             # 综合评分 0-100
    trend_prediction: str            # 趋势预测（强烈看多/看多/震荡/看空/强烈看空）
    operation_advice: str            # 操作建议（买入/加仓/持有/减仓/卖出/观望）
    decision_type: str               # 决策类型（buy/hold/sell）
    confidence_level: str            # 置信度（高/中/低）

    # ---- 决策仪表盘 ----
    dashboard: Dict                  # 完整仪表盘数据
    #   ├── core_conclusion          #   一句话结论 + 信号类型 + 仓位建议
    #   ├── data_perspective         #   趋势状态 + 价格位置 + 量能 + 筹码
    #   ├── intelligence             #   新闻 + 风险提醒 + 利好催化
    #   └── battle_plan              #   狙击点位 + 仓位策略 + 行动清单

    # ---- 分析详情 ----
    trend_analysis: str              # 走势形态
    technical_analysis: str          # 技术指标
    fundamental_analysis: str        # 基本面
    news_summary: str                # 新闻摘要
    analysis_summary: str            # 综合摘要
    key_points: str                  # 核心看点
    risk_warning: str                # 风险提示

    # ---- 元数据 ----
    model_used: str                  # 使用的 LLM 模型
    search_performed: bool           # 是否联网搜索
    current_price: float             # 分析时股价
    change_pct: float                # 涨跌幅
```

### 4.2 配置系统 — `Config`

```python
# 单例模式访问
from src.config import get_config
config = get_config()

# 核心配置分类：
# ├── 自选股：  config.stock_list
# ├── LLM：    config.litellm_model, config.litellm_fallback_models
# ├── API Key：config.gemini_api_key, config.deepseek_api_key, ...
# ├── 数据源：  config.tushare_token
# ├── 搜索：   config.bocha_api_keys, config.tavily_api_keys, ...
# ├── 通知：   config.wechat_webhook, config.telegram_bot_token, ...
# ├── 调度：   config.schedule_enabled, config.schedule_time
# ├── Agent：  config.agent_mode, config.agent_skills
# └── 系统：   config.max_workers, config.report_language, config.debug
```

### 4.3 通知系统 — `NotificationService`

```python
# 多继承 Mixin 模式 — 每个渠道是一个独立的 Sender
class NotificationService(
    WechatSender,       # 企业微信 Webhook
    FeishuSender,       # 飞书 Webhook
    TelegramSender,     # Telegram Bot
    DiscordSender,      # Discord Webhook
    SlackSender,        # Slack Webhook
    EmailSender,        # SMTP 邮件
    PushoverSender,     # Pushover 推送
    PushplusSender,     # PushPlus 推送
    Serverchan3Sender,  # Server酱
    AstrbotSender,      # Astrbot
    CustomWebhookSender # 自定义 Webhook
):
    def send(self, content: str) -> bool:
        # 遍历所有已配置渠道，逐一发送
        # 单渠道失败不影响其他渠道
```

### 4.4 搜索引擎聚合 — `SearchService`

```python
# 5 个搜索源的优先级 fallback：
# Bocha（中文优化）→ Tavily → SerpAPI → Brave → SearXNG（自托管）
# MiniMax（另一条搜索路径）

class SearchService:
    def search(self, stock_name, stock_code) -> str:
        # 聚合新闻、公告、市场评论
        # 返回格式化的文本，注入 LLM Prompt
```

---

## 5. 数据流与执行流水线

### 5.1 CLI 分析流程

```
用户执行: python main.py --stocks 600519
          │
          ▼
    parse_arguments()
          │
          ▼
    run_full_analysis()
          │
          ▼
    StockAnalysisPipeline.run([600519])
          │
          ├──► DataFetcherManager.get_historical_data("600519")
          │      └─ efinance → [失败] → akshare → [成功] → 返回 DataFrame
          │
          ├──► StockTrendAnalyzer.analyze(df)
          │      └─ 计算 MA/MACD/RSI/乖离率/量能 → TrendAnalysisResult
          │
          ├──► SearchService.search("贵州茅台", "600519")
          │      └─ Bocha → [成功] → 返回新闻摘要文本
          │
          ├──► GeminiAnalyzer.analyze(code, name, df, trend, news, ...)
          │      └─ 构造 Prompt → LiteLLM 调用 → 解析 JSON → AnalysisResult
          │
          ├──► DatabaseManager.save_analysis(result)
          │      └─ 持久化到 SQLite
          │
          └──► NotificationService.send(report_markdown)
                 ├─ 企业微信 Webhook → ✓
                 ├─ Telegram Bot → ✓
                 └─ 邮件 SMTP → ✓
```

### 5.2 API 异步分析流程

```
POST /api/v1/analysis/analyze { "stock_code": "600519" }
     │
     ├─► 去重检查（已有相同任务 → 409 Conflict）
     ├─► 创建异步任务，入队 TaskQueue
     └─► 返回 202 Accepted { "task_id": "xxx" }
     
     ─── 后台执行 ───
     │
     TaskQueue Worker:
     ├─► StockAnalysisPipeline.analyze_stock("600519")
     ├─► 存储结果到 DB
     └─► 更新任务状态 RUNNING → COMPLETED
     
     ─── 客户端获取结果 ───
     │
     GET /api/v1/analysis/tasks/stream (SSE)
     └─► 实时推送任务状态变更
     
     GET /api/v1/analysis/status/{task_id}
     └─► 轮询获取结果
```

### 5.3 Bot 交互流程

```
用户在钉钉发送: /analyze 600519
     │
     ├─► Webhook → handler.py → 签名校验
     ├─► dispatcher.py → 路由到 AnalyzeCommand
     ├─► AnalyzeCommand.execute()
     │     └─► StockAnalysisPipeline.analyze_stock("600519")
     └─► 格式化结果 → 回复到钉钉群
```

---

## 6. 设计模式与设计原则

### 6.1 核心设计模式

| 模式 | 应用位置 | 说明 |
|------|---------|------|
| **策略模式 (Strategy)** | `DataFetcherManager` | 6 个数据源实现统一接口，运行时按优先级动态切换 |
| **工厂模式 (Factory)** | `src/agent/factory.py` | 根据配置创建 Single/Multi Agent 执行器 |
| **单例模式 (Singleton)** | `Config`, `DatabaseManager` | 全局唯一实例，`get_config()` / `get_db()` |
| **仓库模式 (Repository)** | `src/repositories/` | 将数据访问逻辑从业务逻辑中分离 |
| **模板方法 (Template)** | `BaseAgent`, `BaseCommand`, `BaseFetcher` | 定义算法骨架，子类实现具体步骤 |
| **观察者模式 (Observer)** | `NotificationService` | 分析完成后，通知所有已注册渠道 |
| **适配器模式 (Adapter)** | `FundamentalAdapter`, 各 Bot Platform | 统一不同外部系统的接口 |
| **中间件模式 (Middleware)** | FastAPI auth/error handler | 请求处理管道 |
| **流水线模式 (Pipeline)** | `StockAnalysisPipeline` | 将分析过程编排为有序步骤链 |
| **Mixin 模式** | `NotificationService` | 通过多继承组合 11 个 Sender |

### 6.2 设计原则

| 原则 | 体现 |
|------|------|
| **单一数据源故障不拖垮全流程** | DataFetcherManager 自动 fallback |
| **单一通知渠道故障不拖垮全流程** | NotificationService 逐渠道发送，独立容错 |
| **配置驱动，不配置也可运行** | 所有功能默认关闭或有 fallback 行为 |
| **渐进增强** | 核心流程（数据+分析）始终可用，Agent/Bot/Portfolio 可选 |
| **关注点分离** | 数据获取、技术分析、LLM 分析、通知推送各自独立模块 |
| **DRY (Don't Repeat Yourself)** | 统一的代码规范化、统一的 LLM 抽象（LiteLLM）、统一的通知接口 |

---

## 7. 技术栈总览

### 7.1 后端

| 类别 | 技术 | 用途 |
|------|------|------|
| **语言** | Python 3.10+ | 全栈后端 |
| **Web 框架** | FastAPI + uvicorn | REST API + SSE |
| **ORM** | SQLAlchemy 2.0 + SQLite | 数据持久化 |
| **LLM 客户端** | LiteLLM | 统一接入 Gemini/Claude/GPT/DeepSeek |
| **数据处理** | pandas + numpy | 行情数据分析 |
| **定时任务** | schedule | 每日定时执行 |
| **交易日历** | exchange-calendars | A 股/港股/美股交易日判断 |
| **重试机制** | tenacity | 指数退避重试 |
| **模板引擎** | Jinja2 | 报告模板 |
| **Markdown 转图片** | markdown2 + imgkit (wkhtmltopdf) | 报告渲染 |
| **配置管理** | python-dotenv | .env 文件加载 |
| **HTTP 客户端** | requests + httpx[socks] | 网络请求 + 代理 |

### 7.2 数据源

| 优先级 | 数据源 | 库 | 覆盖市场 |
|--------|--------|-----|---------|
| P0 | 东方财富 | efinance | A 股 |
| P1 | 东方财富(爬虫) | akshare | A 股/港股 |
| P2 | 挖地兔 Pro | tushare | A 股 |
| P2 | 通达信 | pytdx | A 股 |
| P3 | 证券宝 | baostock | A 股 |
| P4 | Yahoo Finance | yfinance | 全球 |

### 7.3 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19 | UI 框架 |
| TypeScript | — | 类型安全 |
| Vite | — | 构建工具 |
| TailwindCSS | 4 | 样式系统 |
| Zustand | — | 状态管理 |
| Axios | — | HTTP 客户端 |
| React-Markdown | — | 报告渲染 |
| Electron | 31 | 桌面端封装 |

---

## 8. MVP 核心功能提炼

### 8.1 MVP 目标

从完整系统中提炼出 **最小可用产品**，保留核心价值链，剔除增强功能。

### 8.2 功能取舍矩阵

| 功能 | 完整版 | MVP | 理由 |
|------|--------|-----|------|
| ✅ 行情数据获取 | 6 个数据源 + fallback | **1 个数据源**（akshare 或 yfinance） | 一个稳定数据源即可，无需 fallback |
| ✅ 技术指标计算 | MA/MACD/RSI/乖离率/量能 | **MA + 量能**（最小子集） | 够 LLM 分析即可 |
| ✅ LLM 智能分析 | LiteLLM 多模型 + fallback | **单个 LLM API**（如 DeepSeek） | 一个即可，直接调 OpenAI SDK |
| ✅ 结构化报告 | 完整仪表盘 + 多字段 | **简化报告**（评分 + 建议 + 摘要） | 保留核心决策信息 |
| ✅ 配置管理 | .env 100+ 配置项 | **10 个核心配置项** | 只保留 API Key、股票列表等 |
| ✅ 数据持久化 | SQLAlchemy + 7 张表 | **SQLite + 1 张表**（分析结果） | 最小存储需求 |
| ⬜ 通知推送 | 11 个渠道 | **1 个渠道**（如终端打印或 Telegram） | 可选，但有最好 |
| ❌ Web UI | React 完整 SPA | 不需要 | MVP 先 CLI |
| ❌ Desktop App | Electron | 不需要 | MVP 先 CLI |
| ❌ Multi-Agent | 4 个专家 Agent | 不需要 | 直接 LLM 调用更简单 |
| ❌ Bot 接入 | 3 个平台 | 不需要 | MVP 后期可加 |
| ❌ 回测系统 | 历史验证 + 准确率 | 不需要 | 非核心功能 |
| ❌ Portfolio | 持仓管理 + 收益 | 不需要 | 非核心功能 |
| ❌ 新闻搜索 | 5 个搜索源 | 不需要 | LLM 自身知识先够用 |
| ❌ API Server | FastAPI REST API | 不需要 | MVP 先 CLI |
| ❌ 定时调度 | schedule 库 | 不需要 | crontab 替代 |
| ❌ Trading Skills | 11 个策略 | 不需要 | 后续增强 |

### 8.3 MVP 核心模块

```
mvp/
├── main.py                 # CLI 入口（~50 行）
├── config.py               # 简化配置（~30 行）
├── data_fetcher.py         # 单数据源行情获取（~80 行）
├── technical_analyzer.py   # 技术指标计算（~100 行）
├── llm_analyzer.py         # LLM 分析（~120 行）
├── report.py               # 报告生成（~60 行）
├── storage.py              # SQLite 持久化（~50 行）
├── .env.example            # 配置模板
└── requirements.txt        # 精简依赖
```

**预估总代码量：~500 行 Python**（对比完整版 ~10 万行）

### 8.4 MVP 核心配置

```env
# .env — MVP 最小配置
STOCK_LIST=600519,300750           # 自选股列表
LLM_API_KEY=sk-xxx                 # LLM API Key（DeepSeek/OpenAI）
LLM_BASE_URL=https://api.deepseek.com  # LLM API 地址
LLM_MODEL=deepseek-chat            # 模型名称
```

### 8.5 MVP 技术栈

| 类别 | 选型 | 理由 |
|------|------|------|
| 数据源 | akshare | 免费、无需注册、覆盖 A 股 |
| LLM | OpenAI SDK + DeepSeek | 成本低、中文好、兼容 OpenAI 协议 |
| 数据处理 | pandas | 行业标准 |
| 数据库 | SQLite（内置） | 零配置 |
| 配置 | python-dotenv | 简洁 |
| HTTP | requests | 简洁 |

### 8.6 MVP 精简依赖

```txt
# requirements.txt — MVP
akshare>=1.12.0
pandas>=2.0.0
openai>=1.0.0
python-dotenv>=1.0.0
```

---

## 9. MVP 实现路线图

### Phase 1：数据获取（Day 1）

```python
# data_fetcher.py — 核心逻辑
import akshare as ak

def get_stock_data(stock_code: str, days: int = 60) -> pd.DataFrame:
    """获取股票日 K 线数据"""
    df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq")
    return df.tail(days)

def get_realtime_quote(stock_code: str) -> dict:
    """获取实时行情"""
    df = ak.stock_zh_a_spot_em()
    row = df[df['代码'] == stock_code].iloc[0]
    return {"price": row['最新价'], "change_pct": row['涨跌幅']}
```

### Phase 2：技术分析（Day 1-2）

```python
# technical_analyzer.py — 核心逻辑
def analyze(df: pd.DataFrame) -> dict:
    """计算技术指标"""
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()

    latest = df.iloc[-1]
    trend = "多头排列" if latest['ma5'] > latest['ma10'] > latest['ma20'] else \
            "空头排列" if latest['ma5'] < latest['ma10'] < latest['ma20'] else "盘整"

    vol_avg = df['volume'].rolling(5).mean().iloc[-1]
    vol_status = "放量" if latest['volume'] > vol_avg * 1.3 else \
                 "缩量" if latest['volume'] < vol_avg * 0.7 else "正常"

    return {
        "trend": trend,
        "ma5": round(latest['ma5'], 2),
        "ma10": round(latest['ma10'], 2),
        "ma20": round(latest['ma20'], 2),
        "volume_status": vol_status,
        "price": latest['close'],
        "change_pct": round((latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100, 2)
    }
```

### Phase 3：LLM 分析（Day 2-3）

```python
# llm_analyzer.py — 核心逻辑
from openai import OpenAI

SYSTEM_PROMPT = """你是一位专业的股票分析师。请根据提供的技术指标数据，给出分析报告。

请以 JSON 格式输出，包含以下字段：
- sentiment_score: 综合评分(0-100)
- trend_prediction: 趋势预测(强烈看多/看多/震荡/看空/强烈看空)
- operation_advice: 操作建议(买入/持有/卖出/观望)
- analysis_summary: 综合分析(200字以内)
- risk_warning: 风险提示
"""

def analyze(stock_name: str, technical_data: dict) -> dict:
    client = OpenAI(api_key=config.llm_api_key, base_url=config.llm_base_url)
    
    user_message = f"""
    股票：{stock_name}
    当前价格：{technical_data['price']}
    涨跌幅：{technical_data['change_pct']}%
    趋势状态：{technical_data['trend']}
    MA5={technical_data['ma5']}, MA10={technical_data['ma10']}, MA20={technical_data['ma20']}
    量能状态：{technical_data['volume_status']}
    """
    
    response = client.chat.completions.create(
        model=config.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
```

### Phase 4：报告与持久化（Day 3）

```python
# report.py
def format_report(stock_name: str, analysis: dict) -> str:
    score = analysis['sentiment_score']
    emoji = "🟢" if score >= 60 else "🟡" if score >= 40 else "🔴"
    return f"""
# {emoji} {stock_name} 分析报告

**综合评分**: {score}/100 | **趋势**: {analysis['trend_prediction']} | **建议**: {analysis['operation_advice']}

## 分析摘要
{analysis['analysis_summary']}

## ⚠️ 风险提示
{analysis['risk_warning']}
"""
```

```python
# storage.py
import sqlite3

def save_analysis(stock_code, stock_name, analysis):
    conn = sqlite3.connect("data/analysis.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT, stock_name TEXT,
            sentiment_score INTEGER, trend_prediction TEXT,
            operation_advice TEXT, analysis_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("INSERT INTO analysis (...) VALUES (...)", (...))
    conn.commit()
```

### Phase 5：主程序集成（Day 3-4）

```python
# main.py — MVP 入口
import argparse
from config import load_config
from data_fetcher import get_stock_data
from technical_analyzer import analyze as tech_analyze
from llm_analyzer import analyze as llm_analyze
from report import format_report
from storage import save_analysis

def main():
    config = load_config()
    for stock_code in config.stock_list:
        print(f"正在分析 {stock_code}...")
        
        # 1. 获取数据
        df = get_stock_data(stock_code)
        
        # 2. 技术分析
        tech_result = tech_analyze(df)
        
        # 3. LLM 分析
        analysis = llm_analyze(stock_name, tech_result)
        
        # 4. 生成报告
        report = format_report(stock_name, analysis)
        print(report)
        
        # 5. 持久化
        save_analysis(stock_code, stock_name, analysis)

if __name__ == "__main__":
    main()
```

### 后续扩展路线

```
MVP (Phase 1-5)
 │
 ├── Phase 6: 新闻搜索集成（Tavily/Bocha）
 ├── Phase 7: 通知推送（Telegram/企业微信）
 ├── Phase 8: 定时调度
 ├── Phase 9: FastAPI 服务化
 ├── Phase 10: Web UI（React）
 ├── Phase 11: 多数据源 Fallback
 ├── Phase 12: Multi-Agent 系统
 └── Phase 13: 回测 + Portfolio
```

---

## 10. 参考文件索引

快速查阅完整版实现的关键文件：

| 功能 | 文件路径 | 说明 |
|------|---------|------|
| CLI 入口 | `main.py` | 参数解析与主流程调度 |
| API 入口 | `server.py` | FastAPI 应用入口 |
| 分析流水线 | `src/core/pipeline.py` | 核心编排逻辑（最重要的文件） |
| LLM 分析器 | `src/analyzer.py` | Prompt 工程与结构化输出 |
| 技术分析 | `src/stock_analyzer.py` | MA/MACD/RSI 指标计算 |
| 报告 Schema | `src/schemas/report_schema.py` | 决策仪表盘数据结构 |
| 数据源管理 | `data_provider/base.py` | Fetcher 接口与 Fallback 策略 |
| 配置系统 | `src/config.py` | 环境变量解析与校验 |
| 数据库模型 | `src/storage.py` | SQLAlchemy ORM 定义 |
| 通知中心 | `src/notification.py` | 多渠道分发逻辑 |
| 搜索聚合 | `src/search_service.py` | 新闻搜索引擎 |
| Agent 基类 | `src/agent/agents/base_agent.py` | Agent 抽象接口 |
| Agent 编排 | `src/agent/orchestrator.py` | Multi-Agent 协作逻辑 |
| API 端点 | `api/v1/endpoints/analysis.py` | 分析 API 实现 |
| 前端入口 | `apps/dsa-web/src/App.tsx` | React SPA 入口 |
| Docker | `docker/Dockerfile` | 多阶段构建配置 |
| 部署指南 | `docs/DEPLOY.md` | 完整部署文档 |
| 完整用户指南 | `docs/full-guide.md` | 49 KB 全功能说明 |

---

> **提示**：如果你打算从 MVP 开始复刻，建议重点阅读 `src/core/pipeline.py`（理解编排思路）、`src/analyzer.py`（理解 Prompt 设计）和 `src/stock_analyzer.py`（理解技术指标计算），这三个文件包含了系统最核心的业务逻辑。
