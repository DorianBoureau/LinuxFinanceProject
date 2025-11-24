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

    # Strategy parameters
    fast, slow, window = None, None, None

    if strategy_choice == "Momentum":
        window = st.sidebar.slider("Momentum Window", 5, 90, 20)

    elif strategy_choice == "MA Crossover":
        fast = st.sidebar.slider("Fast MA (days)", 5, 50, 20)
        slow = st.sidebar.slider("Slow MA (days)", 50, 200, 100)

    # ============================================================
    # REAL TIME PRICE
    # ============================================================

    st.subheader(f"Current Price — {asset}")
    price_now = get_realtime_price(asset)

    if price_now is None:
        st.error("Real-time price unavailable.")
    else:
        st.metric("Real-Time Price", f"{price_now:,.6f}")

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
        df = df.tail(7)
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

        # Select & apply strategy
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

        with col1:
            st.metric("Max Drawdown", f"{max_drawdown(strategy_series):.2%}")

        with col2:
            st.metric("Sharpe Ratio", f"{sharpe_ratio(strategy_returns):.2f}")

        with col3:
            vol = strategy_returns.std() * np.sqrt(252)
            st.metric("Volatility (Annual)", f"{vol:.2%}")

        # ============================================================
        # PRICE CHART
        # ============================================================

        st.write("### Price Chart")

        fig = go.Figure()

        # Price curve
        fig.add_trace(go.Scatter(
            x=df.index, y=price_series,
            mode="lines", name="Price",
            line=dict(color="#4AA3FF", width=2)
        ))

        # Strategy normalized to price scale
        strategy_norm = strategy_series * (price_series.iloc[0] / strategy_series.iloc[0])

        fig.add_trace(go.Scatter(
            x=df.index, y=strategy_norm,
            mode="lines", name="Strategy",
            line=dict(color="#FFA500", width=1.6)
        ))

        # Zoom & style
        y_max = float(price_series.max())
        y_min = float(price_series.min())
        pad = (y_max - y_min) * 0.20

        fig.update_yaxes(
            range=[y_min - pad, y_max + pad],
            fixedrange=False
        )

        fig.update_layout(
            height=520,
            hovermode="x unified",
            dragmode="pan",
            xaxis=dict(title="Date", rangeslider=dict(visible=True)),
            plot_bgcolor="#0E1117",
            paper_bgcolor="#0E1117",
            font=dict(color="white")
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

        with col1:
            st.metric("📉 Lowest Price", f"{low_price:,.2f} USD")

        with col2:
            st.metric("📈 Highest Price", f"{high_price:,.2f} USD")

        with col3:
            st.metric("💰 Current Price", f"{last_price:,.2f} USD")

        st.markdown("---")

        st.markdown(
            f"""
            <h3>Total Performance Since Start:</h3>
            <div style="
                font-size:32px;
                font-weight:700;
                color:{perf_color};
            ">
                {total_perf:.2f}%
            </div>
            """,
            unsafe_allow_html=True
        )

    # ============================================================
    # TAB STRATEGY DETAILS
    # ============================================================

    with tab_strategy:

        st.subheader("📘 Strategy Details")

        # --------------------------------------------------------
        # Buy & Hold
        # --------------------------------------------------------
        st.markdown(
            """
            # 📌 1. **Buy & Hold Strategy**
            - Buy once  
            - Never sell  
            - Exposed to all cycles  
            - Very high volatility  
            - Large drawdowns  
            ---
            """,
            unsafe_allow_html=True
        )

        # --------------------------------------------------------
        # Momentum
        # --------------------------------------------------------
        st.markdown(
            """
            # 📌 2. **Momentum Strategy**
            **Rule:**  
            > Go long when today’s price is higher than X days ago.  
            """
        )

        st.markdown(
            """
            ### ✔ Advantages
            - Simple trend-following method  
            - Often reduces drawdowns  

            ### ❗ Drawbacks
            - Can underperform in sideways markets  
            ---
            """
        )

        # --------------------------------------------------------
        # MA Crossover (only if selected)
        # --------------------------------------------------------
        if strategy_choice == "MA Crossover":
            st.markdown(
                f"""
                # 📌 3. **MA Crossover Strategy**
                **Rule:**  
                > Go long when the {fast}-day moving average is above the {slow}-day moving average.  
                > Stay in cash otherwise.

                ### ✔ Advantages
                - Robust trend-following  
                - Filters noise  
                - Reduces drawdowns

                ### ❗ Drawbacks
                - Whipsaws in low-volatility periods  
                - Can miss sudden reversals  
                ---
                """,
                unsafe_allow_html=True
            )
