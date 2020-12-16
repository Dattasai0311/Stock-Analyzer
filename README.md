# Stock Analyzer (SQLite + CLI)

This is a small side project I used to keep around for quick, offline analysis of daily stock data. It pulls historical prices, stores them in SQLite, and runs a couple of simple checks I actually look at (panic selling days and moving-average signals). It’s intentionally CLI‑first and small enough to tinker with.

## Features
- ETL pipeline using Yahoo Finance data via `yfinance`
- SQLite storage with normalized tables for tickers and daily prices
- Panic selling detection (configurable drop threshold)
- 50-day and 200-day SMA calculation with signal classification
- Configurable via CLI flags or environment variables

## Tech Stack
- Python 3.8+
- SQLite
- Pandas
- yfinance
- tabulate

## Installation
```bash
git clone https://github.com/yourusername/stock-analyzer.git
cd stock-analyzer
pip install -r requirements.txt
```

## Usage
Run ingestion + analysis:
```bash
python main.py --tickers AAPL MSFT --start-date 2021-01-01 --end-date 2021-12-31
```

The report output is on by default:
```bash
python main.py --tickers AAPL MSFT --start-date 2021-01-01 --end-date 2021-12-31
```

Disable the report and keep logs at INFO:
```bash
python main.py --tickers AAPL MSFT --start-date 2021-01-01 --end-date 2021-12-31 --log-level INFO --no-report
```

## Configuration
The app reads settings from environment variables too:
- `STOCK_TICKERS` (comma-separated list, e.g. `AAPL,MSFT`)
- `START_DATE` (YYYY-MM-DD)
- `END_DATE` (YYYY-MM-DD)
- `DB_PATH` (SQLite file path)
- `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR)

CLI flags take precedence over environment variables.

## Potential Improvements
- Live data feed (e.g., WebSocket providers like Alpaca or Polygon.io)
- More indicators (RSI, Bollinger Bands, VWAP)
- Backtesting engine with basic P&L tracking
- Containerization for reproducible runs (Docker)
- Simple dashboard (Streamlit or lightweight web UI)
