# 📈 Financial Engineering Dashboard (Quant A & B)

A professional-grade dashboard for real-time asset analysis and multi-asset portfolio simulation.
Deployed on a **Linux Cloud VM (Azure)** and automated with **Cron** jobs.

---

## 📖 Project Overview

This project provides a complete environment for quantitative finance, split into two core modules:

1.  **Quant A (Single Asset):** Technical analysis, backtesting strategies, and real-time monitoring.
2.  **Quant B (Portfolio Management):** Asset allocation, rebalancing simulation, and risk management (VaR, CVaR).

**Tech Stack:** Python, Streamlit, Plotly, yfinance, Pandas, Linux (Ubuntu), Bash.

---

## 🚀 Key Features

### 🔹 Module A: Single Asset Analysis

_Designed for in-depth analysis of individual instruments (Stocks, Forex, Crypto)._

- **Supported Assets:** Pre-configured list (BTC-USD, AAPL, EURUSD=X, GC=F) + dynamic fetching.
- **Timeframe System:** Flexible analysis periods (1D, 1W, 1M, 3M, 1Y, 5Y, MAX).
- **Algorithmic Strategies:**
  - _Buy & Hold:_ Benchmark strategy.
  - _Momentum:_ Trend following based on rolling windows.
  - _Moving Average Crossover:_ Classic signal generation (Fast vs Slow MA).
- **Metrics:** Sharpe Ratio, Max Drawdown, Annualized Volatility.

### 🔹 Module B: Portfolio Management

_Designed for asset allocation and risk parity simulation._

- **Dynamic Inputs:** Users can input _any_ ticker available on Yahoo Finance (e.g., `LVMH.PA`, `ETH-USD`).
- **Allocation Engines:**
  - _Equal Weight (1/N)_
  - _Inverse Volatility (Risk Parity)_: Allocates less capital to volatile assets.
  - _Custom Weights_: Manual user-defined allocation.
- **Advanced Simulation:** Handles **Drift** (price evolution between rebalancing dates) and **Rebalancing Frequencies** (Monthly, Weekly, Buy & Hold).
- **Pro Risk Metrics:** Value at Risk (VaR 95%), Expected Shortfall (CVaR), Sortino Ratio, and **Diversification Benefit**.
- **Visualizations:** Correlation Matrix (Heatmap), Underwater Plot (Drawdown), and Performance Comparison.

---

## 🛠️ System Architecture & Automation

This project is not just a local script; it is deployed as a production-like service.

### 1. Daily Reporting (Cron Job)

A background script automatically generates a financial report (Volatility, Returns, Drawdown) every day at **8:00 PM**.

- **Script:** `scripts/daily_report.py` (Headless execution, no GUI).
- **Cron Configuration (on VM):**
  ```bash
  0 20 * * * /home/azureuser/LinuxFinanceProject/venv/bin/python /home/azureuser/LinuxFinanceProject/scripts/daily_report.py >> /home/azureuser/LinuxFinanceProject/cron_log.txt 2>&1
  ```

### 2. 24/7 Availability (Systemd)

The dashboard runs continuously using a Linux Service, ensuring it restarts automatically after server reboots or crashes.

- **Service File:** `/etc/systemd/system/finance-app.service`

  ```ini
  [Unit]
  Description=Streamlit Finance Dashboard
  After=network.target

  [Service]
  User=azureuser
  WorkingDirectory=/home/azureuser/LinuxFinanceProject
  ExecStart=/home/azureuser/LinuxFinanceProject/venv/bin/streamlit run app/main.py --server.port 8501
  Restart=always

  [Install]
  WantedBy=multi-user.target
  ```

---

## 📂 Project Structure

```text
LinuxFinanceProject/
│
├── app/                        # Main Application Code
│   ├── main.py                 # Entry point (Tabs & Auto-refresh logic)
│   │
│   ├── quantA/                 # Quant A Package
│   │   ├── config.py               # Initial Configuration
│   │   ├── single_asset.py         # Quant A Logic
│   │   └── utils.py                # Shared utilities
│   │
│   └── quantB/                 # Quant B Package
│       ├── dashboard.py        # UI & Interaction
│       ├── data_loader.py      # Bulk Data Fetching & Caching
│       ├── metrics.py          # Financial Math (VaR, Sortino, Div Effect)
│       └── portfolio_engine.py # Backtesting Core (Drift & Rebalancing)
│
├── scripts/                    # Backend automation scripts
│   └── daily_report.py         # Cron-triggered reporting script
│
├── .gitignore                  # Ignore files when committing changes
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

---

## ⚙️ Installation & Usage

### Local Setup

1.  Clone the repository:
    ```bash
    git clone [https://github.com/DorianBoureau/LinuxFinanceProject.git](https://github.com/DorianBoureau/LinuxFinanceProject.git)
    cd LinuxFinanceProject
    ```
2.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # (On Windows: venv\Scripts\activate)
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the application:
    ```bash
    streamlit run app/main.py
    ```

### Accessing the Live VM

The application is hosted on an Azure Virtual Machine.

- **URL:** `http://4.235.121.158:8501`
- _Note: Ensure port 8501 is allowed in Azure Networking settings._

---

## 👥 Authors

- **Teofil BEJOT** - Quant A Module (Single Asset)
- **Dorian BOUREAU** - Quant B Module (Portfolio & Infrastructure)

_Project carried out as part of the Master in Financial Engineering._

```

```
