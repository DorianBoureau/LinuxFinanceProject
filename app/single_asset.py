import streamlit as st
import pandas as pd
import numpy as np
import time
from sklearn.linear_model import LinearRegression

from utils import (
    get_realtime_price,
    load_historical_data,
    max_drawdown,
    sharpe_ratio
)

# ============================================================
#  HELPERS
# ============================================================

def ensure_series(x):
    """Ensures a clean 1D Pandas Series (fixes (n,1) DataFrame cases)."""
    if isinstance(x, pd.DataFrame):
        return x.iloc[:, 0]
    return x


# ============================================================
#  STRATEGIES
# ============================================================

def buy_and_hold(df):
    df = df.copy()
    price = ensure_series(df["price"])
    df["strategy"] = price / price.iloc[0]
    return df


def momentum_strategy(df, window=20):
    df = df.copy()
    price = ensure_series(df["price"])

    df["return"] = price.pct_change()
    df["signal"] = (price > price.shift(window)).astype(int)

    df["strategy"] = (1 + df["return"] * df["signal"]).cumprod()
    return df


# ============================================================
#  STREAMLIT MODULE
# ============================================================

def run_single_asset_module():

    # ============================================================
    # AUTO REFRESH (toutes les 5 minutes)
    # ============================================================
    if int(time.time()) % (5 * 60) < 2:
        st.experimental_rerun()

    st.title("🔵 Single Asset Quantitative Analysis")

    # ------------------------------
    # Sidebar parameters
    # ------------------------------

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
        window = st.sidebar.slider("Momentum Lookback Window", 5, 90, 20)

    # ------------------------------
    # REAL-TIME PRICE
    # ------------------------------

    st.subheader(f"Current Price of {asset}")

    try:
        price_now = get_realtime_price(asset)
        st.metric("Real-Time Price", round(price_now, 6))
    except:
        st.error("Real-time price unavailable.")
        price_now = None

    # ------------------------------
    # LOAD HISTORICAL DATA
    # ------------------------------

    df = load_historical_data(asset)

    if df is None or df.empty:
        st.error(f"❌ No historical data for {asset}.")
        return

    df = df.copy()
    df["price"] = ensure_series(df["price"])

    # ------------------------------
    # APPLY STRATEGY
    # ------------------------------

    if strategy_choice == "Buy & Hold":
        df = buy_and_hold(df)
    else:
        df = momentum_strategy(df, window)

    strategy = ensure_series(df["strategy"])
    price_series = ensure_series(df["price"])

    # ------------------------------
    # PERFORMANCE METRICS
    # ------------------------------

    st.subheader("📈 Performance Metrics")

    returns = price_series.pct_change().dropna()

    # Max Drawdown
    try:
        md = float(max_drawdown(price_series))
        st.write(f"**Max Drawdown:** {md:.2%}")
    except:
        st.write("**Max Drawdown:** N/A")

    # Sharpe Ratio
    try:
        sr = float(sharpe_ratio(returns))
        st.write(f"**Sharpe Ratio:** {sr:.2f}")
    except:
        st.write("**Sharpe Ratio:** N/A")

    # Annual Volatility
    try:
        vol = float(returns.std() * (252 ** 0.5))
        st.write(f"**Annual Volatility:** {vol:.2%}")
    except:
        st.write("**Annual Volatility:** N/A")

    # ------------------------------
    # NORMALIZED CHART (QUANT STANDARD)
    # ------------------------------

    st.subheader("📊 Price & Strategy Performance (Normalized)")

    chart_df = pd.DataFrame({
        "price_normalized": price_series / price_series.iloc[0],
        "strategy_normalized": strategy
    })

    st.line_chart(chart_df, height=450)

    st.caption(
        "💡 Both curves start at 1.0 for proper comparison. "
        "This is the standard method used in quantitative finance."
    )


    # ============================================================
    #  BONUS — SIMPLE LINEAR REGRESSION FORECAST
    # ============================================================

    st.subheader("🔮 Simple Price Forecast (Linear Regression)")

    df = df.dropna()
    y = price_series.values.reshape(-1, 1)
    X = np.arange(len(y)).reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)

    # Predict next 30 days
    future_X = np.arange(len(y), len(y) + 30).reshape(-1, 1)
    future_pred = model.predict(future_X)

    forecast_dates = pd.date_range(df.index[-1], periods=30, freq="D")

    forecast_df = pd.DataFrame({
        "historical_price": price_series,
        "forecast_price": pd.Series(future_pred.flatten(), index=forecast_dates)
    })

    st.line_chart(forecast_df, height=400)
    st.caption("📘 Model: Linear Regression — for illustrative forecasting only.")
