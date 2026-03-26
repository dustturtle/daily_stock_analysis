# DSA MVP — 股票智能分析最小化版本

> Daily Stock Analysis 的最小可用产品，保留核心分析流程，~500 行 Python 代码。

## 功能

| 模块 | 功能 | 文件 |
|------|------|------|
| 配置管理 | 从 `.env` 读取配置 | `config.py` |
| 行情获取 | akshare A 股日 K 线 | `data_fetcher.py` |
| 技术分析 | MA5/MA10/MA20 + 量能 | `technical_analyzer.py` |
| LLM 分析 | OpenAI 协议兼容 API | `llm_analyzer.py` |
| 报告生成 | 终端打印 Markdown 报告 | `report.py` |
| 数据持久化 | SQLite 存储分析结果 | `storage.py` |
| CLI 入口 | 命令行主程序 | `main.py` |

## 快速开始

```bash
# 1. 安装依赖
pip install -r DSA_MVP/requirements.txt

# 2. 配置
cp DSA_MVP/.env.example .env
# 编辑 .env，填入 LLM_API_KEY 和 STOCK_LIST

# 3. 运行分析
python -m DSA_MVP --stocks 600519

# 4. dry-run 模式（跳过 LLM，仅技术分析）
python -m DSA_MVP --stocks 600519 --dry-run
```

## CLI 参数

```
--stocks STOCKS   要分析的股票代码，逗号分隔
--days DAYS       获取最近多少个交易日数据（默认 60）
--debug           启用 DEBUG 日志
--dry-run         跳过 LLM 调用
```

## 测试

```bash
pip install pytest
python -m pytest DSA_MVP/tests/ -v
```

## 配置项

| 配置 | 说明 | 默认值 |
|------|------|--------|
| `STOCK_LIST` | 自选股列表（逗号分隔） | 空 |
| `LLM_API_KEY` | LLM API Key | 空 |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | LLM 模型名称 | `deepseek-chat` |
| `DB_PATH` | SQLite 数据库路径 | `data/analysis.db` |

## 技术栈

- **数据源**: akshare（A 股行情）
- **LLM**: OpenAI SDK（兼容 DeepSeek/GPT 等）
- **数据处理**: pandas
- **数据库**: SQLite（零配置）
- **配置**: python-dotenv
