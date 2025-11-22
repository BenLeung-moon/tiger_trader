import time
import os
import logging
from collections import deque

def setup_loggers():
    """
    Sets up two loggers: one for trading history and one for errors.
    Returns (trading_logger, error_logger).
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Trading Logger
    trading_logger = logging.getLogger('trading_logger')
    trading_logger.setLevel(logging.INFO)
    # Prevent adding multiple handlers if setup is called multiple times
    if not trading_logger.handlers:
        trading_handler = logging.FileHandler('logs/trading.log')
        trading_handler.setFormatter(formatter)
        trading_logger.addHandler(trading_handler)
        # Also output to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        trading_logger.addHandler(console_handler)

    # Error Logger
    error_logger = logging.getLogger('error_logger')
    error_logger.setLevel(logging.ERROR)
    if not error_logger.handlers:
        error_handler = logging.FileHandler('logs/errors.log')
        error_handler.setFormatter(formatter)
        error_logger.addHandler(error_handler)
        # Also output to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        error_logger.addHandler(console_handler)

    return trading_logger, error_logger

def setup_position_logger():
    """
    Sets up a logger specifically for recording account positions.
    Returns position_logger.
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Formatter - simpler format for positions
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    
    position_logger = logging.getLogger('position_logger')
    position_logger.setLevel(logging.INFO)
    
    if not position_logger.handlers:
        handler = logging.FileHandler('logs/positions.log')
        handler.setFormatter(formatter)
        position_logger.addHandler(handler)
    
    return position_logger

class RateLimiter:
    def __init__(self, max_calls, period_seconds):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.timestamps = deque()

    def can_proceed(self):
        """
        Checks if a new action is allowed.
        Returns True if allowed, False otherwise.
        """
        current_time = time.time()
        
        # Remove timestamps older than the period
        while self.timestamps and self.timestamps[0] <= current_time - self.period_seconds:
            self.timestamps.popleft()

        if len(self.timestamps) < self.max_calls:
            self.timestamps.append(current_time)
            return True
        
        return False

    def wait_for_slot(self):
        """
        Blocks execution until a slot is available.
        """
        while not self.can_proceed():
            # Calculate time to wait for the oldest timestamp to expire
            if self.timestamps:
                wait_time = (self.timestamps[0] + self.period_seconds) - time.time()
                if wait_time > 0:
                    time.sleep(wait_time)

def round_price_to_tick(price, is_hk=False):
    """
    Rounds the price to the nearest valid tick size.
    Supports HKEX tick rules and standard US 0.01 tick.
    """
    if not is_hk:
        # US Stocks usually 0.01
        return round(price, 2)

    # HKEX Tick Rules (Simplified Part A)
    if price < 0.25:
        tick = 0.001
    elif price < 0.50:
        tick = 0.005
    elif price < 10.00:
        tick = 0.01
    elif price < 20.00:
        tick = 0.02
    elif price < 100.00:
        tick = 0.05
    elif price < 200.00:
        tick = 0.10
    elif price < 500.00:
        tick = 0.20
    elif price < 1000.00:
        tick = 0.50
    elif price < 2000.00:
        tick = 1.00
    elif price < 5000.00:
        tick = 2.00
    else:
        tick = 5.00
        
    # Round to nearest tick
    return round(round(price / tick) * tick, 3)
