import sqlite3
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class StockDB:
    def __init__(self, db_name="stocks.db"):
        # Create a single connection per instance; callers should reuse this object.
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Keep schema creation idempotent so repeated runs don't blow up.
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                company_name TEXT
            );
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker_id INTEGER,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                FOREIGN KEY (ticker_id) REFERENCES tickers (id),
                UNIQUE(ticker_id, date)
            );
        """)
        self.conn.commit()

    def save_price_data(self, symbol, df):
        # Resolve ticker ID once per batch; this avoids repeated lookups per row.
        self.cursor.execute("INSERT OR IGNORE INTO tickers (symbol) VALUES (?)", (symbol,))
        self.cursor.execute("SELECT id FROM tickers WHERE symbol = ?", (symbol,))
        result = self.cursor.fetchone()
        if result:
            ticker_id = result[0]
        else:
            return
        
        self.conn.commit()

        # Convert dataframe rows into plain Python types for sqlite3.
        if isinstance(df.columns, pd.MultiIndex):
            if symbol in df.columns.get_level_values(-1):
                df = df.xs(symbol, axis=1, level=-1, drop_level=True)
            else:
                df = df.droplevel(-1, axis=1)
        def _scalar(value):
            return value.iloc[0] if isinstance(value, pd.Series) else value
        records = []
        for index, row in df.iterrows():
            date_str = index.strftime('%Y-%m-%d')
            
            try:
                open_price = float(_scalar(row['Open']))
                high_price = float(_scalar(row['High']))
                low_price = float(_scalar(row['Low']))
                close_price = float(_scalar(row['Close']))
                volume = int(_scalar(row['Volume']))
            except ValueError:
                continue

            records.append((
                ticker_id, 
                date_str, 
                open_price, 
                high_price, 
                low_price, 
                close_price, 
                volume
            ))

        if records:
            # Bulk insert for performance and fewer transactions.
            self.cursor.executemany("""
                INSERT OR IGNORE INTO daily_prices 
                (ticker_id, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, records)
            self.conn.commit()
            logger.info("Saved %s records for %s", len(records), symbol)
        else:
            logger.warning("No valid records to save for %s", symbol)

    def get_data(self, symbol):
        query = """
            SELECT d.date, d.close, d.volume 
            FROM daily_prices d
            JOIN tickers t ON d.ticker_id = t.id
            WHERE t.symbol = ?
            ORDER BY d.date ASC
        """
        return pd.read_sql_query(query, self.conn, params=(symbol,), index_col='date')
