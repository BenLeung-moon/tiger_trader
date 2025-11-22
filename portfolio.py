from tigeropen.trade.trade_client import TradeClient
from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.common.util.signature_utils import read_private_key
import config
from utils import setup_loggers

trading_logger, error_logger = setup_loggers()

class PortfolioManager:
    def __init__(self):
        self.client_config = TigerOpenClientConfig()
        self.client_config.private_key = config.PRIVATE_KEY_CONTENT
        self.client_config.tiger_id = config.TIGER_ID
        self.client_config.account = config.TIGER_ACCOUNT
        self.client_config.token = config.TIGER_TOKEN
        
        try:
            self.trade_client = TradeClient(self.client_config)
        except Exception as e:
            error_logger.error(f"Error initializing TradeClient for Portfolio: {e}")
            self.trade_client = None

    def get_all_positions(self):
        """
        Fetches all current positions for the account.
        Returns a list of dictionaries with position details.
        """
        if not self.trade_client:
            return []

        try:
            # Fetch all positions (omit symbol)
            positions = self.trade_client.get_positions(
                account=config.TIGER_ACCOUNT, 
                sec_type='STK'
            )
            
            formatted_positions = []
            if positions:
                for pos in positions:
                    formatted_positions.append({
                        "symbol": pos.contract.symbol,
                        "quantity": pos.quantity,
                        "average_cost": pos.average_cost,
                        "market_price": pos.market_price,
                        "unrealized_pnl": pos.unrealized_pnl,
                        "market_value": pos.market_value
                    })
            return formatted_positions
        except Exception as e:
            error_logger.error(f"Error fetching all positions: {e}")
            return []

    def get_position(self, symbol):
        """
        Fetches the current position for a given symbol.
        Returns a dictionary with position details or None if not found.
        """
        if not self.trade_client:
            return None

        try:
            # Fetch positions for the account
            positions = self.trade_client.get_positions(
                account=config.TIGER_ACCOUNT, 
                sec_type='STK', 
                symbol=symbol
            )
            
            if positions:
                # Assuming we get a list of positions matching the symbol
                # We return the first one (usually unique per symbol/account)
                pos = positions[0]
                return {
                    "symbol": pos.contract.symbol,
                    "quantity": pos.quantity,
                    "average_cost": pos.average_cost,
                    "market_price": pos.market_price,
                    "unrealized_pnl": pos.unrealized_pnl
                }
            return None
        except Exception as e:
            error_logger.error(f"Error fetching position for {symbol}: {e}")
            return None

    def get_account_funds(self):
        """
        Fetches account funds, specifically available cash for trade in different currencies.
        Returns a dictionary: {'USD': {'cash_available_for_trade': 1000.0, ...}, 'HKD': ...}
        """
        if not self.trade_client:
            return {}
        
        try:
            # get_prime_assets returns a list of PortfolioAccount objects
            assets = self.trade_client.get_prime_assets(account=config.TIGER_ACCOUNT)
            funds = {}
            if assets:
                # assets might be a list or a single PortfolioAccount object depending on SDK version
                if isinstance(assets, list):
                    account_asset = assets[0]
                else:
                    account_asset = assets

                # We are interested in Securities segment ('S') for stocks
                # The attribute name in the SDK might be 'segments' which is a dict
                if hasattr(account_asset, 'segments') and 'S' in account_asset.segments:
                    segment = account_asset.segments['S']
                    if hasattr(segment, 'currency_assets'):
                        for currency, asset in segment.currency_assets.items():
                            # Extract relevant cash info
                            # Check attributes existence to be safe
                            cash_avail = getattr(asset, 'cash_available_for_trade', 0.0)
                            cash_balance = getattr(asset, 'cash_balance', 0.0)
                            buying_power = getattr(asset, 'buying_power', 0.0)
                            
                            funds[currency] = {
                                "available_for_trade": cash_avail,
                                "cash_balance": cash_balance,
                                "buying_power": buying_power
                            }
            return funds
        except Exception as e:
            error_logger.error(f"Error fetching account funds: {e}")
            return {}
