# -----------------------------------------------------------------------------
# Module: bot.client
# Description: Core API Client for Binance Futures interaction.
# -----------------------------------------------------------------------------

import os
import time
import logging
from binance.client import Client

class BinanceClient:
    """
    Binance API Client specialized for Futures trading.
    Handles authentication, environment switching (Testnet/Mainnet), 
    and server-time synchronization.
    """
    def __init__(self, key, secret):
        """
        Initialize the Binance Client and establish connection.
        
        Args:
            key (str): Binance API Key.
            secret (str): Binance API Secret.
        """
        self.key = key
        self.secret = secret
        self.market = "FUTURES" # Unified for this assignment
        
        # Load environment configuration from .env
        self.use_testnet = os.getenv("BINANCE_USE_TESTNET", "True").lower() == "true"
        
        try:
            # Initialize the underlying python-binance client
            self.client = Client(key, secret, testnet=self.use_testnet)
            
            # --- Server Time Synchronization (Fix for APIError -1021) ---
            # Calculates the offset between local system time and Binance server time.
            # This is critical for preventing 'recvWindow' rejected requests.
            serv_time = self.client.futures_time()
            local_time = int(time.time() * 1000)
            self.client.timestamp_offset = serv_time['serverTime'] - local_time
            
            # Connection Verification: Attempt to fetch account details.
            self.client.futures_account()
            env_name = "Futures Testnet" if self.use_testnet else "Futures Mainnet"
            print(f"Connection Status: [SUCCESS] Verified connection to {env_name}.")
            
        except Exception as e:
            # Graceful error handling for authentication or connectivity failures.
            logging.error(f"Failed to connect to Binance ({'Testnet' if self.use_testnet else 'Mainnet'}): {e}")
            raise

    def get_order_status(self, symbol, order_id):
        """
        Fetch current status of a specific order.
        Used for tracking fills and execution prices.
        """
        try:
            return self.client.futures_get_order(symbol=symbol, orderId=order_id)
        except Exception as e:
            logging.error(f"Failed to retrieve status for order {order_id}: {e}")
            raise

    def place_order(self, symbol, side, type, qty, price=None):
        """
        Place a new order on the Binance Futures exchange.
        
        Args:
            symbol (str): Trading pair (e.g., BTCUSDT).
            side (str): BUY or SELL.
            type (str): MARKET or LIMIT.
            qty (float): Order quantity.
            price (float, optional): Limit price (required for LIMIT orders).
        """
        args = {
            'symbol': symbol,
            'side': side,
            'type': type,
            'quantity': qty,
        }

        if type == 'LIMIT':
            args['price'] = str(price)
            args['timeInForce'] = 'GTC' # Standard "Good Till Cancelled" policy

        logging.info(f"Dispatching {side} {type} order: {qty} {symbol}")
        
        try:
            # Using the specialized futures_create_order method for the task.
            res = self.client.futures_create_order(**args)
            return res
        except Exception as e:
            logging.error(f"Execution Error: Binance API rejected the order: {e}")
            raise
