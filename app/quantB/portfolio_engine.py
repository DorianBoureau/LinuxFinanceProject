import numpy as np
import pandas as pd

# -------------------------------------------------------------------
# Equal Weight Portfolio
# -------------------------------------------------------------------
def equal_weight_weights(n_assets):
    """
    Renvoie des poids égaux pour n actifs.
    """
    return np.ones(n_assets) / n_assets


# -------------------------------------------------------------------
# Custom Weight Portfolio
# -------------------------------------------------------------------
def normalize_weights(weights):
    """
    Normalise une liste de poids pour que leur somme = 1.
    """
    weights = np.array(weights)
    return weights / weights.sum()


# -------------------------------------------------------------------
# Portefeuille sans rebalancing
# -------------------------------------------------------------------
def compute_portfolio_returns(returns_df, weights):
    """
    Calcule le rendement du portefeuille chaque jour.
    returns_df = DataFrame des rendements journaliers (pct_change)
    weights = vecteur numpy
    """
    weights = np.array(weights).reshape(-1,)
    port_ret = returns_df.dot(weights)
    return port_ret


# -------------------------------------------------------------------
# Rebalancing
# -------------------------------------------------------------------
def rebalance_portfolio(returns_df, weights, freq="M"):
    """
    Rebalance le portefeuille selon une fréquence donnée :
    - 'W' = weekly
    - 'M' = monthly

    Le rebalancing consiste à remettre les poids comme au départ
    sur la période choisie.
    """

    weights = np.array(weights).reshape(-1,)

    # On découpe les données en sous-périodes selon la fréquence
    periods = returns_df.resample(freq)

    all_returns = []

    for period_start, period_df in periods:
        if len(period_df) == 0:
            continue

        # rendement du portefeuille sur cette période
        period_port_ret = period_df.dot(weights)

        all_returns.append(period_port_ret)

    # concatène les séries
    final_series = pd.concat(all_returns)
    return final_series


# -------------------------------------------------------------------
# Valeur cumulée du portefeuille (NAV)
# -------------------------------------------------------------------
def compute_cumulative_value(portfolio_returns, initial_value=100):
    """
    Transforme les rendements journaliers du portefeuille
    en courbe de valeur cumulée.
    """
    return initial_value * (1 + portfolio_returns).cumprod()
