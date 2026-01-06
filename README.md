# LinuxFinanceProject


Single Asset Quantitative Analysis Module
-----------------------------------------

This project provides an interactive Streamlit application for analyzing the performance
of a single financial asset using quantitative methods. It includes historical data
visualization, trading strategy backtesting, real-time price integration, and performance
metrics.

1. Supported Assets
-------------------

The module allows the user to analyze several assets, including:

- BTC-USD
- AAPL
- EURUSD=X
- GC=F

Data is retrieved using:

- get_realtime_price()        → retrieves the current price (with fallback)
- load_historical_data(asset) → loads historical market data

2. Timeframe System
-------------------

The user can select a timeframe. Each timeframe corresponds to the last N rows of data:

- 1D  → last 3 rows  
- 1W  → last 7 rows  
- 1M  → last 30 rows  
- 3M  → last 90 rows  
- 1Y  → last 365 rows  
- 5Y  → last 1825 rows  
- MAX → entire dataset

This system ensures that calculations, charts, and indicators work reliably.


3. Trading Strategies
---------------------

The module includes three quantitative trading strategies.

3.1 Buy & Hold
--------------
- Buy once at the start and hold permanently
- Always fully exposed to the market
- Strategy curve = normalized price

Pros:
- Simple, stable over long periods

Cons:
- Large drawdowns
- No risk control

3.2 Momentum Strategy
----------------------
- Long position when price > price X days ago
- Otherwise stay in cash
- User-defined parameter: window

Pros:
- Strong in trending markets

Cons:
- Weak in sideways markets

3.3 Moving Average Crossover
-----------------------------
- Long position when fast moving average > slow moving average
- Otherwise stay in cash
- User-defined parameters: fast, slow

Pros:
- Trend following, noise filtering

Cons:
- Delayed entries, frequent whipsaws


4. Interactive Chart (Plotly)
------------------------------

The chart displays:
- The asset price curve
- The cumulative return curve of the selected strategy

Features:
- Full zooming and panning
- Range slider
- Unified hover mode
- Dark theme
- Clean and responsive display


5. Performance Metrics
----------------------

The module automatically computes:

- Maximum Drawdown
- Sharpe Ratio
- Annualized Volatility

These metrics allow evaluating the risk and efficiency of each strategy.


6. Information Panel
---------------------

This panel displays:

- Start date of the dataset
- End date of the dataset
- Lowest price
- Highest price
- Current price
- Total performance since the beginning of the selected timeframe


7. Strategy Description Panel
------------------------------

This panel explains in detail:

- The concept behind each strategy
- Entry and exit rules
- Pros and cons
- Values of user-selected parameters


8. Project Structure
---------------------

LinuxFinanceProject/
│
├── app/
│   ├── main.py
│   ├── single_asset.py
│   ├── utils.py
│   ├── config.py
│
├── data/
├── scripts/
├── requirements.txt
├── README.md


9. Summary
-----------

This module provides a complete environment for:

- Quantitative backtesting
- Visualization of historical asset data
- Comparison of trading strategies
- Real-time and historical price integration

It is designed to be simple, modular, and extensible for further financial research
and development.


