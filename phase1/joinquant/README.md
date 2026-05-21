# 聚宽 (JoinQuant) 平台学习指南

> https://www.joinquant.com

## 为什么用聚宽？

聚宽是中国最大的在线量化平台，优势：
- **零配置**：浏览器打开即用，无需安装任何东西
- **数据齐全**：A股全量日线/分钟线、财务报表、龙虎榜、行业分类
- **研究环境**：Jupyter Notebook 风格，适合探索性分析
- **模拟交易**：内置模拟交易，可做回测和模拟实盘
- **社区活跃**：策略分享、问答、克隆机制

## 快速上手步骤

### 1. 注册账号
访问 https://www.joinquant.com → 注册 → 登录

### 2. 了解三个核心模块

| 模块 | 用途 | 入口 |
|------|------|------|
| **研究** | 数据分析、因子研究、可视化 | 顶部导航 → 研究 |
| **回测** | 策略回测、绩效分析 | 顶部导航 → 回测 |
| **模拟交易** | 模拟实盘运行 | 顶部导航 → 模拟交易 |

### 3. 第一个研究 Notebook

在"研究"环境中新建Notebook，运行以下代码：

```python
# === 获取A股数据 ===
import pandas as pd
import numpy as np

# 获取沪深300成分股
hs300 = get_index_stocks('000300.XSHG')
print(f"沪深300成分股数量: {len(hs300)}")
print(f"前10只: {hs300[:10]}")

# 获取单只股票的日线数据
df = get_price('000300.XSHG', start_date='2023-01-01', end_date='2024-12-31',
               frequency='daily', fields=['open', 'close', 'high', 'low', 'volume'])
print(f"\n沪深300指数日线数据:")
df.head()
```

### 4. 聚宽核心 API 速查

```python
# ----- 数据获取 -----
# 股票列表
get_index_stocks('000300.XSHG')         # 沪深300
get_industry_stocks('801180')           # 行业成分股
get_all_securities(['stock'])           # 全市场股票

# 行情数据
get_price(security, start_date, end_date, frequency, fields)
# frequency: 'daily', 'minute', '5minute', '60minute'
# fields: ['open','close','high','low','volume','money','factor']

# 基本面数据
get_fundamentals(query(valuation.pe_ratio, valuation.market_cap)
                 .filter(valuation.market_cap > 100), date='2024-01-01')

# 财务数据
get_fundamentals(query(balance.cash_equivalents, income.net_profit)
                 .filter(income.net_profit > 0))

# ----- 回测 (在回测环境中) -----
def initialize(context):
    """初始化函数，回测开始时调用一次"""
    g.security = '000300.XSHG'
    set_benchmark('000300.XSHG')
    
def handle_data(context, data):
    """每个交易日调用一次"""
    # 交易逻辑
    pass

# ----- 下单函数 -----
order(security, amount)                 # 按股数
order_target(security, target_amount)   # 调整到目标股数
order_value(security, value)            # 按金额
order_target_value(security, value)     # 调整到目标市值
```

### 5. 第一个回测策略

```python
# 在"回测"模块中粘贴以下代码，设置时间范围 2019-01-01 ~ 2024-12-31

def initialize(context):
    g.stock = '000300.XSHG'
    g.fast = 10
    g.slow = 30
    set_benchmark(g.stock)
    set_option('use_real_price', True)
    log.info('策略初始化完成')

def handle_data(context, data):
    # 计算双均线
    prices = attribute_history(g.stock, g.slow+1, '1d', 'close')
    fast_ma = prices['close'][-g.fast:].mean()
    slow_ma = prices['close'][-g.slow:].mean()
    
    cash = context.portfolio.cash
    
    # 金叉买入
    if fast_ma > slow_ma and g.stock not in context.portfolio.positions:
        order_value(g.stock, cash * 0.8)
        log.info(f'金叉买入: {context.current_dt}')
    
    # 死叉卖出
    elif fast_ma < slow_ma and g.stock in context.portfolio.positions:
        order_target(g.stock, 0)
        log.info(f'死叉卖出: {context.current_dt}')
```

### 6. 聚宽 vs 本地环境

| 功能 | 聚宽 | 本地 (Backtrader/Alphalens) |
|------|------|---------|
| 上手速度 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 数据获取 | 平台提供，一键调用 | 需自建数据管道 |
| 回测速度 | 受平台限制 | 取决于本地硬件 |
| 策略保密 | 代码在云端 | 完全本地 |
| 实盘对接 | 需对接券商 | vnpy等直接支持 |
| 定制能力 | API固定 | 完全自由 |

### 学习建议

**第1周**：聚宽研究环境，熟悉数据API，做探索性分析
**第2周**：聚宽回测，写双均线/动量/均值回归策略
**第3周**：转向本地 Backtrader + Alphalens，理解引擎原理
**第4周+**：两者结合——聚宽做快速验证，本地做深度开发
