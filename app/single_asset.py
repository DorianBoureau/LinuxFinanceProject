import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils import (
    get_realtime_price,
    load_historical_data,
    max_drawdown,
    sharpe_ratio
)

# ============================================================
# HELPERS
# ============================================================

def ensure_series(x):
    if isinstance(x, pd.DataFrame):
        return x.iloc[:, 0]
    return x

# ============================================================
# STRATEGIES
# ============================================================

def buy_and_hold(df):
    df = df.copy()
    p = ensure_series(df["price"])
    df["strategy"] = p / p.iloc[0]
    return df

def momentum_strategy(df, window=20):
    df = df.copy()
    p = ensure_series(df["price"])
    df["return"] = p.pct_change()
    df["signal"] = (p > p.shift(window)).astype(int)
    df["strategy"] = (1 + df["return"] * df["signal"]).cumprod()
    return df

def ma_crossover_strategy(df, fast=20, slow=100):
    df = df.copy()
    p = ensure_series(df["price"])
    df["fast_ma"] = p.rolling(fast).mean()
    df["slow_ma"] = p.rolling(slow).mean()
    df["signal"] = (df["fast_ma"] > df["slow_ma"]).astype(int)
    df["return"] = p.pct_change()
    df["strategy"] = (1 + df["return"] * df["signal"]).cumprod()
    return df

# ============================================================
# MAIN MODULE
# ============================================================

