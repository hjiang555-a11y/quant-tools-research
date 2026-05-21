"""Alphalens 02 - 真实A股因子分析

用 akshare 获取真实数据，分析市盈率(PE)因子的选股效果。

因子逻辑：低PE股票 → 预期高收益（价值因子）

运行: uv run python phase1/alphalens/02_pe_factor.py
"""

import numpy as np
import pandas as pd


def get_csi300_pe_data():
    """获取沪深300成分股的PE数据作为因子值

    注：akshare 的 stock_a_lg_indicator 可获取行业PE，个股PE需逐个获取。
    这里用简化版示例——用个股历史PE数据。
    """
    try:
        import akshare as ak

        # 获取沪深300成分股列表
        hs300 = ak.index_stock_cons_csindex("000300")
        symbols = hs300["成分券代码"].tolist()[:20]  # 先取20只做演示
        print(f"获取到 {len(symbols)} 只成分股: {symbols[:5]}...")

        all_data = {}
        for sym in symbols[:20]:
            try:
                df = ak.stock_a_lg_indicator(symbol=sym)
                pe = df[["trade_date", "pe"]].copy()
                pe["trade_date"] = pd.to_datetime(pe["trade_date"])
                pe.set_index("trade_date", inplace=True)
                all_data[sym] = pe["pe"]
            except Exception:
                continue

        factor_df = pd.DataFrame(all_data)
        # 负PE去掉
        factor_df = factor_df.clip(lower=1)
        print(f"因子数据: {factor_df.shape}")

        # 需要价格数据来计算前向收益...
        # 这里简化，用模拟数据演示流程
        return None
    except Exception as e:
        print(f"获取真实数据失败: {e}")
        return None


def run_simulated_pe_analysis():
    """用模拟数据演示PE因子的分析流程"""
    # 内联数据生成
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=252, freq="B")
    tickers = [f"STOCK_{i:03d}" for i in range(30)]
    rets = np.random.randn(252, 30) * 0.02 + 0.0005
    prices_arr = 100 * np.exp(np.cumsum(rets, axis=0))
    prices = pd.DataFrame(prices_arr, index=dates, columns=tickers)

    # 构建模拟PE因子：用价格的倒数（低价→高PE-ish 模拟）
    pe_factor = 1.0 / (prices / prices.iloc[0] + np.random.randn(*prices.shape) * 0.1)

    print("=" * 60)
    print("  PE 因子分析示例 (模拟数据)")
    print("  因子逻辑: 低PE = 价值股 → 预期高收益")
    print("=" * 60)

    import alphalens as al

    factor_data = al.utils.get_clean_factor_and_forward_returns(
        pe_factor.stack(),
        prices,
        quantiles=5,
        periods=(1, 5, 20),
        max_loss=0.35,
    )

    # IC 分析
    ic = al.performance.factor_information_coefficient(factor_data)
    print("\n--- IC Summary ---")
    ic_summary = al.performance.mean_information_coefficient(factor_data)
    print(ic_summary)

    # 分层收益
    mean_ret, _ = al.performance.mean_return_by_quantile(
        factor_data, by_date=True, by_group=False, demeaned=False
    )
    print("\n--- Quantile Mean Returns (1D forward) ---")
    print(mean_ret.groupby("factor_quantile").mean())

    # 多空组合
    ls = mean_ret[5].groupby("date").mean() - mean_ret[1].groupby("date").mean()
    cumulative = (1 + ls).cumprod()
    print(f"\n--- 多空组合 (Q5 - Q1) ---")
    print(f"累积收益: {cumulative.iloc[-1]:.4f}")
    print(f"日均收益: {ls.mean():.6f}")

    return factor_data


if __name__ == "__main__":
    # 尝试真实数据，失败则用模拟
    result = get_csi300_pe_data()
    if result is None:
        factor_data = run_simulated_pe_analysis()

    print(f"\n{'='*60}")
    print("  PE因子分析要点:")
    print("  1. 低PE组(Q1)应跑赢高PE组(Q5) — 价值效应")
    print("  2. 观察IC是否为正 — IC正=低PE确实与高收益正相关")
    print("  3. 分市场看 — A股价值因子在2019-2021年失效，2022年后回归")
    print("  4. 行业中性很重要 — 银行PE低不等于银行股好")
    print(f"{'='*60}")
