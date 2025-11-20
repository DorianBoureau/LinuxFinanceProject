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
    # Crypto case:
    if symbol.endswith("USDT") or symbol.endswith("USD"):
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            r = requests.get(url).json()
            return float(r["price"])
        except:
            pass
    
    # Other assets
    data = yf.Ticker(symbol).history(period="1d")
    return float(data["Close"].iloc[-1])


# -----------------
# HISTORICAL DATA
# -----------------
def load_historical_data(symbol):
    df = yf.download(symbol, period="2y")  # 2 years history
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

