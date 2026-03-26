# A 股数据源参考文档

> 本文档整理自 [daily_stock_analysis](https://github.com/dustturtle/daily_stock_analysis) 项目实际使用的全部 A 股数据源，供其他项目参考。

---

## 目录

- [数据源总览](#数据源总览)
- [1. efinance（东方财富）](#1-efinance东方财富)
- [2. akshare（多源聚合）](#2-akshare多源聚合)
- [3. Tushare Pro（挖地兔）](#3-tushare-pro挖地兔)
- [4. pytdx（通达信）](#4-pytdx通达信)
- [5. baostock（证券宝）](#5-baostock证券宝)
- [6. yfinance（Yahoo Finance）](#6-yfinanceyahoo-finance)
- [7. TickFlow（市场大盘专用）](#7-tickflow市场大盘专用)
- [8. 新浪/腾讯实时行情（直接 HTTP）](#8-新浪腾讯实时行情直接-http)
- [数据能力对比矩阵](#数据能力对比矩阵)
- [实时行情数据源](#实时行情数据源)
- [优先级与 Failover 机制](#优先级与-failover-机制)
- [反爬与稳定性策略](#反爬与稳定性策略)
- [数据标准化](#数据标准化)
- [安装依赖](#安装依赖)
- [环境变量配置](#环境变量配置)

---

## 数据源总览

| 数据源 | 默认优先级 | 底层来源 | 是否免费 | 需要 Token | 适合场景 |
|--------|-----------|---------|---------|-----------|---------|
| **efinance** | 0（最高） | 东方财富 | ✅ 免费 | ❌ | K 线、实时行情、批量拉取 |
| **akshare** | 1 | 东方财富 / 新浪 / 腾讯 | ✅ 免费 | ❌ | K 线、实时行情、筹码分布 |
| **Tushare Pro** | 2（有 Token 时升至 -1） | Tushare 官方 | 部分免费 | ✅ 需注册 | K 线、实时行情（专业级） |
| **pytdx** | 2 | 通达信行情服务器 | ✅ 免费 | ❌ | K 线（直连行情服务器） |
| **baostock** | 3 | 证券宝 | ✅ 免费 | ❌ | K 线（稳定兜底） |
| **yfinance** | 4（最低） | Yahoo Finance | ✅ 免费 | ❌ | 美股/港股为主，A 股兜底 |
| **TickFlow** | 99（特殊用途） | TickFlow API | ✅ 免费 | ⭕ 可选 | 大盘指数、涨跌统计 |

---

## 1. efinance（东方财富）

### 基本信息

| 项目 | 说明 |
|------|------|
| **库名** | `efinance` |
| **版本要求** | >= 0.5.5 |
| **底层数据源** | 东方财富（Eastmoney） |
| **官方仓库** | <https://github.com/Micro-sheep/efinance> |
| **费用** | 免费，无需 Token |
| **覆盖市场** | A 股、ETF |

### 提供的数据

- **日 K 线数据**：开盘价、最高价、最低价、收盘价、成交量、成交额、涨跌幅
- **实时行情**：最新价、涨跌幅、涨跌额、成交量、成交额、换手率、振幅、最高/最低/开盘价
- **ETF 数据**
- **股票代码列表 & 名称**

### 使用方法

```python
import efinance

# 获取日 K 线
df = efinance.stock.get_quote_history('600519')  # 贵州茅台
# 返回: 日期、开盘、收盘、最高、最低、成交量、成交额、涨跌幅 等

# 获取实时行情（全市场批量拉取）
quotes = efinance.stock.get_realtime_quotes()
# 返回: 全部 A 股（约 5000+）的实时行情
```

### 特点与注意事项

- **批量接口**：调用 `get_realtime_quotes()` 一次拉取全市场约 5000+ 只股票，效率高
- **需要东方财富认证补丁**：长时间使用可能触发反爬，建议配合 NID Token 认证（项目已内置 `eastmoney_patch`）
- **反爬策略**：建议请求间隔 1.5–3.0 秒
- **超时设置**：通过 `EFINANCE_CALL_TIMEOUT` 环境变量控制（默认 30 秒）
- **缓存**：实时行情全量拉取后缓存 20 分钟

### 环境变量

```bash
EFINANCE_PRIORITY=0          # 优先级（默认 0，最高）
EFINANCE_CALL_TIMEOUT=30     # 超时时间（秒）
ENABLE_EASTMONEY_PATCH=true  # 启用东方财富认证补丁
```

---

## 2. akshare（多源聚合）

### 基本信息

| 项目 | 说明 |
|------|------|
| **库名** | `akshare` |
| **版本要求** | >= 1.12.0 |
| **底层数据源** | 东方财富、新浪财经、腾讯财经 |
| **官方文档** | <https://akshare.akfamily.xyz/> |
| **费用** | 免费，无需 Token |
| **覆盖市场** | A 股、港股、美股 |

### 提供的数据

- **日 K 线数据**：开盘价、最高价、最低价、收盘价、成交量、成交额、涨跌幅
- **实时行情**：支持三个底层源（东方财富 / 新浪 / 腾讯）
- **增强数据**：量比、换手率、市盈率 (PE)、市净率 (PB)、总市值、流通市值
- **筹码分布**：获利比例、平均成本
- **股票列表 & 名称**

### 使用方法

```python
import akshare as ak

# 获取日 K 线（东方财富源）
df = ak.stock_zh_a_daily(symbol='600519', adjust='qfq')
# 返回: 日期、开盘、最高、最低、收盘、成交量

# 获取实时行情 - 东方财富源（全量拉取）
spot_df = ak.stock_zh_a_spot_em()
# 返回: 全部 A 股实时行情（约 5000+ 只）

# 获取 A 股列表
stock_list = ak.stock_zh_a_spot_em()[['代码', '名称']]
```

### 多源内部 Failover

akshare 在本项目中配置了内部多源切换：

1. **东方财富 (em)**：默认首选，全量拉取效率最高
2. **新浪财经 (sina)**：单只查询，稳定备用
3. **腾讯财经 (tencent)**：单只查询，额外备用

### 特点与注意事项

- **多数据源聚合**：一个库覆盖三大行情源
- **全量拉取**：东财源 `ak.stock_zh_a_spot_em()` 可一次获取全市场
- **筹码分布**：独有的 `get_chip_distribution()` 能力
- **反爬限制较重**：东财源容易被封，建议请求间隔 2–5 秒 + UA 轮换
- **UA 轮换**：内置 5 个预设 User-Agent 随机切换
- **重试机制**：使用 tenacity 库，3 次重试 + 指数退避

### 环境变量

```bash
AKSHARE_PRIORITY=1       # 优先级（默认 1）
AKSHARE_SLEEP_MIN=2.0    # 最小请求间隔（秒）
AKSHARE_SLEEP_MAX=5.0    # 最大请求间隔（秒）
```

---

## 3. Tushare Pro（挖地兔）

### 基本信息

| 项目 | 说明 |
|------|------|
| **库名** | `tushare` |
| **版本要求** | >= 1.4.0 |
| **底层数据源** | Tushare Pro 官方 API |
| **官网** | <https://tushare.pro> |
| **费用** | 基础免费，高级接口需积分（2000+ 积分解锁实时行情） |
| **覆盖市场** | A 股、港股、基金、期货 |

### 提供的数据

- **日 K 线数据**：完整 OHLCV + 涨跌幅 + 涨跌额
- **实时行情**（Pro 接口需 2000+ 积分，旧接口无需）
- **ETF 数据**
- **基本面数据**：市盈率、市净率等
- **交易日历**
- **股票基本信息**

### 使用方法

```python
import tushare as ts

# 设置 Token
ts.set_token('你的Token')
pro = ts.pro_api()

# 获取日 K 线
df = pro.daily(ts_code='600519.SH', start_date='20240101', end_date='20240301')
# 返回: trade_date, open, high, low, close, vol, amount, pct_chg 等

# 获取实时行情（旧 API）
df = ts.get_realtime_quotes('600519')

# 获取实时行情（Pro API，需 2000+ 积分）
df = pro.quotation(ts_code='600519.SH')

# 获取 A 股列表
stock_list = pro.stock_basic(exchange='', list_status='L')

# 获取交易日历
cal = pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20241231')
```

### 特点与注意事项

- **专业级数据**：数据质量和覆盖面最全
- **需要注册**：在 <https://tushare.pro> 注册获取 Token
- **频率限制**：免费层 80 次/分钟、500 次/天
- **代码格式特殊**：使用 `600519.SH` 格式（后缀为 `.SH` / `.SZ`）
- **API 端点注意**：SDK 默认的 `api.waditu.com` 可能 503，建议 patch 到 `api.tushare.pro`（本项目已内置）
- **动态优先级**：配置了 Token 后，优先级自动提升至 -1（最高）

### 环境变量

```bash
TUSHARE_TOKEN=xxx                    # 必须：Tushare Pro Token
TUSHARE_PRIORITY=2                   # 优先级（有 Token 时自动升至 -1）
TUSHARE_RATE_LIMIT_PER_MINUTE=80     # 频率限制（次/分钟）
```

---

## 4. pytdx（通达信）

### 基本信息

| 项目 | 说明 |
|------|------|
| **库名** | `pytdx` |
| **版本要求** | >= 1.72 |
| **底层数据源** | 通达信行情服务器（TCP 直连） |
| **费用** | 免费，无需 Token |
| **覆盖市场** | A 股 |

### 提供的数据

- **日 K 线数据**：开盘价、最高价、最低价、收盘价、成交量、成交额
- **股票代码列表 & 名称**

### 使用方法

```python
from pytdx.hq import TdxHq_API

api = TdxHq_API()

# 连接通达信服务器
with api.connect('119.147.212.81', 7709):
    # 获取日 K 线（最近 100 天）
    # market: 0=深圳, 1=上海
    data = api.get_security_bars(
        category=9,    # 9=日K线
        market=1,      # 1=上海
        code='600519', # 股票代码
        start=0,       # 起始位置
        count=100      # 获取条数
    )
    
    # 获取股票列表
    stocks = api.get_security_list(market=1, start=0)
```

### 内置行情服务器

本项目预置了 8 个通达信行情服务器地址（深圳、上海、广州、武汉、杭州），自动切换：

```python
DEFAULT_SERVERS = [
    ('119.147.212.81', 7709),   # 深圳
    ('112.74.214.43', 7727),    # 深圳
    ('221.231.141.60', 7709),   # 上海
    ('101.227.73.20', 7709),    # 上海
    ('114.80.63.12', 7709),     # 上海
    ('218.75.126.9', 7709),     # 杭州
    ('119.97.185.5', 7709),     # 武汉
    ('59.36.6.3', 7709),        # 广州
]
```

### 特点与注意事项

- **TCP 直连**：不走 HTTP，直接连接通达信行情服务器，绕过 Web 反爬
- **无频率限制**：没有 API 配额限制
- **稳定可靠**：比 Web API 更稳定
- **数据有限**：仅提供基础 OHLCV，无市盈率、换手率等增强指标
- **市场代码**：0 = 深圳，1 = 上海
- **自动重连**：内置多服务器 failover

### 环境变量

```bash
PYTDX_PRIORITY=2                  # 优先级（默认 2）
PYTDX_SERVERS=ip:port,ip:port     # 自定义服务器列表
PYTDX_HOST=119.147.212.81         # 指定单个服务器 IP
PYTDX_PORT=7709                   # 指定单个服务器端口
```

---

## 5. baostock（证券宝）

### 基本信息

| 项目 | 说明 |
|------|------|
| **库名** | `baostock` |
| **版本要求** | >= 0.8.0 |
| **官网** | <http://baostock.com> |
| **费用** | 免费，无需 Token |
| **覆盖市场** | A 股 |

### 提供的数据

- **日 K 线数据**：开盘价、最高价、最低价、收盘价、成交量、成交额、涨跌幅
- **股票基本信息 & 名称**
- **股票列表**

### 使用方法

```python
import baostock as bs

# 必须先登录
lg = bs.login()

# 获取日 K 线（前复权）
rs = bs.query_history_k_data_plus(
    code='sh.600519',                 # 注意代码格式: sh./sz. 前缀
    fields='date,open,high,low,close,volume,amount,pctChg',
    start_date='2024-01-01',
    end_date='2024-03-01',
    frequency='d',                     # d=日, w=周, m=月
    adjustflag='2'                     # 1=后复权, 2=前复权, 3=不复权
)

# 解析结果
data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())
df = pd.DataFrame(data_list, columns=rs.fields)

# 获取股票基本信息
rs = bs.query_stock_basic(code='sh.600519')

# 必须登出
bs.logout()
```

### 特点与注意事项

- **需要 login/logout**：每次使用前 `bs.login()`，使用后 `bs.logout()`（建议使用上下文管理器）
- **完全免费**：无 Token、无频率限制、无配额
- **非常稳定**：不容易被封禁
- **数据有 T+1 延迟**：当天数据需要下一个交易日才能获取
- **代码格式**：使用 `sh.600519` / `sz.000001` 格式（带 `sh.` / `sz.` 前缀）
- **仅支持 A 股**：不支持港股、美股
- **数据范围有限**：仅基础 OHLCV，无增强指标

### 环境变量

```bash
BAOSTOCK_PRIORITY=3    # 优先级（默认 3）
```

---

## 6. yfinance（Yahoo Finance）

### 基本信息

| 项目 | 说明 |
|------|------|
| **库名** | `yfinance` |
| **版本要求** | >= 0.2.0 |
| **底层数据源** | Yahoo Finance |
| **费用** | 免费，无需 Token |
| **覆盖市场** | 全球（美股为主，兼容 A 股和港股） |

### 提供的数据

- **日 K 线数据**：开盘价、最高价、最低价、收盘价、成交量
- **实时行情**
- **股票名称**

### A 股代码映射

Yahoo Finance 使用特殊的代码格式：

| 交易所 | 代码前缀 | Yahoo 格式 | 示例 |
|--------|---------|-----------|------|
| 上海证券交易所 | 60xxxx, 5xxxx, 90xxxx | `{code}.SS` | `600519.SS` |
| 深圳证券交易所 | 00xxxx, 02xxxx, 30xxxx | `{code}.SZ` | `000001.SZ` |

### 使用方法

```python
import yfinance as yf

# 获取日 K 线（A 股）
ticker = yf.Ticker('600519.SS')   # 贵州茅台
df = ticker.history(period='3mo')  # 最近 3 个月
# 返回: Open, High, Low, Close, Volume

# 或使用 download 方法（支持多只股票）
df = yf.download('600519.SS 000001.SZ', start='2024-01-01', end='2024-03-01')

# 获取美股
df = yf.download('AAPL', period='1y')
```

### 特点与注意事项

- **兜底数据源**：仅在所有国内数据源均失败时使用
- **A 股数据延迟**：可能有 15–20 分钟延迟
- **A 股覆盖不全**：部分小票可能缺失数据
- **主要优势在美股/港股**：国际市场数据更全面
- **无频率限制**：但请求过于频繁可能被临时封禁

### 环境变量

```bash
YFINANCE_PRIORITY=4    # 优先级（默认 4，最低）
```

---

## 7. TickFlow（市场大盘专用）

### 基本信息

| 项目 | 说明 |
|------|------|
| **库名** | `tickflow` |
| **版本要求** | >= 0.1.0 |
| **费用** | 免费，API Key 可选 |
| **用途** | 仅用于大盘综述，不参与个股分析 |

### 提供的数据

- **A 股主要指数行情**：上证指数、深证成指、创业板指、科创 50、上证 50、沪深 300
- **市场涨跌统计**：上涨/下跌家数

### 覆盖指数

| 指数代码 | 名称 |
|---------|------|
| 000001 | 上证指数 |
| 399001 | 深证成指 |
| 399006 | 创业板指 |
| 000688 | 科创 50 |
| 000016 | 上证 50 |
| 000300 | 沪深 300 |

### 特点与注意事项

- **不用于个股分析**：仅在市场综述（market review）场景下使用
- **独立于主数据流**：优先级 99，不参与常规 failover 链
- **API Key 可选**：不配置也可使用基本功能

### 环境变量

```bash
TICKFLOW_API_KEY=xxx      # 可选：TickFlow API Key
TICKFLOW_TIMEOUT=30       # 超时时间（秒）
```

---

## 8. 新浪/腾讯实时行情（直接 HTTP）

除了通过 akshare 库间接调用，项目还直接通过 HTTP 请求获取新浪和腾讯的实时行情：

### 新浪财经

```
GET http://hq.sinajs.cn/list=sh600519,sz000001,...
```

- **响应格式**：JavaScript 变量赋值格式
- **返回字段**：股票名称、开盘价、昨收、当前价、最高、最低、买入价、卖出价、成交量、成交额、买一到买五、卖一到卖五等
- **特点**：单只查询，响应快速，适合少量股票实时行情
- **频率限制**：无明确限制，但大量请求可能被封

```
响应示例:
var hq_str_sh600519="贵州茅台,1849.00,1853.00,1860.01,...";
```

### 腾讯财经

```
GET http://qt.gtimg.cn/q=sh600519,sz000001,...
```

- **响应格式**：管道符（`~`）分隔
- **返回字段**：股票代码、名称、当前价、涨跌、涨跌幅、成交量、成交额等
- **特点**：单只查询，稳定性好，适合实时行情补充
- **频率限制**：无明确限制

```
响应示例:
v_sh600519="1~贵州茅台~600519~1860.01~1853.00~1849.00~...~";
```

### 使用方法（直接 HTTP）

```python
import requests

# 新浪行情
url = 'http://hq.sinajs.cn/list=sh600519'
headers = {'Referer': 'http://finance.sina.com.cn'}
resp = requests.get(url, headers=headers)
# 解析 JavaScript 响应

# 腾讯行情
url = 'http://qt.gtimg.cn/q=sh600519'
resp = requests.get(url)
# 按 ~ 分隔解析
```

---

## 数据能力对比矩阵

| 能力 | efinance | akshare | Tushare | pytdx | baostock | yfinance |
|------|----------|---------|---------|-------|----------|----------|
| **日 K 线** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **实时行情** | ✅ | ✅ | ✅（需积分） | ❌ | ❌ | ✅ |
| **市盈率/市净率** | ✅ | ✅ | ✅（需积分） | ❌ | ❌ | ❌ |
| **换手率** | ✅ | ✅ | ✅（需积分） | ❌ | ❌ | ❌ |
| **筹码分布** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **股票名称** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **股票列表** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **ETF 数据** | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **交易日历** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **批量拉取** | ✅（全量） | ✅（全量） | ❌（逐只） | ❌（逐只） | ❌（逐只） | ❌（逐只） |
| **港股支持** | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **美股支持** | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |

---

## 实时行情数据源

实时行情有独立的优先级配置，不同于 K 线数据的 Failover 顺序：

### 可选数据源

| 标识 | 底层来源 | 特点 |
|------|---------|------|
| `tushare` | Tushare Pro API | 专业级，需 Token 和积分 |
| `efinance` | 东方财富 | 全量拉取，缓存 20 分钟 |
| `akshare_em` | 东方财富（via akshare） | 全量拉取，速度最快 |
| `akshare_sina` | 新浪财经（via akshare） | 单只查询，稳定 |
| `tencent` | 腾讯财经（via akshare） | 单只查询，可靠 |

### 配置方式

```bash
# 自定义优先级（逗号分隔，从左到右依次尝试）
REALTIME_SOURCE_PRIORITY=tencent,akshare_sina,efinance,akshare_em

# 开关
ENABLE_REALTIME_QUOTE=true

# 预拉取（批量任务时，提前拉取全市场行情缓存）
PREFETCH_REALTIME_QUOTES=true
```

### 工作机制

1. 按配置的优先级顺序依次尝试各数据源
2. 第一个成功返回的作为「主源」
3. 如果主源缺少某些字段（如换手率），会继续从后续源补充
4. 所有源均失败时优雅降级（返回空值，不中断流程）

---

## 优先级与 Failover 机制

### K 线数据获取顺序

```
默认顺序（无 Tushare Token）:

  ① EfinanceFetcher   (Priority 0)
  ② AkshareFetcher    (Priority 1)
  ③ PytdxFetcher      (Priority 2)
  ④ TushareFetcher    (Priority 2, disabled without token)
  ⑤ BaostockFetcher   (Priority 3)
  ⑥ YfinanceFetcher   (Priority 4)

配置 Tushare Token 后:

  ① TushareFetcher    (Priority -1, auto-elevated)
  ② EfinanceFetcher   (Priority 0)
  ③ AkshareFetcher    (Priority 1)
  ④ PytdxFetcher      (Priority 2)
  ⑤ BaostockFetcher   (Priority 3)
  ⑥ YfinanceFetcher   (Priority 4)
```

### Failover 逻辑

1. 从最高优先级开始尝试
2. 当前数据源抛出异常 → 记录错误日志 → 自动切换到下一个
3. 所有数据源均失败 → 抛出 `DataFetchError`（包含完整错误链）
4. 美股代码自动路由到 YfinanceFetcher（跳过国内数据源）

### 优先级可通过环境变量覆盖

```bash
EFINANCE_PRIORITY=0
AKSHARE_PRIORITY=1
TUSHARE_PRIORITY=2
PYTDX_PRIORITY=2
BAOSTOCK_PRIORITY=3
YFINANCE_PRIORITY=4
```

---

## 反爬与稳定性策略

本项目在数据获取层面实现了多层防护策略：

### 1. 请求间隔（Jitter）

| 数据源 | 间隔范围 |
|--------|---------|
| efinance | 1.5–3.0 秒 |
| akshare | 2.0–5.0 秒（可配置） |
| 其他 | 1.0–3.0 秒 |

### 2. User-Agent 轮换

akshare 和 efinance 数据源内置 5 个预设 User-Agent，每次请求随机选择。

### 3. 东方财富 NID 认证补丁（eastmoney_patch）

针对东方财富系 API（efinance、akshare 的东财源）的反爬机制：

- 自动从 `https://anonflow2.eastmoney.com/backend/api/webreport` 获取 NID Token
- 生成伪装设备指纹（UUID、Canvas Key、WebGL Key 等）
- NID Token 缓存 20 秒，失败后冷却 5 分钟
- 仅拦截东方财富域名（`fund.eastmoney.com`、`push2.eastmoney.com`、`push2his.eastmoney.com`）

### 4. 重试机制

- 使用 `tenacity` 库实现指数退避重试（默认 3 次，间隔 1–30 秒）
- 每个数据源独立的断路器（Circuit Breaker）
- Tushare 内置分钟级频率追踪（80 次/分钟）

### 5. 缓存策略

| 缓存项 | TTL |
|--------|-----|
| NID Token | 20 秒 |
| 实时行情全量数据 | 20 分钟 |
| 基本面数据 | 可配 `FUNDAMENTAL_CACHE_TTL_SECONDS`（默认 120 秒） |

---

## 数据标准化

所有数据源返回的数据都会统一标准化为以下格式：

### 标准列名

```python
['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']
```

| 列名 | 说明 | 数据类型 |
|------|------|---------|
| `date` | 日期 | datetime |
| `open` | 开盘价 | float |
| `high` | 最高价 | float |
| `low` | 最低价 | float |
| `close` | 收盘价 | float |
| `volume` | 成交量 | float |
| `amount` | 成交额 | float |
| `pct_chg` | 涨跌幅（%） | float |

### 自动计算的技术指标

```python
['ma5', 'ma10', 'ma20', 'volume_ratio']
```

| 指标 | 说明 |
|------|------|
| `ma5` | 5 日均线 |
| `ma10` | 10 日均线 |
| `ma20` | 20 日均线 |
| `volume_ratio` | 量比（当日成交量 / 前 5 日均量） |

### 股票代码标准化

```python
# 输入 → 标准化输出
'SH600519'   → '600519'    # 去掉交易所前缀
'600519.SH'  → '600519'    # 去掉交易所后缀
'sh.600519'  → '600519'    # baostock 格式
'HK00700'    → 'HK00700'   # 港股保留 HK 前缀
'AAPL'       → 'AAPL'      # 美股保持不变
```

---

## 安装依赖

```bash
# 核心数据源
pip install efinance>=0.5.5       # 东方财富
pip install akshare>=1.12.0       # 多源聚合
pip install tushare>=1.4.0        # Tushare Pro
pip install pytdx>=1.72           # 通达信
pip install baostock>=0.8.0       # 证券宝
pip install yfinance>=0.2.0       # Yahoo Finance

# 可选
pip install tickflow>=0.1.0       # TickFlow（大盘专用）

# 辅助库
pip install tenacity>=8.2.0       # 重试机制
pip install pandas>=2.0.0         # 数据处理
pip install fake-useragent>=1.4.0 # UA 轮换
pip install exchange-calendars>=4.5.0  # 交易日历

# 一键安装（本项目）
pip install -r requirements.txt
```

---

## 环境变量配置

完整的数据源相关环境变量清单：

```bash
# ====== 数据源 Token ======
TUSHARE_TOKEN=                          # Tushare Pro Token（注册: https://tushare.pro）
TICKFLOW_API_KEY=                       # TickFlow API Key（可选）

# ====== 优先级配置 ======
EFINANCE_PRIORITY=0                     # efinance 优先级
AKSHARE_PRIORITY=1                      # akshare 优先级
TUSHARE_PRIORITY=2                      # tushare 优先级（有 Token 时自动升至 -1）
PYTDX_PRIORITY=2                        # pytdx 优先级
BAOSTOCK_PRIORITY=3                     # baostock 优先级
YFINANCE_PRIORITY=4                     # yfinance 优先级

# ====== 反爬与性能 ======
AKSHARE_SLEEP_MIN=2.0                   # akshare 最小请求间隔（秒）
AKSHARE_SLEEP_MAX=5.0                   # akshare 最大请求间隔（秒）
EFINANCE_CALL_TIMEOUT=30                # efinance 超时时间（秒）
TUSHARE_RATE_LIMIT_PER_MINUTE=80        # tushare 频率限制
TICKFLOW_TIMEOUT=30                     # tickflow 超时时间（秒）
ENABLE_EASTMONEY_PATCH=false            # 东方财富认证补丁（RemoteDisconnected 时启用）

# ====== 通达信服务器 ======
PYTDX_SERVERS=                          # 自定义服务器列表（ip:port,ip:port）
PYTDX_HOST=                             # 单个服务器 IP
PYTDX_PORT=                             # 单个服务器端口

# ====== 实时行情 ======
REALTIME_SOURCE_PRIORITY=tencent,akshare_sina,efinance,akshare_em
ENABLE_REALTIME_QUOTE=true              # 启用实时行情
PREFETCH_REALTIME_QUOTES=true           # 预拉取全市场行情
ENABLE_REALTIME_TECHNICAL_INDICATORS=true  # 用盘中价计算均线

# ====== 基本面数据 ======
ENABLE_FUNDAMENTAL_PIPELINE=true        # 启用基本面数据聚合
ENABLE_CHIP_DISTRIBUTION=true           # 启用筹码分布
FUNDAMENTAL_STAGE_TIMEOUT_SECONDS=1.5   # 阶段超时
FUNDAMENTAL_FETCH_TIMEOUT_SECONDS=0.8   # 拉取超时
FUNDAMENTAL_RETRY_MAX=1                 # 最大重试次数
FUNDAMENTAL_CACHE_TTL_SECONDS=120       # 缓存 TTL
FUNDAMENTAL_CACHE_MAX_ENTRIES=256       # 缓存最大条目

# ====== 交易日 ======
TRADING_DAY_CHECK_ENABLED=true          # 非交易日跳过执行
```

---

## 推荐使用方案

### 场景一：个人项目、快速原型

推荐使用 **akshare** 或 **efinance**，免费无门槛，数据全面。

```python
import akshare as ak

# 日 K 线
df = ak.stock_zh_a_daily(symbol='600519', adjust='qfq')

# 实时行情
quotes = ak.stock_zh_a_spot_em()
```

### 场景二：需要高质量/专业数据

推荐使用 **Tushare Pro**，注册后获取 Token。

```python
import tushare as ts
ts.set_token('your_token')
pro = ts.pro_api()
df = pro.daily(ts_code='600519.SH', start_date='20240101')
```

### 场景三：需要极致稳定性

推荐使用 **pytdx**（直连通达信服务器）或 **baostock**（完全免费无限制）。

### 场景四：生产环境、多源容灾

参考本项目的 `DataFetcherManager` 模式，配置多数据源 + 自动 failover：

```python
from data_provider import DataFetcherManager

manager = DataFetcherManager()
df, source_name = manager.get_daily_data('600519')
print(f"数据来自: {source_name}")
```

---

> **文档版本**：基于 daily_stock_analysis 项目截至 2026-03 的实际代码整理  
> **项目地址**：<https://github.com/dustturtle/daily_stock_analysis>
