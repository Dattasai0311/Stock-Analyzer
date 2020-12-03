import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    tickers: list[str]
    start_date: str
    end_date: str
    db_path: str
    log_level: str

def load_settings() -> Settings:
    # Use env vars when present; avoid guessing tickers/dates by default.
    tickers_raw = os.getenv("STOCK_TICKERS", "")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    return Settings(
        tickers=tickers,
        start_date=os.getenv("START_DATE", ""),
        end_date=os.getenv("END_DATE", ""),
        db_path=os.getenv("DB_PATH", "stocks.db"),
        log_level=os.getenv("LOG_LEVEL", "ERROR").upper(),
    )
