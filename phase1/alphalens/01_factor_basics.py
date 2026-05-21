"""Alphalens 01 - 因子分析基础

用模拟数据演示因子分析的完整流程：
  1. 构建因子值
  2. 计算前向收益
  3. IC 分析（Information Coefficient）
  4. 分层回测（Quantile analysis）
  5. 因子 turnover

运行: uv run python phase1/alphalens/01_factor_basics.py
"""

import numpy as np
import pandas as pd
import alphalens as al


def generate_sample_data(n_stocks=50, n_days=252):
    """生成模拟数据：多只股票的价格和因子值"""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
    tickers = [f"STOCK_{i:03d}" for i in range(n_stocks)]

    # 价格：几何布朗运动
    returns = np.random.randn(n_days, n_stocks) * 0.02 + 0.0005
    prices = 100 * np.exp(np.cumsum(returns, axis=0))
    prices_df = pd.DataFrame(prices, index=dates, columns=tickers)

    # 因子值：与未来收益有 0.05 的相关性（模拟弱但真实的因子）
    # 因子 = 部分可预测的成分 + 噪声
    noise = np.random.randn(n_days, n_stocks) * 0.98
    predictive = np.vstack([
        np.zeros((5, n_stocks)),  # 前5天无关联（对齐到future returns）
        returns[:-5, :] * 0.02    # 与未来收益的弱相关
    ])
    factor = predictive + noise
    factor_df = pd.DataFrame(factor, index=dates, columns=tickers)

    return prices_df, factor_df


def run_analysis(prices, factor, name="Demo Factor"):
    """运行 Alphalens 标准分析流程"""
    # Step 1: 整理因子数据格式
    factor_data = al.utils.get_clean_factor_and_forward_returns(
        factor.stack(),
        prices,
        quantiles=5,
        periods=(1, 5, 20),  # 1天、5天、20天前向收益
        max_loss=0.35,
    )
    print(f"因子数据形状: {factor_data.shape}")
    print(f"列: {list(factor_data.columns)}")

    # Step 2: IC 分析
    print(f"\n{'='*60}")
    print(f"  {name} - IC 分析")
    print(f"{'='*60}")
    ic = al.performance.factor_information_coefficient(factor_data)
    print(ic.head(10))

    # Step 3: 分层回测（按因子值分5组，看各组收益）
    print(f"\n{'='*60}")
    print(f"  {name} - 分层回测 (Quantile Returns)")
    print(f"{'='*60}")
    mean_ret_by_q = al.performance.mean_return_by_quantile(factor_data, by_group=False)
    print(mean_ret_by_q.head(10))

    # Step 4: 累积收益（做多最高因子组 vs 做空最低因子组）
    print(f"\n{'='*60}")
    print(f"  {name} - 多空组合累积收益 (1D forward)")
    print(f"{'='*60}")
    mean_ret_by_q_daily, _ = al.performance.mean_return_by_quantile(
        factor_data, by_date=True, by_group=False, demeaned=False
    )
    ls_ret = mean_ret_by_q_daily[5].groupby("date").mean() - mean_ret_by_q_daily[1].groupby("date").mean()
    cumulative = (1 + ls_ret).cumprod()
    print(f"初始: 1.0000")
    print(f"最终: {cumulative.iloc[-1]:.4f}")
    print(f"年化收益: {(cumulative.iloc[-1] - 1) * 100:.2f}%")

    # Step 5: Turnover
    print(f"\n{'='*60}")
    print(f"  {name} - 因子换手率")
    print(f"{'='*60}")
    turnover = al.performance.factor_rank_autocorrelation(factor_data, period=20)
    print(turnover.head())

    return factor_data


if __name__ == "__main__":
    print("=" * 60)
    print("  Alphalens 因子分析入门")
    print("=" * 60)
    print("\n生成 50 只股票 × 252 天的模拟数据...\n")

    prices, factor = generate_sample_data()
    run_analysis(prices, factor, "Simulated Alpha Factor")

    print(f"\n{'='*60}")
    print("  关键指标解读:")
    print("  - IC Mean: 因子与未来收益的相关性，|IC|>0.02 有意义")
    print("  - IC Std:  IC 的稳定性，IC_IR=mean/std，>0.5 为较好")
    print("  - Quantile Spread: 第5组-第1组收益差，越大越好")
    print("  - Turnover: 因子排序稳定性，越高说明换仓越少")
    print(f"{'='*60}")
