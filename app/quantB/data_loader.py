import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=24*3600)  # Cache data for 24h to speed up user experience
def load_market_data(tickers, start_date, end_date):
    """
    Downloads data for multiple tickers at once.
    Handles yfinance MultiIndex formatting issues automatically.
    """
    if not tickers:
        return None

    try:
        # Bulk download is faster than looping
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=True)
    except Exception as e:
        st.error(f"Critical error during download: {e}")
        return None

    # Handle the single ticker edge-case (yfinance returns different structure)
    if len(tickers) == 1:
        ticker = tickers[0]
        # Force MultiIndex structure to match the multi-asset logic
        data.columns = pd.MultiIndex.from_product([[ticker], data.columns])

    close_prices = pd.DataFrame()

    for ticker in tickers:
        try:
            # We only need the 'Close' price for this module
            if (ticker, 'Close') in data.columns:
                close_prices[ticker] = data[(ticker, 'Close')]
            elif 'Close' in data.columns and len(tickers) == 1:
                close_prices[ticker] = data['Close']
        except KeyError:
            st.warning(f"Data not found for {ticker}")

    # Clean missing values: forward fill first, then drop leading NaNs
    close_prices = close_prices.ffill().dropna()

    return close_prices

def get_returns(prices_df):
    """
    Computes simple arithmetic returns (pct_change).
    """
    return prices_df.pct_change().dropna()