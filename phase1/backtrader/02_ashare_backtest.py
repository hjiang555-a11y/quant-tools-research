"""Backtrader 02 - 真实A股数据回测

用 akshare 获取真实A股数据，运行 SMA 交叉策略。

运行: uv run python phase1/backtrader/02_ashare_backtest.py
"""

import backtrader as bt
import datetime


class SmaCrossover(bt.Strategy):
    """双均线交叉 + 止损 + 仓位管理"""
    params = (
        ("fast", 10),
        ("slow", 30),
        ("stop_loss", 0.05),   # 5% 止损
        ("position_pct", 0.8),  # 每次用 80% 资金
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.entry_price = 0

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f"  !! 订单失败: {order.status}")

    def next(self):
        # 止损检查
        if self.position and self.entry_price > 0:
            loss = (self.data.close[0] - self.entry_price) / self.entry_price
            if loss < -self.params.stop_loss:
                self.close()
                print(f"  !!! STOP LOSS {self.data.datetime.date()} @ {self.data.close[0]:.2f}")
                return

        # 信号
        if not self.position and self.crossover > 0:
            cash = self.broker.getcash() * self.params.position_pct
            size = cash / self.data.close[0]
            self.buy(size=size)
            print(f"  >>> BUY  {self.data.datetime.date()} @ {self.data.close[0]:.2f} | size={size:.0f}")
        elif self.position and self.crossover < 0:
            self.close()
            print(f"  <<< SELL {self.data.datetime.date()} @ {self.data.close[0]:.2f}")


def get_akshare_data(symbol="600519", start="20230101", end="20241231"):
    """用 akshare 获取A股日线数据，返回 Backtrader PandasData"""
    import pandas as pd
    import akshare as ak

    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                start_date=start, end_date=end, adjust="qfq")
    except Exception:
        # 网络不可用时回退到示例
        return None

    df = df.rename(columns={
        "日期": "datetime", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume",
    })
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)
    df["openinterest"] = 0

    class AKData(bt.feeds.PandasData):
        params = (("openinterest", "openinterest"),)

    return AKData(dataname=df)


def get_random_data():
    """回退方案：生成随机数据"""
    import random as _r
    dates, o_vals, hi, lo, cl, vol = [], [], [], [], [], []
    price = 100.0
    d = datetime.date(2024, 1, 1)
    while len(dates) < 252:
        d = d + datetime.timedelta(days=1)
        if d.weekday() >= 5:
            continue
        dates.append(d)
        price *= (1 + _r.gauss(0.0005, 0.015))
        o_vals.append(round(price * (1 + _r.gauss(0, 0.005)), 2))
        hi.append(round(max(o_vals[-1], price) * (1 + abs(_r.gauss(0, 0.008))), 2))
        lo.append(round(min(o_vals[-1], price) * (1 - abs(_r.gauss(0, 0.008))), 2))
        cl.append(round(price, 2))
        vol.append(_r.randint(1_000_000, 10_000_000))
    import pandas as pd
    df = pd.DataFrame({"open": o_vals, "high": hi, "low": lo, "close": cl, "volume": vol},
                      index=pd.DatetimeIndex(dates))
    return bt.feeds.PandasData(dataname=df)


if __name__ == "__main__":
    cerebro = bt.Cerebro()

    # 尝试获取真实数据
    print("正在获取A股数据...")
    data = get_akshare_data("600519", "20230101", "20241231")
    if data is None:
        print("无法获取真实数据，使用随机数据演示\n")
        data = get_random_data()
    else:
        print("已获取600519(贵州茅台)前复权日线数据\n")

    cerebro.adddata(data)
    cerebro.broker.setcash(100000.0)
    cerebro.addstrategy(SmaCrossover)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=0.02)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="dd")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annret")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    print(f"初始资金: ¥{cerebro.broker.getvalue():,.0f}\n")
    results = cerebro.run()
    print(f"\n最终资金: ¥{cerebro.broker.getvalue():,.0f}")

    strat = results[0]
    print(f"\n======== 策略评估 ========")
    sharpe = strat.analyzers.sharpe.get_analysis()
    dd = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()

    sr = sharpe.get("sharperatio", 0)
    max_dd = dd.get("max", {}).get("drawdown", 0) if dd.get("max") else 0
    total = trades.get("total", {}).get("total", 0) if trades.get("total") else 0
    won = trades.get("won", {}).get("total", 0) if trades.get("won") else 0
    lost = trades.get("lost", {}).get("total", 0) if trades.get("lost") else 0
    win_rate = won / total * 100 if total else 0

    print(f"Sharpe Ratio : {sr:.2f}")
    print(f"最大回撤     : {max_dd:.2f}%")
    print(f"交易次数     : {total}")
    print(f"胜率         : {win_rate:.1f}% ({won}W / {lost}L)")

    try:
        cerebro.plot(style="candlestick", volume=False)
    except Exception:
        print("(图表显示需要图形界面)")
