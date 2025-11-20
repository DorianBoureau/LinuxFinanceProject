import requests
import pandas as pd
import numpy as np
import yfinance as yf


# -----------------
# REAL-TIME PRICE (BTCUSDT via Binance, sinon Yahoo Finance)
# -----------------
def get_realtime_price(symbol):
    # --- Crypto: Binance ---
    if symbol.endswith("USDT"):
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            r = requests.get(url, timeout=5).json()
            if "price" in r:
                return float(r["price"])
        except:
            pass

    # --- Yahoo Finance fallback ---
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if data.empty:
            return None
        return float(data["Close"].iloc[-1])
    except:
        return None



# -----------------
# HISTORICAL DATA (Yahoo > Binance fallback)
# -----------------
def load_historical_data(symbol):
    # 1. Try Yahoo Finance
    df = yf.download(symbol, period="2y", interval="1d", progress=False)

    if df is not None and not df.empty:
        df = df.rename(columns={"Close": "price"})
        df = df[["price"]].dropna()
        return df

    # 2. Crypto fallback (Binance)
    bin_sym = None
    if symbol.endswith("USDT"):
        bin_sym = symbol
    elif "-" in symbol:
        base = symbol.split("-")[0]
        bin_sym = base + "USDT"

    if bin_sym:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={bin_sym}&interval=1d&limit=1000"
            raw = requests.get(url, timeout=10).json()
            rows = []
            for item in raw:
                ts = int(item[0]) // 1000
                close = float(item[4])
                rows.append((pd.to_datetime(ts, unit="s"), close))
            df2 = pd.DataFrame(rows, columns=["date", "price"]).set_index("date")
            return df2
        except:
            pass

    return pd.DataFrame(columns=["price"])



# -----------------
# METRICS
# -----------------
def max_drawdown(series):
    roll_max = series.cummax()
    dd = (series - roll_max) / roll_max
    return float(dd.min())

def sharpe_ratio(returns):
    # Always convert to a Series to avoid ambiguity
    returns = pd.Series(returns).dropna()

    s = float(returns.std())

    # si aucune volatilité → Sharpe = 0
    if pd.isna(s) or s == 0:
        return 0.0

    mean_ret = float(returns.mean())
    sharpe = np.sqrt(252) * mean_ret / s

    return float(sharpe)


