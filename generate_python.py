from utils import load_historical_data, max_drawdown, sharpe_ratio

df = load_historical_data("BTC-USD")
returns = df["price"].pct_change()

report = f"""
DAILY REPORT
============
Last Price: {df['price'].iloc[-1]:.2f}
Daily Return: {returns.iloc[-1]:.2%}
Volatility (Ann.): {returns.std() * (252**0.5):.2%}
Sharpe Ratio: {sharpe_ratio(returns):.2f}
Max Drawdown: {max_drawdown(df['price']):.2%}
"""

with open("data/daily_reports/report.txt", "w") as f:
    f.write(report)

print("Daily report generated.")
