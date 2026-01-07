import requests
import pandas as pd
import numpy as np
import yfinance as yf


# ============================================================
# REAL-TIME PRICE — ultra robuste
# ============================================================

def get_realtime_price(symbol):
    """
    Ordre de priorité :
      1. Yahoo Finance (fiable pour tout)
      2. Binance (si symbol USDT)
    """

    # ---- Yahoo Finance
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
    except:
        pass

    # ---- Crypto Binance
    if symbol.endswith("USDT"):
        try:
            r = requests.get(
                f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}",
                timeout=5
            ).json()
            if "price" in r:
                return float(r["price"])
        except:
            pass

    return None

# ============================================================
# HISTORICAL DATA — version PRO, zéro bug
# ============================================================

def load_historical_data(symbol):
    """
    Source principale : Yahoo Finance
    => Données complètes, propres, MAX range
    """

    try:
        df = yf.download(symbol, period="max", interval="1d", progress=False)
        if not df.empty:
            df = df.rename(columns={"Close": "price"})[["price"]].dropna()
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            return df
    except:
        pass

    return pd.DataFrame(columns=["price"])


# ============================================================
# METRICS
# ============================================================

def max_drawdown(series):
    ser = pd.Series(series).dropna()
    roll = ser.cummax()
    dd = (ser - roll) / roll
    return float(dd.min())


def sharpe_ratio(returns):
    ret = pd.Series(returns).dropna()
    if len(ret) < 2:
        return 0.0

    std = ret.std()
    if std == 0 or pd.isna(std):
        return 0.0

    return float(np.sqrt(252) * ret.mean() / std)
