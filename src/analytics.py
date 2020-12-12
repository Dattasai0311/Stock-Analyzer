import pandas as pd
from .database import StockDB
from tabulate import tabulate
import logging

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self, db_name="stocks.db"):
        # Keep DB access localized to the analyzer to simplify call sites.
        self.db = StockDB(db_name=db_name)

    def find_panic_selling_days(self, symbol, drop_threshold=0.05):
        df = self.db.get_data(symbol)
        
        if df.empty:
            logger.warning("No data found for %s. Skipping panic detection.", symbol)
            return pd.DataFrame()

        # Daily % change for threshold filtering; first row will be NaN.
        df['pct_change'] = df['close'].pct_change()
        
        panic_days = df[df['pct_change'] < -drop_threshold].copy()
        
        if panic_days.empty:
            logger.info("No panic days for %s at %.2f%%", symbol, drop_threshold * 100)
        else:
            logger.info("Panic days for %s: %s below %.2f%%", symbol, len(panic_days), drop_threshold * 100)
            logger.debug(
                "Panic days sample:\n%s",
                tabulate(panic_days[['close', 'pct_change']].tail(10), headers='keys', tablefmt='psql'),
            )
        return panic_days

    def calculate_moving_averages(self, symbol):
        df = self.db.get_data(symbol)

        if df.empty:
            logger.warning("No data found for %s. Skipping moving averages.", symbol)
            return None
        
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['SMA_200'] = df['close'].rolling(window=200).mean()
        
        latest = df.iloc[-1]

        # Classify the signal only when both SMAs are available.
        signal = "insufficient_data"
        if pd.notna(latest['SMA_50']) and pd.notna(latest['SMA_200']):
            signal = "golden_cross" if latest['SMA_50'] > latest['SMA_200'] else "death_cross"

        logger.info("Indicators %s: close=%.2f sma50=%.2f sma200=%.2f signal=%s",
                    symbol, latest['close'], latest['SMA_50'], latest['SMA_200'], signal)
        return {
            "as_of": latest.name,
            "close": float(latest['close']),
            "sma_50": float(latest['SMA_50']) if pd.notna(latest['SMA_50']) else None,
            "sma_200": float(latest['SMA_200']) if pd.notna(latest['SMA_200']) else None,
            "signal": signal,
        }
