# app/quantB/dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# imports locaux (assurez-vous que ces fichiers existent)
from quantB.data_loader import load_multiple_assets, get_returns
from quantB.portfolio_engine import (
    equal_weight_weights,
    normalize_weights,
    compute_portfolio_returns,
    rebalance_portfolio,
    compute_cumulative_value,
)
from quantB.metrics import (
    correlation_matrix,
    annualized_return,
    annualized_volatility,
    sharpe_ratio,
    max_drawdown,
    diversification_effect,
)


def run_quantB():
    st.header("Quant B — Multi-Asset Portfolio Module")

    # -------------------------
    # 1. Sidebar - Inputs
    # -------------------------
    st.sidebar.subheader("Paramètres de récupération des données")
    today = datetime.today().date()
    default_start = today - timedelta(days=365)  # 1 an par défaut

    start_date = st.sidebar.date_input("Start date", value=default_start)
    end_date = st.sidebar.date_input("End date", value=today)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Actifs & stratégie")

    # Exemple d'actifs par défaut (tu peux les remplacer)
    default_assets = ["AAPL", "MSFT", "GOOGL", "TSLA", "BTC-USD"]  # inclut crypto tickers si yfinance
    assets = st.sidebar.multiselect(
        "Choisir les actifs (au moins 3)", options=default_assets, default=default_assets[:3]
    )

    if len(assets) < 3:
        st.warning("Sélectionne au moins 3 actifs pour le module Quant B.")
        st.stop()

    strategy = st.sidebar.selectbox("Stratégie de portefeuille", ["Equal Weight", "Custom Weights", "Rebalancing"])
    rebalance_freq = None
    if strategy == "Rebalancing":
        rebalance_freq = st.sidebar.selectbox("Fréquence de rebalancement", ["W", "M"])  # W=weekly, M=monthly

    st.sidebar.markdown("---")
    st.sidebar.subheader("Paramètres supplémentaires")
    initial_value = st.sidebar.number_input("Valeur initiale du portefeuille (NAV)", value=100.0, step=10.0)
    risk_free = st.sidebar.number_input("Taux sans risque annuel (pour Sharpe)", value=0.02, step=0.001, format="%.4f")

    st.sidebar.markdown("---")
    if st.sidebar.button("Rafraîchir / Charger les données"):
        st.experimental_rerun()

    # -------------------------
    # 2. Load data
    # -------------------------
    with st.spinner("Chargement des données..."):
        try:
            price_df = load_multiple_assets(assets, start=start_date.isoformat(), end=end_date.isoformat())
            if price_df is None or price_df.empty:
                st.error("Aucune donnée récupérée — vérifie les tickers ou la connexion.")
                st.stop()
        except Exception as e:
            st.error(f"Erreur lors du chargement des données : {e}")
            st.stop()

    st.success("Données chargées ✅")
    # Sanitize column names: yfinance or other sources can sometimes return
    # MultiIndex or tuple-like column labels (e.g. ("AAPL", "AAPL")).
    # Plotly expects the 'name' property to be a string, so coerce columns
    # to readable strings here.
    def _col_to_str(c):
        if isinstance(c, str):
            return c
        if isinstance(c, (tuple, list)):
            # prefer the last non-empty element in the tuple/list
            for x in reversed(c):
                if x:
                    return str(x)
            return "_".join(map(str, c))
        return str(c)

    price_df.columns = [_col_to_str(c) for c in price_df.columns]

    st.write(f"Données comprises entre **{price_df.index.min().date()}** et **{price_df.index.max().date()}**")
    st.dataframe(price_df.tail(5))

    # -------------------------
    # 3. Compute returns & weights
    # -------------------------
    returns_df = get_returns(price_df)

    n_assets = returns_df.shape[1]

    if strategy == "Equal Weight":
        weights = equal_weight_weights(n_assets)

    elif strategy == "Custom Weights":
        st.subheader("Définir des poids personnalisés")
        st.write("Utilise les sliders pour définir les poids; ils seront normalisés automatiquement.")
        # create sliders for each asset
        sliders = []
        cols = st.columns(2)
        for i, asset in enumerate(returns_df.columns):
            with cols[i % 2]:
                val = st.slider(f"{asset} weight (raw)", 0.0, 100.0, 100.0 / n_assets)
                sliders.append(val)
        weights = normalize_weights(sliders)

    elif strategy == "Rebalancing":
        st.subheader("Paramètres de rebalancing")
        st.write("Poids initiaux (raw) — seront normalisés.")
        cols = st.columns(2)
        raw = []
        for i, asset in enumerate(returns_df.columns):
            with cols[i % 2]:
                v = st.number_input(f"{asset} initial weight (raw)", value=1.0, step=0.1, format="%.2f")
                raw.append(v)
        weights = normalize_weights(raw)

    # Show weights table
    weights_series = pd.Series(weights, index=returns_df.columns)
    st.subheader("Poids du portefeuille")
    st.table(pd.DataFrame({"Asset": weights_series.index, "Weight": weights_series.values}).set_index("Asset"))

    # -------------------------
    # 4. Compute portfolio returns & NAV
    # -------------------------
    if strategy == "Rebalancing":
        # rebalance_portfolio returns daily series after concatenation of periods
        try:
            port_returns = rebalance_portfolio(returns_df, weights, freq=rebalance_freq)
            # rebalance_portfolio may return non-sorted index — sort by index
            port_returns = port_returns.sort_index()
        except Exception as e:
            st.error(f"Erreur pendant le rebalancement : {e}")
            st.stop()
    else:
        port_returns = compute_portfolio_returns(returns_df, weights)

    port_cum = compute_cumulative_value(port_returns, initial_value=initial_value)

    # -------------------------
    # 5. Plots — Prices + Portfolio NAV
    # -------------------------
    st.subheader("Prix des actifs et NAV du portefeuille")

    fig = go.Figure()
    # normalize prices for plotting on same scale (optional)
    norm_prices = price_df / price_df.iloc[0] * initial_value

    for col in norm_prices.columns:
        fig.add_trace(go.Scatter(x=norm_prices.index, y=norm_prices[col], name=str(col), mode="lines"))

    fig.add_trace(go.Scatter(x=port_cum.index, y=port_cum.values, name="Portfolio NAV", mode="lines", line=dict(width=4)))
    fig.update_layout(height=500, legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # 6. KPIs
    # -------------------------
    st.subheader("Metrics du portefeuille")

    col1, col2, col3, col4 = st.columns(4)
    try:
        ann_ret = annualized_return(port_returns)
        ann_vol = annualized_volatility(port_returns)
        sr = sharpe_ratio(port_returns, risk_free_rate=risk_free)
        mdd = max_drawdown(port_cum)

        col1.metric("Annualized Return", f"{ann_ret:.2%}")
        col2.metric("Annualized Volatility", f"{ann_vol:.2%}")
        col3.metric("Sharpe Ratio", f"{sr:.2f}")
        col4.metric("Max Drawdown", f"{mdd:.2%}")
    except Exception as e:
        st.error(f"Erreur calcul metrics : {e}")

    # Diversification effect
    try:
        div_eff = diversification_effect(returns_df, weights)
        st.write(f"**Effet de diversification (naive_vol - vol_port):** {div_eff:.4f}")
    except Exception as e:
        st.info("Impossible de calculer l'effet de diversification : " + str(e))

    # -------------------------
    # 7. Correlation matrix
    # -------------------------
    st.subheader("Matrice de corrélation")
    try:
        corr = correlation_matrix(returns_df)
        fig_corr = px.imshow(corr, text_auto=True, aspect="auto")
        st.plotly_chart(fig_corr, use_container_width=True)
    except Exception as e:
        st.info("Erreur matrice corr: " + str(e))

    # -------------------------
    # 8. Comparison single assets vs portfolio
    # -------------------------
    st.subheader("Comparaison: actifs individuels vs Portefeuille")

    # cumulative returns for each asset (normalized to initial_value)
    assets_cum = (1 + returns_df).cumprod() * initial_value

    comp_fig = go.Figure()
    for col in assets_cum.columns:
        comp_fig.add_trace(go.Scatter(x=assets_cum.index, y=assets_cum[col], name=str(col), mode="lines"))
    comp_fig.add_trace(go.Scatter(x=port_cum.index, y=port_cum.values, name="Portfolio", mode="lines", line=dict(width=4)))
    comp_fig.update_layout(height=450, legend=dict(orientation="h"))
    st.plotly_chart(comp_fig, use_container_width=True)

    # -------------------------
    # 9. Export / Download
    # -------------------------
    st.subheader("Export")
    export_df = pd.DataFrame({"portfolio_returns": port_returns}).join(price_df, how="left")
    export_df["portfolio_cum"] = port_cum
    csv = export_df.to_csv(index=True).encode("utf-8")
    st.download_button("Télécharger le rapport CSV", csv, file_name="quantB_portfolio_report.csv", mime="text/csv")

    st.info("Module Quant B loaded.")
