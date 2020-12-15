import argparse
import logging
from src.ingest import fetch_and_store_data
from src.analytics import MarketAnalyzer
from src.config import load_settings
from tabulate import tabulate

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="*", help="Ticker symbols")
    parser.add_argument("--start-date", help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", help="End date YYYY-MM-DD")
    parser.add_argument("--db", help="SQLite DB path")
    parser.add_argument("--log-level", help="Log level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--drop-threshold", type=float, default=None, help="Panic drop threshold (0.05 = 5%%)")
    parser.add_argument("--no-report", action="store_true", help="Disable the human-friendly report")
    return parser.parse_args()

def configure_logging(level):
    # Consistent CLI-friendly logs with timestamps and module names.
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

def main():
    args = parse_args()
    settings = load_settings()

    # CLI overrides env values when provided.
    tickers = args.tickers or settings.tickers
    start_date = args.start_date or settings.start_date
    end_date = args.end_date or settings.end_date
    db_path = args.db or settings.db_path
    log_level = (args.log_level or settings.log_level).upper()
    drop_threshold = args.drop_threshold if args.drop_threshold is not None else 0.05

    configure_logging(log_level)

    if not tickers:
        raise SystemExit("No tickers provided. Use --tickers or set STOCK_TICKERS.")
    if not start_date or not end_date:
        raise SystemExit("Start/end dates required. Use --start-date/--end-date or set START_DATE/END_DATE.")

    # Ingest before analysis to ensure DB is populated for this run.
    fetch_and_store_data(tickers, start_date=start_date, end_date=end_date, db_name=db_path)

    analyzer = MarketAnalyzer(db_name=db_path)

    report_sections = []
    for stock in tickers:
        panic_days = analyzer.find_panic_selling_days(stock, drop_threshold=drop_threshold)
        indicators = analyzer.calculate_moving_averages(stock)
        if not args.no_report:
            report_sections.append((stock, panic_days, indicators))

    if not args.no_report:
        # Lightweight report output with tables.
        print("\nMarket report")
        print(f"Range: {start_date} to {end_date}")
        print(f"Tickers: {', '.join(tickers)}")
        for stock, panic_days, indicators in report_sections:
            print(f"\n{stock}")
            if indicators:
                indicator_rows = [[
                    indicators["as_of"],
                    f"{indicators['close']:.2f}",
                    f"{indicators['sma_50']:.2f}" if indicators["sma_50"] is not None else "n/a",
                    f"{indicators['sma_200']:.2f}" if indicators["sma_200"] is not None else "n/a",
                    indicators["signal"],
                ]]
                print("Indicators")
                print(tabulate(
                    indicator_rows,
                    headers=["as_of", "close", "sma_50", "sma_200", "signal"],
                    tablefmt="psql",
                ))
            else:
                print("Indicators")
                print("No data available.")

            print("\nPanic days")
            if panic_days is not None and not panic_days.empty:
                display = panic_days[['close', 'pct_change']].copy()
                display['pct_change'] = (display['pct_change'] * 100).round(2).astype(str) + "%"
                print(tabulate(display, headers=["date", "close", "pct_change"], tablefmt="psql"))
            else:
                print("None.")

if __name__ == "__main__":
    main()
