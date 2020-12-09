import yfinance as yf
from .database import StockDB
import logging

logger = logging.getLogger(__name__)

def fetch_and_store_data(tickers, start_date, end_date, db_name="stocks.db"):
    # Single DB connection for the ingest run; avoids reconnecting per ticker.
    db = StockDB(db_name=db_name)
    
    logger.info("Fetching data from %s to %s", start_date, end_date)
    
    for symbol in tickers:
        # Pull daily OHLCV data; yfinance handles date bounds.
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if not data.empty:
            db.save_price_data(symbol, data)
        else:
            logger.warning("No data found for %s", symbol)

    logger.info("Ingestion complete")
