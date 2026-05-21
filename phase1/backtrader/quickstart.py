"""Backtrader 01 - 快速入门：最简单的回测

用随机生成数据跑通完整流程，不依赖任何外部数据源。

运行: uv run python phase1/backtrader/01_quickstart.py
"""

import backtrader as bt
import datetime
import random


class SmaCross(bt.Strategy):
    """经典双均线交叉策略"""
    params = (("fast", 10), ("slow", 30))

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position:  # 无持仓 → 金叉买入
            if self.crossover > 0:
                size = self.broker.getcash() / self.data.close[0]
                self.buy(size=size)
                print(f"  >>> BUY  {self.data.datetime.date()} @ {self.data.close[0]:.2f}")
        elif self.crossover < 0:  # 有持仓 → 死叉卖出
            self.close()
            print(f"  <<< SELL {self.data.datetime.date()} @ {self.data.close[0]:.2f}")


def generate_price_data(n=252, start_price=100):
    """生成一年(252个交易日)的模拟价格数据，返回 Backtrader PandasData"""
    import pandas as pd

    dates = []
    opens, highs, lows, closes, volumes = [], [], [], [], []

    price = start_price
    d = datetime.date(2024, 1, 1)
    while len(dates) < n:
        d = d + datetime.timedelta(days=1)
        if d.weekday() >= 5:
            continue
        dates.append(d)

        daily_return = random.gauss(0.0005, 0.015)
        price = price * (1 + daily_return)
        o = price * (1 + random.gauss(0, 0.005))
        h = max(o, price) * (1 + abs(random.gauss(0, 0.008)))
        l = min(o, price) * (1 - abs(random.gauss(0, 0.008)))
        v = random.randint(1_000_000, 10_000_000)

        opens.append(round(o, 2))
        highs.append(round(h, 2))
        lows.append(round(l, 2))
        closes.append(round(price, 2))
        volumes.append(v)

    df = pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes},
        index=pd.DatetimeIndex(dates),
    )
    return bt.feeds.PandasData(dataname=df)


if __name__ == "__main__":
    # 1. 生成模拟数据
    data = generate_price_data()

    # 2. 创建 Cerebro（回测引擎）
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000.0)

    # 3. 加载数据
    cerebro.adddata(data)

    # 4. 加入策略
    cerebro.addstrategy(SmaCross)

    # 5. 加入分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

    # 6. 运行
    print(f"初始资金: ¥{cerebro.broker.getvalue():,.0f}\n")
    results = cerebro.run()
    print(f"\n最终资金: ¥{cerebro.broker.getvalue():,.0f}")

    # 7. 分析结果
    strat = results[0]
    sharpe = strat.analyzers.sharpe.get_analysis()
    dd = strat.analyzers.drawdown.get_analysis()
    ret = strat.analyzers.returns.get_analysis()

    sharpe_ratio = sharpe.get("sharperatio")
    max_dd = (dd.get("max") or {}).get("drawdown", 0)
    total_ret = ret.get("rnorm100", 0)

    print(f"\n======== 回测结果 ========")
    if sharpe_ratio is not None:
        print(f"Sharpe Ratio : {sharpe_ratio:.2f}")
    else:
        print("Sharpe Ratio : N/A (数据不足)")
    print(f"最大回撤     : {max_dd:.2f}%")
    print(f"总收益率     : {total_ret:.2f}%")

    # 8. 画图
    cerebro.plot(style="candlestick", volume=False)
