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
                                 ["BTC-USD", "XAUUSD=X", "EURUSD=X", "AAPL"])

    strategy_choice = st.sidebar.selectbox("Choose Strategy:", 
                                           ["Buy & Hold", "Momentum"])

    if strategy_choice == "Momentum":
        window = st.sidebar.slider("Momentum Window", 5, 60, 20)

    st.subheader(f"Current Price of {asset}")
    price = get_realtime_price(asset)
    st.metric("Real-Time Price", price)

    df = load_historical_data(asset)

    # Apply selected strategy
    if strategy_choice == "Buy & Hold":
        df = buy_and_hold(df)
    else:
        df = momentum_strategy(df, window)

    # Metrics
    st.subheader("📈 Performance Metrics")

    returns = df["price"].pct_change()

    st.write(f"**Max Drawdown:** {max_drawdown(df['price']):.2%}")
    st.write(f"**Sharpe Ratio:** {sharpe_ratio(returns):.2f}")
    st.write(f"**Annual Volatility:** {returns.std() * (252**0.5):.2%}")

    # Plot
    st.subheader("📊 Price & Strategy Performance")
    st.line_chart(df[["price", "strategy"]])

    # Autorefresh every 5 minutes
    st.experimental_rerun()
