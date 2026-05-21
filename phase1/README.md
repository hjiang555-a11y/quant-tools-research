# 第一阶段：量化交易基础学习（0-3 个月）

> 目标：掌握回测框架、因子分析方法论，跑通从数据到策略评估的完整流程

## 环境信息

- Python: 3.14.4 (uv venv)
- 核心包: backtrader, alphalens-reloaded, pyfolio-reloaded, akshare, tushare, pandas, numpy, sklearn, jupyter
- 激活虚拟环境: `source .venv/bin/activate`
- 运行脚本: `uv run python <script>`

## 学习路线

```
第 1-2 周: 基础建设
├── 聚宽平台上手 ── 了解数据API、研究环境、回测API
├── 运行第一个本地回测 (quickstart.py)
└── 理解回测引擎核心概念: Cerebro, Strategy, Data Feed, Broker

第 3-4 周: 策略开发
├── 掌握 Backtrader 策略生命周期
├── 实现经典策略: 双均线交叉、动量、均值回归
├── 添加分析器: Sharpe, Drawdown, TradeAnalyzer
└── 自定义指标

第 5-6 周: 因子研究
├── 理解因子的本质: factor = signal = edge
├── Alphalens 因子分析流程
├── IC 分析 (Information Coefficient)
├── 分层回测 (Quantile Analysis)
└── 因子组合与行业中性

第 7-8 周: 进阶主题
├── 交易成本建模 (手续费 + 滑点)
├── 过拟合检测 (样本外测试、交叉验证)
├── 实盘对接基础 (vnpy 初步了解)
└── 第一个完整策略从研究到模拟交易
```

## 按周分解

### 第 1 周：环境与第一笔回测

| 天数 | 任务 | 文件/资源 |
|------|------|-----------|
| Day 1 | 注册聚宽，浏览研究环境 | [joinquant/README.md](joinquant/README.md) |
| Day 2 | 聚宽Notebook：获取数据、画K线图 | 聚宽研究环境 |
| Day 3 | 聚宽回测：最简单的双均线策略 | 聚宽回测模块 |
| Day 4 | 本地：运行 quickstart.py，理解输出 | `backtrader/quickstart.py` |
| Day 5 | 阅读 Backtrader 文档 Quickstart | https://www.backtrader.com/docu/quickstart/quickstart/ |

### 第 2 周：A股真实数据回测

| 天数 | 任务 | 文件/资源 |
|------|------|-----------|
| Day 1 | 学习 akshare 数据获取API | `backtrader/02_ashare_backtest.py` |
| Day 2 | 获取A股真实数据，运行双均线策略 | 同上 |
| Day 3 | 优化策略参数 (fast/slow period) | 修改脚本实验 |
| Day 4 | 添加止损、仓位管理 | `backtrader/02_ashare_backtest.py` |
| Day 5 | 分析回测报告，理解每个指标 | 总结笔记 |

### 第 3 周：自定义策略与指标

| 天数 | 任务 | 文件/资源 |
|------|------|-----------|
| Day 1 | 理解 Backtrader 的 Indicator 体系 | BT官方文档 |
| Day 2 | 实现自定义 RSI 指标 | `backtrader/03_advanced.py` |
| Day 3 | 实现 RSI+布林带组合策略 | 同上 |
| Day 4 | 多策略对比框架 | 同上 |
| Day 5 | 回测系统完整知识图谱 | 自己画图总结 |

### 第 4 周：因子分析入门

| 天数 | 任务 | 文件/资源 |
|------|------|-----------|
| Day 1 | 理解因子分析基本概念 | 阅读 Alphalens 文档 |
| Day 2 | 运行模拟因子分析 | `alphalens/01_factor_basics.py` |
| Day 3 | 解读 IC、分层回测、Turnover | 同上 |
| Day 4 | PE因子分析 | `alphalens/02_pe_factor.py` |
| Day 5 | 写第一个自己的因子并评估 | 自主练习 |

## 关键概念速查

### Backtrader 核心概念

```
Cerebro (大脑)
  ├── adddata()        加载数据源
  ├── addstrategy()    加入策略
  ├── addanalyzer()    加入分析器
  ├── broker           资金管理 (setcash, getvalue)
  └── run() / plot()   执行回测 / 画图

Strategy (策略生命周期)
  ├── __init__()       初始化指标 (整个回测只调用一次)
  ├── start()          回测开始前
  ├── next()           每个bar调用一次 (策略核心逻辑)
  └── stop()           回测结束后

Data Feed (数据源)
  ├── GenericCSVData   通用CSV
  ├── PandasData       Pandas DataFrame
  └── YahooFinanceData Yahoo格式

Analyzer (分析器)
  ├── SharpeRatio      夏普比率
  ├── DrawDown         最大回撤
  ├── AnnualReturn     年化收益
  ├── TradeAnalyzer    交易统计
  └── TimeReturn       时间序列收益
```

### Alphalens 核心概念

```
因子分析流程:
  1. 准备数据: factor values + prices
  2. get_clean_factor_and_forward_returns()
  3. IC 分析: 因子与未来收益的相关性
  4. 分层回测: 按因子值分组，看各组收益
  5. Turnover: 因子排序的稳定性

关键指标:
  - IC Mean: 因子与未来收益的平均相关系数 (>0.02 有意义)
  - IC IR: IC Mean / IC Std (>0.5 较好)
  - Quantile Spread: Q5-Q1 收益差（多空组合收益）
  - Factor Auto-correlation: 因子自相关（越高越稳定）
```

## 数据源

| 数据源 | 覆盖 | 获取方式 |
|--------|------|----------|
| **akshare** | A股全场、期货、基金、宏观经济 | `pip install akshare` |
| **tushare** | A股(需注册token)、港股、美股 | `pip install tushare` |
| **聚宽数据API** | A股全量(在线平台内) | `get_price()` 等 |
| **baostock** | A股历史数据(研究用途) | `pip install baostock` |

### akshare 常用函数

```python
import akshare as ak

# A股个股日线
ak.stock_zh_a_hist(symbol="600519", period="daily",
                   start_date="20230101", end_date="20241231", adjust="qfq")

# 指数日线
ak.stock_zh_index_daily(symbol="sh000300")

# 沪深300成分股
ak.index_stock_cons_csindex("000300")

# 行业板块
ak.stock_board_industry_name_em()

# 龙虎榜
ak.stock_sina_lhb_detail_daily(trade_date="20240501")
```

## 检验标准

完成第一阶段后，你应该能回答这些问题：

1. [ ] Backtrader 的 Cerebro、Strategy、Data Feed 各自负责什么？
2. [ ] `__init__` vs `next` 在策略中的执行时机有何不同？
3. [ ] 如何给回测添加交易成本和滑点？
4. [ ] Sharpe Ratio 和最大回撤分别衡量什么？
5. [ ] IC 是什么？正的 IC 和负的 IC 分别意味着什么？
6. [ ] Alphalens 的分层回测是怎么做的？
7. [ ] 为什么样本外测试比样本内更重要？
8. [ ] 如何从聚宽导出数据到本地分析？

## 下一步

完成第一阶段后 → 进入**第二阶段（策略开发 3-6 个月）**：
- Microsoft Qlib — AI量化研究
- QuantConnect — 跨市场回测
- 自建数据管道
- vnpy 实盘基础

## 参考

- Backtrader 官方文档: https://www.backtrader.com/docu/
- Alphalens 文档: https://github.com/stefan-jansen/alphalens-reloaded
- 聚宽API文档: https://www.joinquant.com/help/api/help
- akshare 文档: https://akshare.akfamily.xyz/
