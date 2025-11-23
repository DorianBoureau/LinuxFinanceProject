import pandas as pd
import yfinance as yf
import streamlit as st

def load_single_asset(asset, start, end):
    """
    Charge un seul asset via yfinance (compatible avec ton Quant A).
    Retourne un DataFrame contenant uniquement la colonne 'Close'.
    """
    try:
        data = yf.download(asset, start=start, end=end, progress=False)
        if data.empty:
            st.warning(f"Aucune donnée trouvée pour {asset}")
            return None
        data = data[['Close']]
        data.rename(columns={'Close': asset}, inplace=True)
        return data
    except Exception as e:
        st.error(f"Erreur lors du chargement de {asset} : {e}")
        return None


def load_multiple_assets(asset_list, start, end):
    """
    Charge plusieurs actifs et fusionne leurs prix de clôture dans un seul DataFrame.
    """
    merged_df = pd.DataFrame()

    for asset in asset_list:
        df = load_single_asset(asset, start, end)
        if df is None:
            continue

        if merged_df.empty:
            merged_df = df
        else:
            merged_df = merged_df.join(df, how="outer")

    merged_df.dropna(inplace=True)

    return merged_df


def get_returns(price_df):
    """
    Transforme les prix en rendements journaliers.
    """
    return price_df.pct_change().dropna()
