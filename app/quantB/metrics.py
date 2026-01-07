import numpy as np
import pandas as pd

def compute_annualized_return(daily_returns, freq=252):
    """
    Geometric annualized return.
    Formula: (1 + r_total)^(252/N) - 1
    """
    if len(daily_returns) < 2:
        return 0.0

    cumulative = (1 + daily_returns).prod()
    n_days = len(daily_returns)

    return (cumulative) ** (freq / n_days) - 1

def compute_annualized_volatility(daily_returns, freq=252):
    """Annualized standard deviation."""
    return daily_returns.std() * np.sqrt(freq)

def compute_sharpe_ratio(daily_returns, risk_free_rate=0.0, freq=252):
    """
    Sharpe Ratio = (R_p - R_f) / Vol_p
    """
    mu = compute_annualized_return(daily_returns, freq)
    vol = compute_annualized_volatility(daily_returns, freq)

    if vol == 0:
        return 0.0
    return (mu - risk_free_rate) / vol

def compute_sortino_ratio(daily_returns, risk_free_rate=0.0, freq=252):
    """
    Sortino Ratio: Similar to Sharpe but only penalizes downside volatility.
    Better suited for asymmetrical assets like Crypto.
    """
    mu = compute_annualized_return(daily_returns, freq)

    # Consider only negative returns for risk calculation
    negative_returns = daily_returns[daily_returns < 0]

    if len(negative_returns) < 2:
        return np.nan

    downside_dev = negative_returns.std() * np.sqrt(freq)

    if downside_dev == 0:
        return np.nan

    return (mu - risk_free_rate) / downside_dev

def compute_max_drawdown(daily_returns):
    """
    Computes Maximum Drawdown (peak-to-valley loss).
    Returns a negative float (e.g., -0.20 for 20% loss).
    """
    cum_ret = (1 + daily_returns).cumprod()
    peak = cum_ret.cummax()
    drawdown = (cum_ret - peak) / peak
    return drawdown.min()

def compute_var_historical(daily_returns, confidence_level=0.95):
    """
    Historical Value at Risk (VaR) at 95%.
    "We are 95% confident the daily loss won't exceed X%".
    """
    return np.percentile(daily_returns, 100 * (1 - confidence_level))

def compute_cvar_historical(daily_returns, confidence_level=0.95):
    """
    Conditional VaR (Expected Shortfall).
    Average loss in the worst (1-conf)% scenarios.
    """
    var = compute_var_historical(daily_returns, confidence_level)
    return daily_returns[daily_returns <= var].mean()

def compute_correlation_matrix(returns_df):
    return returns_df.corr()

def compute_diversification_effect(returns_df, weights):
    """
    Calculates the 'Diversification Benefit'.
    Difference between the weighted average of individual volatilities
    and the actual portfolio volatility.
    """
    coeffs = np.array(weights)
    # 1. Individual annualized volatilities
    individual_vols = returns_df.std() * np.sqrt(252)

    # 2. Naive risk (assuming perfect correlation = 1)
    naive_risk = np.dot(coeffs, individual_vols)

    # 3. Real portfolio risk (using Covariance matrix)
    cov_matrix = returns_df.cov() * 252
    port_variance = np.dot(coeffs.T, np.dot(cov_matrix, coeffs))
    real_risk = np.sqrt(port_variance)

    return naive_risk - real_risk