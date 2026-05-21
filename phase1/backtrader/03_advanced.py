"""Backtrader 03 - 高级特性：自定义指标、分析器、多策略比较

运行: uv run python phase1/backtrader/03_advanced.py
"""

import backtrader as bt
import numpy as np
import random
import datetime


# ============================================================
# 自定义指标：RSI
# ============================================================
class RSI(bt.Indicator):
    """从零实现 RSI 指标"""
    lines = ("rsi",)
    params = (("period", 14),)

    def __init__(self):
        delta = self.data.close - self.data.close(-1)
        gain = bt.If(delta > 0, delta, 0)
        loss = bt.If(delta < 0, -delta, 0)
        avg_gain = bt.indicators.EMA(gain, period=self.params.period)
        avg_loss = bt.indicators.EMA(loss, period=self.params.period)
        rs = avg_gain / avg_loss
        self.lines.rsi = 100.0 - 100.0 / (1.0 + rs)


# ============================================================
# 策略：RSI + 布林带组合
# ============================================================
class RsiBollingerStrategy(bt.Strategy):
    params = (
        ("rsi_period", 14),
        ("bb_period", 20),
        ("bb_dev", 2.0),
        ("rsi_oversold", 30),
        ("rsi_overbought", 70),
    )

    def __init__(self):
        self.rsi = RSI(self.data.close, period=self.params.rsi_period)
        self.bb = bt.indicators.BollingerBands(
            self.data.close, period=self.params.bb_period, devfactor=self.params.bb_dev
        )
        # 记录每日信号值用于事后分析
        self.signal_log = []

    def next(self):
        signal = 0  # 0=无信号, 1=买入, -1=卖出
        if self.rsi < self.params.rsi_oversold and self.data.close < self.bb.lines.bot:
            signal = 1
        elif self.rsi > self.params.rsi_overbought and self.data.close > self.bb.lines.top:
            signal = -1

        self.signal_log.append((self.data.datetime.date(), float(self.rsi[0]), signal))

        if not self.position and signal == 1:
            self.buy()
        elif self.position and signal == -1:
            self.close()


# ============================================================
# 策略比较器：同时运行多条策略
# ============================================================
def generate_price_data(n=252, start_price=100):
    """生成模拟价格数据"""
    import random as _r
    dates = []
    opens, highs, lows, closes, volumes = [], [], [], [], []
    price = start_price
    d = datetime.date(2024, 1, 1)
    while len(dates) < n:
        d = d + datetime.timedelta(days=1)
        if d.weekday() >= 5:
            continue
        dates.append(d)
        ret = _r.gauss(0.0005, 0.015)
        price = price * (1 + ret)
        o = price * (1 + _r.gauss(0, 0.005))
        h = max(o, price) * (1 + abs(_r.gauss(0, 0.008)))
        l_ = min(o, price) * (1 - abs(_r.gauss(0, 0.008)))
        v = _r.randint(1_000_000, 10_000_000)
        opens.append(round(o, 2)); highs.append(round(h, 2))
        lows.append(round(l_, 2)); closes.append(round(price, 2))
        volumes.append(v)
    return dates, opens, highs, lows, closes, volumes


class PandasDataFeed(bt.feeds.PandasData):
    pass


if __name__ == "__main__":
    import pandas as _pd
    dates, o, h, l, c, v = generate_price_data(n=252 * 2)
    df = _pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v},
                       index=_pd.DatetimeIndex(dates))
    data = PandasDataFeed(dataname=df)

    # ---- 多策略对比 ----
    class SmaCross(bt.Strategy):
        params = (("fast", 10), ("slow", 30))
        def __init__(self):
            self.crossover = bt.indicators.CrossOver(
                bt.indicators.SMA(self.data.close, period=self.params.fast),
                bt.indicators.SMA(self.data.close, period=self.params.slow))
        def next(self):
            if not self.position and self.crossover > 0:
                self.buy(size=self.broker.getcash() / self.data.close[0])
            elif self.position and self.crossover < 0:
                self.close()

    for name, strat in [("SMA交叉", SmaCross), ("RSI+布林带", RsiBollingerStrategy)]:
        cerebro = bt.Cerebro()
        cerebro.adddata(data)
        cerebro.broker.setcash(100000.0)
        cerebro.addstrategy(strat)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="dd")

        print(f"\n{'='*50}")
        print(f"  策略: {name}")
        print(f"{'='*50}")
        print(f"初始资金: ¥{cerebro.broker.getvalue():,.0f}")
        results = cerebro.run()
        print(f"最终资金: ¥{cerebro.broker.getvalue():,.0f}")

        strat_result = results[0]
        sharpe = strat_result.analyzers.sharpe.get_analysis()
        dd = strat_result.analyzers.drawdown.get_analysis()

        sr = sharpe.get("sharperatio", "N/A")
        max_dd = dd.get("max", {}).get("drawdown", 0) if dd.get("max") else 0
        dd_len = dd.get("max", {}).get("len", 0) if dd.get("max") else 0

        print(f"Sharpe: {sr:.2f}" if isinstance(sr, float) else f"Sharpe: {sr}")
        print(f"最大回撤: {max_dd:.2f}%  (持续 {dd_len} 天)")

    print(f"\n{'='*50}")
    print("  提示：真实的策略选择要基于:")
    print("  1. 样本外 (out-of-sample) 测试")
    print("  2. 多时间段的稳定性")
    print("  3. 交易成本(手续费+滑点)的影响")
    print(f"{'='*50}")