def run_single_asset_module():

    st.markdown("<meta http-equiv='refresh' content='300'>", unsafe_allow_html=True)
    st.title("Single Asset Quantitative Analysis")
    st.write("")

    # ============================================================
    # SIDEBAR
    # ============================================================

    st.sidebar.header("Asset Parameters")

    asset = st.sidebar.selectbox(
        "Select Asset",
        ["BTC-USD", "AAPL", "EURUSD=X", "GC=F"]
    )

    timeframe = st.sidebar.radio(
        "Timeframe",
        ["1D", "1W", "1M", "3M", "1Y", "5Y", "MAX"],
        index=6
    )

    strategy_choice = st.sidebar.selectbox(
        "Strategy",
        ["Buy & Hold", "Momentum", "MA Crossover"]
    )

    fast, slow, window = None, None, None

    if strategy_choice == "Momentum":
        window = st.sidebar.slider("Momentum Window", 5, 90, 20)

    elif strategy_choice == "MA Crossover":
        fast = st.sidebar.slider("Fast MA (days)", 5, 50, 20)
        slow = st.sidebar.slider("Slow MA (days)", 50, 200, 100)

    # ============================================================
    # REAL TIME PRICE (SILENT FALLBACK)
    # ============================================================

    st.subheader(f"Current Price — {asset}")

    price_now = get_realtime_price(asset)

    if price_now is None:
        df_tmp = load_historical_data(asset)
        if df_tmp is not None and not df_tmp.empty:
            price_now = float(df_tmp["price"].iloc[-1])
        else:
            price_now = None

    if price_now is None:
        st.metric("Current Price", "N/A")
    else:
        st.metric("Current Price", f"{price_now:,.6f}")

    st.write("")

    # ============================================================
    # LOAD DATA
    # ============================================================

    df = load_historical_data(asset)

    if df is None or df.empty:
        st.error("No data available.")
        return

    df["price"] = ensure_series(df["price"])
    df = df.sort_index()

    # ============================================================
    # APPLY TIMEFRAME
    # ============================================================

    if timeframe == "1D":
        df = df.tail(3)      
    elif timeframe == "1W":
        df = df.tail(7)      
    elif timeframe == "1M":
        df = df.tail(30)     
    elif timeframe == "3M":
        df = df.tail(90)     
    elif timeframe == "1Y":
        df = df.tail(365)     
    elif timeframe == "5Y":
        df = df.tail(1825)   

    # ============================================================
    # TABS
    # ============================================================

    tab_graph, tab_info, tab_strategy = st.tabs([
        "📊 Chart",
        "ℹ️ Important information",
        "⚡ Strategy"
    ])

    # ============================================================
    # TAB GRAPH
    # ============================================================

    with tab_graph:

        st.subheader("Data Overview")
        st.write(f"Data available from: **{df.index[0]}**")
        st.write(f"Data available to: **{df.index[-1]}**")
        st.write(f"Total rows: **{len(df)}**")
        st.write("")

        if strategy_choice == "Buy & Hold":
            df = buy_and_hold(df)
        elif strategy_choice == "Momentum":
            df = momentum_strategy(df, window)
        elif strategy_choice == "MA Crossover":
            df = ma_crossover_strategy(df, fast, slow)

        price_series = ensure_series(df["price"])
        strategy_series = ensure_series(df["strategy"])

        # ============================================================
        # PERFORMANCE METRICS
        # ============================================================

        st.subheader("Performance Metrics")

        strategy_returns = strategy_series.pct_change()

        col1, col2, col3 = st.columns(3)
        col1.metric("Max Drawdown", f"{max_drawdown(strategy_series):.2%}")
        col2.metric("Sharpe Ratio", f"{sharpe_ratio(strategy_returns):.2f}")
        col3.metric("Volatility (Annual)", f"{(strategy_returns.std()*np.sqrt(252)):.2%}")

        # ============================================================
        # PRICE + STRATEGY CHART
        # ============================================================

        st.write("### Price & Strategy Chart")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df.index,
            y=price_series,
            mode="lines",
            name="Price",
            line=dict(color="#4AA3FF", width=2),
            yaxis="y1"
        ))

        fig.add_trace(go.Scatter(
            x=df.index,
            y=strategy_series,
            mode="lines",
            name="Strategy (Cumulative Return)",
            line=dict(color="#FFA500", width=2),
            yaxis="y2"
        ))

        # 🔥🔥🔥 FREE ZOOM + FREE NAVIGATION FIX HERE 🔥🔥🔥
        fig.update_xaxes(fixedrange=False)   # free horizontal zoom
        fig.update_yaxes(fixedrange=False)   # free vertical zoom

        fig.update_layout(
            height=540,
            hovermode="x unified",
            dragmode="pan",
            xaxis=dict(
                title="Date",
                rangeslider=dict(visible=True),
                fixedrange=False   # allow zoom
            ),
            yaxis=dict(
                title="Price",
                side="left",
                showgrid=False,
                fixedrange=False   # allow zoom
            ),
            yaxis2=dict(
                title="Strategy (Return ×)",
                overlaying="y",
                side="right",
                showgrid=False,
                fixedrange=False   # allow zoom
            ),
            plot_bgcolor="#0E1117",
            paper_bgcolor="#0E1117",
            font=dict(color="white"),
        )

        st.plotly_chart(fig, use_container_width=True)

    # ============================================================
    # TAB INFO
    # ============================================================

    with tab_info:

        st.subheader("📌 Important Information")

        start_date = df.index[0]
        end_date = df.index[-1]

        start_price = float(df["price"].iloc[0])
        last_price = float(df["price"].iloc[-1])

        high_price = float(df["price"].max())
        low_price = float(df["price"].min())

        total_perf = ((last_price - start_price) / start_price) * 100
        perf_color = "green" if total_perf >= 0 else "red"

        st.write(f"**Asset:** {asset}")
        st.write(f"**Data Start:** {start_date.date()}")
        st.write(f"**Data End:** {end_date.date()}")

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        col1.metric("📉 Lowest Price", f"{low_price:,.2f} USD")
        col2.metric("📈 Highest Price", f"{high_price:,.2f} USD")
        col3.metric("💰 Current Price", f"{last_price:,.2f} USD")

        st.markdown("---")

        st.markdown(
            f"""
            <h3>Total Performance Since Start:</h3>
            <div style="font-size:32px; font-weight:700; color:{perf_color};">
                {total_perf:.2f}%
            </div>
            """,
            unsafe_allow_html=True
        )

    # ============================================================
    # TAB STRATEGY DETAILS — ENGLISH VERSION
    # ============================================================

    with tab_strategy:

        st.subheader("📘 Strategy Details")
        st.markdown("---")

        # --------------------------------------------------------
        # 1. BUY & HOLD
        # --------------------------------------------------------
        st.markdown("""
        ## 📌 1. Buy & Hold Strategy

        **Concept:**  
        Buy once and hold forever.

        **Rules:**
        - Initial purchase  
        - Never sell  
        - 100% exposure  

        **Advantages:**
        - ✔ Very simple  
        - ✔ No optimization required  
        - ✔ Strong long-term performance  

        **Drawbacks:**
        - ❌ Huge drawdowns  
        - ❌ Always exposed to market risk  
        """)
        st.markdown("---")

        # --------------------------------------------------------
        # 2. MOMENTUM
        # --------------------------------------------------------
        st.markdown(f"""
        ## 📌 2. Momentum Strategy

        **Concept:**  
        Price must be higher than it was **{window} days ago**.

        **Rules:**
        - Long if `price > price {window} days ago`  
        - Cash otherwise  

        **Advantages:**
        - ✔ Reduces drawdowns  
        - ✔ Performs well in bullish trends  

        **Drawbacks:**
        - ❌ Performs poorly in sideways markets  
        """)
        st.markdown("---")

        # --------------------------------------------------------
        # 3. MA CROSSOVER
        # --------------------------------------------------------
        st.markdown(f"""
        ## 📌 3. Moving Average Crossover Strategy

        **Concept:**  
        Use two moving averages:  
        - Fast MA: **{fast} days**  
        - Slow MA: **{slow} days**

        **Rules:**
        - Long if `MA{fast} > MA{slow}`  
        - Cash otherwise  

        **Advantages:**
        - ✔ Robust  
        - ✔ Filters short-term noise  

        **Drawbacks:**
        - ❌ Late signals  
        - ❌ Frequent whipsaws  
        """)

