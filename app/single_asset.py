import streamlit as st
import pandas as pd
from utils import (
    get_realtime_price,
    load_historical_data,
    max_drawdown,
    sharpe_ratio
)

# --------------------------------
# STRATEGIES
# --------------------------------

def buy_and_hold(df):
    df["strategy"] = df["price"] / df["price"].iloc[0]
    return df

def momentum_strategy(df, window=20):
    df["return"] = df["price"].pct_change()
    df["signal"] = (df["price"] > df["price"].shift(window)).astype(int)
    df["strategy"] = (1 + df["return"] * df["signal"]).cumprod()
    return df

# --------------------------------
# STREAMLIT UI
# --------------------------------

def run_single_asset_module():
    st.title("🔵 Single Asset Quantitative Analysis")

    # Sidebar — parameters
    st.sidebar.header("Asset Parameters")
    asset = st.sidebar.selectbox(
        "Choose an asset:",
        ["BTCUSDT", "AAPL", "EURUSD=X", "GC=F"]
    )

    strategy_choice = st.sidebar.selectbox(
        "Choose Strategy:",
        ["Buy & Hold", "Momentum"]
    )

    if strategy_choice == "Momentum":
        window = st.sidebar.slider("Momentum Window", 5, 60, 20)

    # ------------------------------------
    # REAL-TIME PRICE
    # ------------------------------------
    st.subheader(f"Current Price of {asset}")
    try:
        price = get_realtime_price(asset)
        st.metric("Real-Time Price", price)
    except Exception as e:
        st.error(f"Real-time price unavailable for {asset}: {e}")
        price = None
        st.metric("Real-Time Price", "N/A")

    # ------------------------------------
    # HISTORICAL DATA
    # ------------------------------------
    df = load_historical_data(asset)
    if df is None or df.empty:
        st.error(f"Historical data unavailable for {asset} — cannot compute metrics or plots.")
        return

    # ------------------------------------
    # STRATEGY APPLICATION
    # ------------------------------------
    if strategy_choice == "Buy & Hold":
        df = buy_and_hold(df)
    else:
        df = momentum_strategy(df, window)

    # ------------------------------------
    # METRICS
    # ------------------------------------
    st.subheader("📈 Performance Metrics")

    # Force "price" to be a Series (fixes ALL errors)
    if isinstance(df["price"], pd.DataFrame):
        price_series = df["price"].iloc[:, 0]
    else:
        price_series = df["price"]

    returns = price_series.pct_change().dropna()

    # Max Drawdown
    try:
        md = max_drawdown(price_series)
        st.write(f"**Max Drawdown:** {md:.2%}")
    except Exception:
        st.write("**Max Drawdown:** N/A")

    # Sharpe Ratio
    try:
        sr = sharpe_ratio(returns)
        st.write(f"**Sharpe Ratio:** {sr:.2f}")
    except Exception:
        st.write("**Sharpe Ratio:** N/A")

    # Annual Volatility
    try:
        ann_vol = returns.std() * (252 ** 0.5)
        st.write(f"**Annual Volatility:** {ann_vol:.2%}")
    except Exception:
        st.write("**Annual Volatility:** N/A")

    # ------------------------------------
    # CHART
    # ------------------------------------
    st.subheader("📊 Price & Strategy Performance")

    # Recombine clean DataFrame for chart
    chart_df = pd.DataFrame({
        "price": price_series,
        "strategy": df["strategy"]
    })

    st.line_chart(chart_df)
