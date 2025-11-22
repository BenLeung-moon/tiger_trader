from tigeropen.trade.trade_client import TradeClient
from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.common.consts import Market, SecurityType, Currency
import config
from utils import setup_loggers

trading_logger, error_logger = setup_loggers()

class OrderExecutor:
    def __init__(self):
        self.client_config = TigerOpenClientConfig()
        self.client_config.private_key = config.PRIVATE_KEY_CONTENT
        self.client_config.tiger_id = config.TIGER_ID
        self.client_config.account = config.TIGER_ACCOUNT
        
        try:
            self.trade_client = TradeClient(self.client_config)
        except Exception as e:
            error_logger.error(f"Error initializing TradeClient: {e}")
            self.trade_client = None

    def place_order(self, order_signal):
        """
        Executes the order based on the AI signal.
        Returns the order object/id if successful, None otherwise.
        """
        if not self.trade_client:
            error_logger.error("TradeClient is not initialized. Cannot place order.")
            trading_logger.info(f"Simulated Order: {order_signal}")
            return None

        action = order_signal.get('action', '').upper()
        symbol = order_signal.get('symbol')
        quantity = order_signal.get('quantity', 0)
        price = order_signal.get('price', 0)

        if action == 'HOLD':
            trading_logger.info(f"Action is HOLD for {symbol}. No order placed.")
            return None

        if quantity <= 0:
            error_logger.error(f"Quantity {quantity} is invalid. No order placed.")
            return None

        # Determine Market and Currency
        # Simple logic: US stocks usually 4 letters or less, HK stocks are numeric
        market = Market.US
        currency = Currency.USD
        if symbol.isdigit() and len(symbol) == 5:
            market = Market.HK
            currency = Currency.HKD
        
        # Construct Contract
        try:
            contract = self.trade_client.get_contracts(
                symbol=symbol, 
                sec_type=SecurityType.STK, 
                currency=currency
            )[0] # Assuming first match
        except Exception as e:
            error_logger.error(f"Error fetching contract for {symbol}: {e}")
            return None

        try:
            if price > 0:
                # Limit Order
                order = self.trade_client.create_order(
                    account=config.TIGER_ACCOUNT,
                    contract=contract,
                    action=action, # 'BUY' or 'SELL' string usually works, or map to ActionType
                    order_type='LMT',
                    quantity=quantity,
                    limit_price=price
                )
            else:
                # Market Order
                order = self.trade_client.create_order(
                    account=config.TIGER_ACCOUNT,
                    contract=contract,
                    action=action,
                    order_type='MKT',
                    quantity=quantity
                )
            
            # The return from create_order is usually an Order object or ID
            trading_logger.info(f"Order placed successfully! Order ID: {order.order_id if hasattr(order, 'order_id') else order}")
            self.trade_client.place_order(order)
            
            return order
            
        except Exception as e:
            error_logger.error(f"Failed to execute order: {e}")
            return None

    def get_order_status(self, order_id):
        """
        Checks the status of an order.
        """
        if not self.trade_client or not order_id:
            return None
            
        try:
            # fetch order status
            order = self.trade_client.get_order(account=config.TIGER_ACCOUNT, id=order_id)
            return order
        except Exception as e:
            error_logger.error(f"Error fetching order status: {e}")
            return None

    def get_open_orders(self):
        """
        Fetches all open (active) orders.
        """
        if not self.trade_client:
            return []
        try:
            orders = self.trade_client.get_open_orders(account=config.TIGER_ACCOUNT)
            return orders
        except Exception as e:
            error_logger.error(f"Error fetching open orders: {e}")
            return []

    def cancel_order(self, order_id):
        """
        Cancels an existing order.
        """
        if not self.trade_client or not order_id:
            return False
        try:
            self.trade_client.cancel_order(account=config.TIGER_ACCOUNT, id=order_id)
            trading_logger.info(f"Order {order_id} cancelled successfully.")
            return True
        except Exception as e:
            error_logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def modify_order(self, order_id, new_price=None, new_quantity=None):
        """
        Modifies an existing order (price or quantity).
        """
        if not self.trade_client or not order_id:
            return False
        try:
            # First get the order to ensure it exists and get current details
            order = self.get_order_status(order_id)
            if not order:
                return False
            
            if new_price:
                order.limit_price = new_price
            if new_quantity:
                order.quantity = new_quantity
                
            self.trade_client.modify_order(order)
            trading_logger.info(f"Order {order_id} modified successfully. Price: {new_price}, Qty: {new_quantity}")
            return True
        except Exception as e:
            error_logger.error(f"Error modifying order {order_id}: {e}")
            return False
