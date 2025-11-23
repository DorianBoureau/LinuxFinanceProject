import numpy as np
import pandas as pd

# -------------------------------------------------------------------
# Correlation Matrix
# -------------------------------------------------------------------
def correlation_matrix(returns_df):
    """
    Matrice de corrélation entre les actifs.
    """
    return returns_df.corr()


# -------------------------------------------------------------------
# Annualized Return
# -------------------------------------------------------------------
def annualized_return(portfolio_returns, freq=252):
    """
    Rendement annualisé d'une série de rendements journaliers.
    freq = 252 pour actions/crypto, 365 pour FX
    """
    mean_daily = portfolio_returns.mean()
    return (1 + mean_daily)**freq - 1


# -------------------------------------------------------------------
# Annualized Volatility
# -------------------------------------------------------------------
def annualized_volatility(portfolio_returns, freq=252):
    """
    Volatilité annualisée.
    """
    return portfolio_returns.std() * np.sqrt(freq)


# -------------------------------------------------------------------
# Sharpe Ratio
# -------------------------------------------------------------------
def sharpe_ratio(portfolio_returns, risk_free_rate=0.02, freq=252):
    """
    Sharpe ratio du portefeuille.
    risk_free_rate = 2% par défaut
    """
    ann_return = annualized_return(portfolio_returns, freq)
    ann_vol = annualized_volatility(portfolio_returns, freq)

    if ann_vol == 0:
        return np.nan

    return (ann_return - risk_free_rate) / ann_vol


# -------------------------------------------------------------------
# Max Drawdown
# -------------------------------------------------------------------
def max_drawdown(cumulative_values):
    """
    Max drawdown = pire perte maximale depuis un plus haut historique.
    cumulative_values doit être une courbe de NAV.
    """
    rolling_max = cumulative_values.cummax()
    drawdown = (cumulative_values - rolling_max) / rolling_max
    return drawdown.min()


# -------------------------------------------------------------------
# Diversification (réduction de volatilité)
# -------------------------------------------------------------------
def diversification_effect(returns_df, weights):
    """
    Calcule l'effet de diversification :
    sum(w_i * vol_i) - vol_portefeuille

    Si le résultat est positif → bonne diversification.
    """
    weights = np.array(weights)

    # volatilités des actifs
    vols = returns_df.std()

    # volatilité pondérée (sans diversification)
    naive_vol = np.sum(weights * vols)

    # volatilité réelle du portefeuille
    cov = returns_df.cov()
    port_vol = np.sqrt(weights.T @ cov @ weights)

    return naive_vol - port_vol
