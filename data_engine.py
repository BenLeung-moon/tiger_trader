import pandas as pd
import pandas_ta as ta
from tigeropen.common.consts import BarPeriod, Market
from tigeropen.quote.quote_client import QuoteClient
from tigeropen.tiger_open_config import TigerOpenClientConfig
import config
from utils import setup_loggers

trading_logger, error_logger = setup_loggers()

class DataEngine:
    def __init__(self):
        self.client_config = TigerOpenClientConfig()
        self.client_config.private_key = config.PRIVATE_KEY_CONTENT
        self.client_config.tiger_id = config.TIGER_ID
        self.client_config.account = config.TIGER_ACCOUNT
        self.client_config.token = config.TIGER_TOKEN
        
        # Initialize QuoteClient
        try:
            self.quote_client = QuoteClient(self.client_config)
        except Exception as e:
            error_logger.error(f"Error initializing QuoteClient: {e}")
            self.quote_client = None

    def get_historical_data(self, symbol, period=BarPeriod.DAY, limit=100):
        """
        Fetch historical K-line data.
        """
        if not self.quote_client:
            error_logger.warning("QuoteClient not initialized.")
            return pd.DataFrame()

        try:
            # period can be 'day', 'min', etc.
            # Using 'day' as default from BarPeriod.DAY
            bars = self.quote_client.get_bars(symbols=[symbol], period=period, limit=limit)
            if bars.empty:
                return pd.DataFrame()
            return bars
        except Exception as e:
            error_logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_fundamental_data(self, symbol):
        """
        Fetch basic fundamental data (Financial ratios).
        """
        if not self.quote_client:
            return {}
        
        try:
            # Fetch financial ratios like PE, PB, Market Cap
            # Note: The specific method depends on the SDK version, usually get_financial_daily or get_stock_briefs
            # Using get_stock_briefs as a generic way to get some data if financial specific is complex
            briefs = self.quote_client.get_stock_briefs(symbols=[symbol])
            if not briefs.empty:
                # Convert first row to dict
                return briefs.iloc[0].to_dict()
            return {}
        except Exception as e:
            error_logger.error(f"Error fetching fundamental data for {symbol}: {e}")
            return {}

    def get_realtime_price(self, symbol):
        """
        Fetch the latest real-time price for a symbol.
        """
        if not self.quote_client:
            return None
            
        try:
            briefs = self.quote_client.get_stock_briefs(symbols=[symbol])
            if not briefs.empty and 'latest_price' in briefs.columns:
                return briefs.iloc[0]['latest_price']
            elif not briefs.empty and 'price' in briefs.columns:
                return briefs.iloc[0]['price']
            return None
        except Exception as e:
            error_logger.error(f"Error fetching real-time price for {symbol}: {e}")
            return None

    def check_market_status(self, market):
        """
        Check if the given market is open.
        Returns (bool, str) - (is_open, status_description)
        """
        if not self.quote_client:
            return False, "QuoteClient not initialized"

        try:
            # get_market_status returns a list of MarketStatus objects
            statuses = self.quote_client.get_market_status(market=market)
            if statuses:
                status = statuses[0] 
                # We consider TRADING as open.
                is_open = status.status.upper() == 'TRADING'
                return is_open, status.status
            return False, "Unknown"
        except Exception as e:
            error_logger.error(f"Error checking market status for {market}: {e}")
            return False, str(e)

    def add_technical_indicators(self, df):
        """
        Add technical indicators to the DataFrame using pandas_ta.
        """
        if df.empty:
            return df

        # Ensure column names match what pandas_ta expects (Open, High, Low, Close, Volume)
        # Tiger SDK usually returns: symbol, time, open, high, low, close, volume
        # We might need to rename columns if they are capitalized differently.
        # Standardizing to lowercase for pandas_ta (it usually handles case, but good to be safe)
        df.columns = [c.lower() for c in df.columns]
        
        # RSI
        df.ta.rsi(length=14, append=True)
        
        # MACD
        df.ta.macd(append=True)
        
        # SMA
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        
        # Bollinger Bands
        df.ta.bbands(length=20, append=True)

        # Fill NaN values that result from indicator calculations
        # Fix FutureWarning: Downcasting object dtype arrays on .fillna is deprecated
        with pd.option_context('future.no_silent_downcasting', True):
            df = df.fillna(0).infer_objects(copy=False)
        
        return df
