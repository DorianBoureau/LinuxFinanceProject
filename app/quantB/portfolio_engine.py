import numpy as np
import pandas as pd

# -------------------------------------------------------------------
# 1. Allocation Strategies (Weight Calculation)
# -------------------------------------------------------------------

def get_equal_weights(n_assets):
    """Naive allocation: 1/N"""
    if n_assets == 0:
        return []
    return np.ones(n_assets) / n_assets

def get_inverse_volatility_weights(returns_df):
    """
    Risk Parity (Naive):
    Assets with higher volatility get lower weights.
    w_i = (1/vol_i) / sum(1/vol_j)
    """
    vols = returns_df.std()
    inv_vols = 1 / vols
    return inv_vols / inv_vols.sum()

def normalize_user_weights(weights_dict, assets_order):
    """
    Ensures user-defined weights sum to 1.0 and match the DataFrame column order.
    """
    raw_weights = np.array([weights_dict.get(asset, 0) for asset in assets_order])

    if raw_weights.sum() == 0:
        return get_equal_weights(len(assets_order))

    return raw_weights / raw_weights.sum()


# -------------------------------------------------------------------
# 2. Simulation Engine (Handling Drift)
# -------------------------------------------------------------------

def run_portfolio_simulation(returns_df, weights, rebalance_freq="No Rebal"):
    """
    Simulates portfolio evolution allowing for weight drift between rebalancing dates.

    returns_df: Daily returns (pct_change)
    weights: Target weights array
    rebalance_freq: 'No Rebal', 'W' (Weekly), 'M' (Monthly), 'Q' (Quarterly)
    """
    weights = np.array(weights)

    # Case 1: Buy and Hold (No Rebalancing)
    # Weights drift naturally as assets grow at different speeds.
    if rebalance_freq == "No Rebal":
        cumulative_returns = (1 + returns_df).cumprod()
        # Portfolio Value = Sum(weight_i * Asset_Growth_i)
        portfolio_idx = cumulative_returns.dot(weights)

        # Recover daily returns from the synthetic index
        portfolio_ret = portfolio_idx.pct_change().fillna(0)
        # Fix first day precision
        portfolio_ret.iloc[0] = returns_df.iloc[0].dot(weights)
        return portfolio_ret

    # Case 2: Periodic Rebalancing
    # We reset weights to target at the start of each period.
    else:
        periods = returns_df.groupby(pd.Grouper(freq=rebalance_freq))
        all_period_returns = []

        for date, period_data in periods:
            if period_data.empty:
                continue

            # Within a period, we drift (Buy & Hold logic)
            period_cum_growth = (1 + period_data).cumprod()
            period_portfolio_value = period_cum_growth.dot(weights)

            period_daily_rets = period_portfolio_value.pct_change()

            # Reset weights implies the first day return is just the dot product
            period_daily_rets.iloc[0] = period_data.iloc[0].dot(weights)

            all_period_returns.append(period_daily_rets)

        return pd.concat(all_period_returns)

# -------------------------------------------------------------------
# 3. Utils
# -------------------------------------------------------------------

def compute_cumulative_return(daily_returns):
    """Calculates NAV curve (Base 1)"""
    return (1 + daily_returns).cumprod()