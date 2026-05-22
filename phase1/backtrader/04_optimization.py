"""Backtrader 04 - 策略参数优化 + 样本外检验

核心认知：参数优化容易过拟合，必须做样本外验证！

运行: uv run python phase1/backtrader/04_optimization.py
"""

import backtrader as bt
import datetime
import random
import itertools
import numpy as np
import pandas as pd


class SmaCrossOptimized(bt.Strategy):
    """可优化参数的双均线策略"""
    params = (
        ("fast", 10),
        ("slow", 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.p.fast)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.p.slow)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position and self.crossover > 0:
            # 预留佣金，只用 95% 现金
            size = self.broker.getcash() * 0.95 / self.data.close[0]
            self.buy(size=size)
        elif self.position and self.crossover < 0:
            self.close()


def generate_data(n=504, seed=None):
    """生成模拟价格数据，包含趋势 + 噪声"""
    rng = random.Random(seed or random.randint(1, 99999))
    dates, o_vals, hi, lo, cl, vol = [], [], [], [], [], []
    price = 100.0
    d = datetime.date(2023, 1, 1)
    while len(dates) < n:
        d = d + datetime.timedelta(days=1)
        if d.weekday() >= 5:
            continue
        dates.append(d)
        trend = 0.0002 * np.sin(len(dates) / 30)
        noise = rng.gauss(0, 0.02)
        price *= (1 + trend + noise)
        o_vals.append(price * (1 + rng.gauss(0, 0.005)))
        hi.append(max(o_vals[-1], price) * 1.01)
        lo.append(min(o_vals[-1], price) * 0.99)
        cl.append(price)
        vol.append(rng.randint(500_000, 5_000_000))

    df = pd.DataFrame(
        {"open": o_vals, "high": hi, "low": lo, "close": cl, "volume": vol},
        index=pd.DatetimeIndex(dates),
    )
    return bt.feeds.PandasData(dataname=df)


def evaluate(cerebro):
    """提取评估指标"""
    r = cerebro.run()
    s = r[0]
    sharpe = s.analyzers.sharpe.get_analysis().get("sharperatio")
    sr = sharpe if sharpe is not None else float("nan")
    dd = (s.analyzers.dd.get_analysis().get("max") or {}).get("drawdown", 0)
    total = s.analyzers.trades.get_analysis().get("total", {})
    trades = total.get("total", 0) if total else 0
    pnl = cerebro.broker.getvalue() - cerebro.broker.startingcash
    return sr, dd, trades, pnl


if __name__ == "__main__":
    # ============================================================
    # 1. 参数网格搜索（样本内）
    # ============================================================
    print("=" * 60)
    print("  参数优化：SMA 双均线 fast/slow 网格搜索")
    print("=" * 60)

    results = []

    for fast, slow in itertools.product(range(5, 51, 5), range(20, 101, 10)):
        if fast >= slow:
            continue

        cerebro = bt.Cerebro()
        cerebro.adddata(generate_data(n=504))
        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(commission=0.001)
        cerebro.addstrategy(SmaCrossOptimized, fast=fast, slow=slow)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="dd")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

        sr, dd, trades, pnl = evaluate(cerebro)
        results.append((fast, slow, sr, dd, trades, pnl))

    results.sort(key=lambda x: x[4], reverse=True)
    print(f"\n{'fast':>5} {'slow':>5} {'PnL':>10} {'MaxDD':>8} {'Trades':>7} {'Sharpe':>8}")
    print("-" * 55)
    for fast, slow, sr, dd, tr, pnl in results[:5]:
        sr_str = f"{sr:.2f}" if sr == sr else "  N/A"
        print(f"{fast:>5} {slow:>5} {pnl:>+10,.0f} {dd:>7.1f}% {tr:>7} {sr_str:>8}")

    best_fast, best_slow, best_sr, best_dd, best_tr, best_pnl = results[0]
    sr_str = f"{best_sr:.2f}" if best_sr == best_sr else "N/A"
    print(f"\n最优参数 (样本内): fast={best_fast}, slow={best_slow}")
    print(f"  PnL={best_pnl:+,.0f}, MaxDD={best_dd:.1f}%, Trades={best_tr}, Sharpe={sr_str}")

    # ============================================================
    # 2. 样本外检验 (OOS)
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  样本外检验：用最优参数跑新数据")
    print(f"{'='*60}")

    cerebro_oos = bt.Cerebro()
    cerebro_oos.adddata(generate_data(n=504, seed=999))
    cerebro_oos.broker.setcash(100000.0)
    cerebro_oos.broker.setcommission(commission=0.001)
    cerebro_oos.addstrategy(SmaCrossOptimized, fast=best_fast, slow=best_slow)
    cerebro_oos.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro_oos.addanalyzer(bt.analyzers.DrawDown, _name="dd")
    cerebro_oos.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    oos_sr, oos_dd, oos_tr, oos_pnl = evaluate(cerebro_oos)
    print(f"样本内 PnL:    {best_pnl:>+10,.0f}  →  样本外 PnL:    {oos_pnl:>+10,.0f}")
    print(f"样本内 MaxDD:  {best_dd:>7.1f}%  →  样本外 MaxDD:  {oos_dd:>7.1f}%")
    print(f"样本内 Trades: {best_tr:>7}    →  样本外 Trades: {oos_tr:>7}")

    if best_sr == best_sr and oos_sr == oos_sr:
        print(f"\n⚠ Sharpe 衰减: {best_sr - oos_sr:.2f} (样本内→实盘的典型退化)")
    else:
        print(f"\n⚠ Sharpe 因交易次数不足无法计算，用 PnL 判断")

    # ============================================================
    # 3. 参数稳定性热力图
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  参数稳定性热力图 (PnL)")
    print(f"{'='*60}")
    print(f"{'slow→':>5}", end="")
    for s in range(20, 101, 10):
        print(f"{s:>7}", end="")
    print()

    for fast in range(5, 51, 5):
        print(f"f={fast:<3}", end="")
        for slow in range(20, 101, 10):
            if fast >= slow:
                print(f"{'':>7}", end="")
            else:
                found = [r for r in results if r[0] == fast and r[1] == slow]
                pnl = found[0][4] if found else 0
                print(f"{pnl:>+7,.0f}", end="")
        print()

    print(f"\n{'='*60}")
    print("  结论:")
    print("  1. 参数优化 ≠ 找到最优策略，只是曲线拟合")
    print("  2. 真正的 alpha 在参数空间中应该是一个「高原」而非「尖峰」")
    print("  3. 样本外衰减是必然的，关键是衰减后还有没有 alpha")
    print("  4. 实践中用 walk-forward optimization 更鲁棒")
    print(f"{'='*60}")
