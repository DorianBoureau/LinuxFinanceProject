import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# -----------------
# REAL-TIME PRICE
# -----------------
def get_realtime_price(symbol):
    """
    Récupère le prix en temps réel via l'API Binance (crypto)
    ou via yfinance (indices/actions).
    """
    # Crypto case: only call Binance for USDT pairs (Binance uses e.g. BTCUSDT)
    if symbol.endswith("USDT"):
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            r = requests.get(url).json()
            if isinstance(r, dict) and "price" in r:
                return float(r["price"])
        except Exception:
            pass
    
    # Other assets
    data = yf.Ticker(symbol).history(period="1d")
    # Defensive: if no data, try a crypto-style fallback (e.g. BTC-USD -> BTCUSDT)
    if data is None or data.empty or "Close" not in data.columns or len(data["Close"]) == 0:
        # Attempt automatic crypto mapping for tickers with a dash (common for yfinance crypto symbols)
        try:
            if "-" in symbol:
                # e.g. BTC-USD -> BTCUSDT
                alt = symbol.replace("-", "") + "T" if not symbol.endswith("USDT") else symbol
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={alt}"
                r = requests.get(url).json()
                if isinstance(r, dict) and "price" in r:
                    return float(r["price"])
        except Exception:
            pass
        raise ValueError(f"No price data found for symbol '{symbol}'")
    return float(data["Close"].iloc[-1])


# -----------------
# HISTORICAL DATA
# -----------------
def load_historical_data(symbol):
    # Try yfinance first
    df = yf.download(symbol, period="2y")  # 2 years history
    if df is None or df.empty:
        # If yfinance failed (common for some crypto tickers), attempt Binance klines
        try:
            # Derive a Binance-style symbol when possible, e.g. 'BTC-USD' -> 'BTCUSDT'
            bin_sym = None
            if "-" in symbol:
                base = symbol.split("-")[0]
                bin_sym = base + "USDT"
            elif symbol.endswith("USDT"):
                bin_sym = symbol
            elif symbol.endswith("USD") and len(symbol) <= 8:
                # e.g. 'BTCUSD' or short tickers
                base = symbol.replace("USD", "")
                bin_sym = base + "USDT"

            if bin_sym:
                url = f"https://api.binance.com/api/v3/klines?symbol={bin_sym}&interval=1d&limit=1000"
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    # kline: [open_time, open, high, low, close, volume, close_time, ...]
                    rows = []
                    for item in data:
                        ts = int(item[0]) // 1000
                        close = float(item[4])
                        rows.append((pd.to_datetime(ts, unit="s"), close))
                    df2 = pd.DataFrame(rows, columns=["date", "price"]).set_index("date")
                    df2.index.name = None
                    df2 = df2.sort_index()
                    df2.dropna(inplace=True)
                    return df2
        except Exception:
            pass

        # return empty DataFrame with expected column if everything failed
        return pd.DataFrame(columns=["price"])

    df = df.rename(columns={"Close": "price"})
    df = df[["price"]]
    df.dropna(inplace=True)
    return df


# -----------------
# METRICS
# -----------------
def max_drawdown(series):
    roll_max = series.cummax()
    dd = (series - roll_max) / roll_max
    return dd.min()

def sharpe_ratio(returns):
    if returns.std() == 0:
        return 0
    return np.sqrt(252) * returns.mean() / returns.std()

