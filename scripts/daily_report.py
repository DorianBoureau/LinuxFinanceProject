import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
TICKERS = ["AAPL", "MSFT", "GOOGL", "BTC-USD", "ETH-USD", "TSLA"]
LOOKBACK_PERIOD = "1y"  # Needed to calculate Volatility & Max Drawdown

def compute_max_drawdown(prices_series):
    """Calculates the max loss from a peak within the period."""
    cum_max = prices_series.cummax()
    drawdown = (prices_series - cum_max) / cum_max
    return drawdown.min()

def generate_report():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Starting report generation for {today}...")

    # 1. Fetch Data (Silent mode)
    # We download 1 year of history to compute meaningful risk metrics
    try:
        data = yf.download(TICKERS, period=LOOKBACK_PERIOD, group_by='ticker', auto_adjust=True, progress=False)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    report_lines = []
    report_lines.append(f"=== DAILY MARKET REPORT: {today} ===\n")
    report_lines.append(f"{'ASSET':<10} {'CLOSE':<10} {'DAY VAR':<10} {'VOL (1Y)':<10} {'MAX DD':<10}")
    report_lines.append("-" * 60)

    # 2. Process each ticker
    for ticker in TICKERS:
        try:
            # Handle single vs multi-index structure from yfinance
            df = data[ticker] if len(TICKERS) > 1 else data

            # Extract latest data points
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]

            # Metrics Calculation
            daily_return = (current_price - prev_price) / prev_price

            # Annualized Volatility (Standard Deviation of returns * sqrt(252))
            daily_rets = df['Close'].pct_change().dropna()
            volatility = daily_rets.std() * np.sqrt(252)

            # Max Drawdown (1 Year)
            max_dd = compute_max_drawdown(df['Close'])

            # Formatting the line
            line = (
                f"{ticker:<10} "
                f"${current_price:<9.2f} "
                f"{daily_return:>+8.2%} "
                f"{volatility:>9.1%} "
                f"{max_dd:>9.1%}"
            )
            report_lines.append(line)

        except Exception as e:
            report_lines.append(f"{ticker:<10} Error: Insufficient data")

    report_lines.append("\n" + "-" * 60)
    report_lines.append("End of Report. Generated automatically.")

    # 3. Save to file
    # Ensure the 'reports' directory exists relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Go up one level
    report_dir = os.path.join(project_root, "reports")

    os.makedirs(report_dir, exist_ok=True)

    file_path = os.path.join(report_dir, f"report_{today}.txt")

    with open(file_path, "w") as f:
        f.write("\n".join(report_lines))

    print(f"Report saved successfully: {file_path}")

if __name__ == "__main__":
    generate_report()