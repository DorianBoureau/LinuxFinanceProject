import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from quantB.data_loader import load_market_data, get_returns
from quantB.portfolio_engine import (
    get_equal_weights,
    get_inverse_volatility_weights,
    normalize_user_weights,
    run_portfolio_simulation,
    compute_cumulative_return,
)
from quantB.metrics import (
    compute_annualized_return,
    compute_annualized_volatility,
    compute_sharpe_ratio,
    compute_sortino_ratio,
    compute_max_drawdown,
    compute_var_historical,
    compute_cvar_historical,
    compute_correlation_matrix,
    compute_diversification_effect
)

def run_quantB():
    st.header("Quant B — Multi-Asset Portfolio Module")

    # -------------------------
    # 1. Sidebar - Inputs
    # -------------------------
    st.sidebar.subheader("Data Fetching Parameters")
    today = datetime.today().date()
    default_start = today - timedelta(days=365)

    start_date = st.sidebar.date_input("Start Date", value=default_start)
    end_date = st.sidebar.date_input("End Date", value=today)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Assets & Strategy")

    # User Input for Tickers
    st.sidebar.info("Enter tickers separated by commas (e.g., AAPL, MSFT, BTC-USD).")

    default_tickers = "AAPL, MSFT, GOOGL, NVDA, BTC-USD"
    tickers_input = st.sidebar.text_area("Assets Tickers", value=default_tickers, height=70)

    # Parsing logic: Clean the input string into a clean list
    # 1. Replace newlines with commas (in case user pastes a column)
    # 2. Split by comma
    # 3. Strip whitespace and force uppercase
    assets = [x.strip().upper() for x in tickers_input.replace('\n', ',').split(',') if x.strip()]

    if len(assets) < 3:
        st.warning("Please select at least 3 assets for the Quant B module.")
        st.stop()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Parameters")
    initial_value = st.sidebar.number_input("Initial NAV", value=100.0, step=10.0)
    risk_free = st.sidebar.number_input("Risk-Free Rate (Annual)", value=0.02, step=0.001, format="%.4f")

    st.sidebar.markdown("---")
    if st.sidebar.button("Refresh / Load Data"):
        st.rerun()

    # -------------------------
    # 2. Load Data
    # -------------------------
    with st.spinner("Loading and caching data..."):
        price_df = load_market_data(assets, start_date, end_date)

        if price_df is None or price_df.empty:
            st.error("No data available. Please check your tickers.")
            st.stop()

    st.success(f"Data loaded for {len(price_df.columns)} assets!")

    # Sanitize column names (handle tuples from MultiIndex if any remain)
    def _col_to_str(c):
        if isinstance(c, str): return c
        if isinstance(c, (tuple, list)):
            for x in reversed(c):
                if x: return str(x)
            return "_".join(map(str, c))
        return str(c)

    price_df.columns = [_col_to_str(c) for c in price_df.columns]

    st.caption(f"Data Range: **{price_df.index.min().date()}** to **{price_df.index.max().date()}**")

    # -------------------------
    # 3. Strategy & Weights
    # -------------------------
    returns_df = get_returns(price_df)
    assets_list = returns_df.columns.tolist()
    n_assets = len(assets_list)

    # Strategy Selection
    strategy_type = st.radio(
        "Strategic Allocation Method",
        ["Equal Weight (1/N)", "Inverse Volatility (Risk Parity)", "Custom Weights"]
    )

    # Rebalancing Frequency
    rebal_freq_label = st.selectbox(
        "Rebalancing Frequency",
        ["None (Buy & Hold)", "Monthly (End of Month)", "Weekly", "Quarterly"]
    )

    freq_map = {
        "None (Buy & Hold)": "No Rebal",
        "Monthly (End of Month)": "M",
        "Weekly": "W",
        "Quarterly": "Q"
    }
    rebalance_freq = freq_map[rebal_freq_label]

    # --- Target Weights Calculation ---
    weights = []

    if strategy_type == "Equal Weight (1/N)":
        weights = get_equal_weights(n_assets)
        st.info("Each asset receives an identical allocation.")

    elif strategy_type == "Inverse Volatility (Risk Parity)":
        weights = get_inverse_volatility_weights(returns_df)
        st.info("Allocation is inversely proportional to historical volatility. Stable assets get higher weights.")

    elif strategy_type == "Custom Weights":
        st.write("Adjust weights below (automatically normalized to 100%).")
        user_inputs = {}
        cols = st.columns(3)
        for i, asset in enumerate(assets_list):
            with cols[i % 3]:
                val = st.number_input(f"{asset}", min_value=0.0, max_value=100.0, value=10.0, step=5.0)
                user_inputs[asset] = val

        weights = normalize_user_weights(user_inputs, assets_list)

    # Display Weights Table
    weights_df = pd.DataFrame({
        "Asset": assets_list,
        "Target Weight": [f"{w:.1%}" for w in weights]
    })
    st.write("**Target Allocation:**")
    st.dataframe(weights_df.set_index("Asset").T)

    # -------------------------
    # 4. Portfolio Simulation
    # -------------------------
    try:
        # Run the engine (handles drift & rebalancing)
        port_returns = run_portfolio_simulation(returns_df, weights, rebalance_freq=rebalance_freq)
        port_cum = compute_cumulative_return(port_returns) * initial_value

    except Exception as e:
        st.error(f"Simulation Error: {e}")
        st.stop()

    # -------------------------
    # 5. Pro Visualization (Performance & Drawdown)
    # -------------------------
    st.markdown("### 📈 Performance Analysis")

    tab1, tab2, tab3 = st.tabs(["Cumulative Performance", "Risk Analysis (Drawdown)", "Correlation"])

    with tab1:
        st.subheader("Performance Comparison (Base 100)")

        # Prepare combined data for the 'Main Chart' requirement
        chart_data = (1 + returns_df).cumprod() * 100
        chart_data["PORTFOLIO"] = port_cum

        fig_main = px.line(chart_data, title="Asset vs Portfolio Performance")

        # Style: Assets in thin dotted lines, Portfolio in thick solid green
        fig_main.update_traces(line=dict(width=1, dash='dot'), opacity=0.6)

        fig_main.update_traces(
            selector=dict(name="PORTFOLIO"),
            line=dict(width=4, color='#2ca02c', dash='solid'),
            opacity=1.0
        )
        st.plotly_chart(fig_main, use_container_width=True)

    with tab2:
        st.subheader("Underwater Plot (Drawdown)")
        wealth_index = (1 + port_returns).cumprod()
        previous_peaks = wealth_index.cummax()
        drawdown_series = (wealth_index - previous_peaks) / previous_peaks

        fig_dd = px.area(drawdown_series, title="Historical Drawdown (%)")
        fig_dd.update_traces(line_color='#d62728', fillcolor='rgba(214, 39, 40, 0.3)')
        fig_dd.update_layout(yaxis_tickformat='.1%')
        st.plotly_chart(fig_dd, use_container_width=True)

    with tab3:
        st.subheader("Asset Correlation Matrix")
        corr_matrix = compute_correlation_matrix(returns_df)
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            title="Pearson Correlation"
        )
        st.plotly_chart(fig_corr, use_container_width=True)

    # -------------------------
    # 6. KPI Dashboard
    # -------------------------
    st.markdown("### 📊 Key Performance Indicators (KPIs)")

    col1, col2, col3, col4 = st.columns(4)

    # Compute Metrics
    ann_ret = compute_annualized_return(port_returns)
    ann_vol = compute_annualized_volatility(port_returns)
    sharpe = compute_sharpe_ratio(port_returns, risk_free_rate=risk_free)
    sortino = compute_sortino_ratio(port_returns, risk_free_rate=risk_free)
    max_dd = compute_max_drawdown(port_returns)
    var_95 = compute_var_historical(port_returns)
    cvar_95 = compute_cvar_historical(port_returns)

    col1.metric("Ann. Return", f"{ann_ret:.2%}")
    col2.metric("Ann. Volatility", f"{ann_vol:.2%}")
    col3.metric("Max Drawdown", f"{max_dd:.2%}", delta_color="inverse")
    col4.metric("Sharpe Ratio", f"{sharpe:.2f}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sortino Ratio", f"{sortino:.2f}", help="Like Sharpe, but penalizes only downside volatility.")
    col2.metric("VaR (95%) 1d", f"{var_95:.2%}", help="Max expected daily loss with 95% confidence.")
    col3.metric("CVaR (95%)", f"{cvar_95:.2%}", help="Expected Shortfall: average loss in the worst 5% cases.")
    col4.metric("Days Observed", f"{len(port_returns)}")

    # --- Diversification Effect (Required for Grade) ---
    st.markdown("---")

    try:
        if len(weights) == len(returns_df.columns):
            div_benefit = compute_diversification_effect(returns_df, weights)
            st.metric(
                label="Diversification Benefit (Risk Reduction)",
                value=f"{div_benefit:.2%}",
                help="Reduction in volatility achieved through asset decorrelation. (Weighted Avg Vol - Portfolio Vol)"
            )
        else:
            st.warning("Cannot calculate diversification: mismatch in asset count.")
    except Exception as e:
        st.info(f"Diversification calc skipped: {e}")

    # -------------------------
    # 7. Data Export
    # -------------------------
    st.markdown("### 📥 Reporting")

    # Create exportable DF
    comparison_df = (1 + returns_df).cumprod() * 100
    comparison_df["PORTFOLIO"] = port_cum

    st.download_button(
        label="Download Reporting Data (CSV)",
        data=comparison_df.to_csv().encode('utf-8'),
        file_name='quantB_reporting.csv',
        mime='text/csv',
    )