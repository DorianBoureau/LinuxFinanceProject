import streamlit as st
import pandas as pd
from utils import (
    get_realtime_price, 
    load_historical_data, 
    max_drawdown, 
    sharpe_ratio
)

# -------------- STRATEGIES ---------------

def buy_and_hold(df):
    df["strategy"] = df["price"] / df["price"].iloc[0]
    return df

def momentum_strategy(df, window=20):
    df["return"] = df["price"].pct_change()
    df["signal"] = (df["price"] > df["price"].shift(window)).astype(int)
    df["strategy"] = (1 + df["return"] * df["signal"]).cumprod()
    return df

# -------------- STREAMLIT UI --------------

def run_single_asset_module():
    st.title("🔵 Single Asset Quantitative Analysis")

    st.sidebar.header("Asset Parameters")
    asset = st.sidebar.selectbox("Choose an asset:", 
                                 ["BTCUSDT", "XAUUSD=X", "EURUSD=X", "AAPL"])

    strategy_choice = st.sidebar.selectbox("Choose Strategy:", 
                                           ["Buy & Hold", "Momentum"])

    if strategy_choice == "Momentum":
        window = st.sidebar.slider("Momentum Window", 5, 60, 20)

    st.subheader(f"Current Price of {asset}")
    try:
        price = get_realtime_price(asset)
    except Exception as e:
        st.error(f"Real-time price unavailable for {asset}: {e}")
        price = None

    if price is not None:
        st.metric("Real-Time Price", price)
    else:
        st.metric("Real-Time Price", "N/A")

    df = load_historical_data(asset)
    if df is None or df.empty:
        st.error(f"Historical data unavailable for {asset} — cannot compute metrics or plots.")
        return

    # Apply selected strategy
    if strategy_choice == "Buy & Hold":
        df = buy_and_hold(df)
    else:
        df = momentum_strategy(df, window)

    # Metrics
    st.subheader("📈 Performance Metrics")

    # Ensure we operate on a Series (not a single-column DataFrame)
    price_series = df["price"]
    if isinstance(price_series, pd.DataFrame):
        price_series = price_series.iloc[:, 0]

    returns = price_series.pct_change()

    # Compute metrics and coerce to scalars for formatting
    try:
        md = max_drawdown(price_series)
        if isinstance(md, pd.Series):
            md = md.min()
        md_val = float(md)
        st.write(f"**Max Drawdown:** {md_val:.2%}")
    except Exception:
        st.write("**Max Drawdown:** N/A")

    try:
        sr = sharpe_ratio(returns)
        st.write(f"**Sharpe Ratio:** {float(sr):.2f}")
    except Exception:
        st.write("**Sharpe Ratio:** N/A")

    try:
        ann_vol = float(returns.std() * (252 ** 0.5))
        st.write(f"**Annual Volatility:** {ann_vol:.2%}")
    except Exception:
        st.write("**Annual Volatility:** N/A")

    # Plot
    st.subheader("📊 Price & Strategy Performance")
    st.line_chart(df[["price", "strategy"]])

    # Note: removed automatic immediate rerun to avoid infinite rerun loops.
