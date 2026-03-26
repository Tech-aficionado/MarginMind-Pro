# -----------------------------------------------------------------------------
# Module: bot.orders
# Description: Trading execution logic and persistent logging functionality.
# Author: PrimeTrade.ai Assessment
# -----------------------------------------------------------------------------

import logging
import datetime
import os
import time
from .client import BinanceClient

def place_order(client, symbol, side, order_type, quantity, price=None):
    """
    Executes a trade on Binance and logs the result.
    Includes persistent history tracking and 'Wait for Fill' synchronization.
    """
    logging.info(f"Initiating {side} {order_type} order: {quantity} {symbol}")
    
    try:
        # Calling our client to do the actual work.
        response = client.place_order(symbol, side, order_type, quantity, price)
        
        # Pulling out the important bits from the response.
        oid = response.get('orderId')
        status = response.get('status')
        eqty = response.get('executedQty')
        
        # --- Execution Synchronization (Polling for Fill) ---
        # MARKET orders on Testnet often stay "NEW" initially.
        # We poll for up to 5s to capture the final execution data.
        max_retries = 5
        while status == 'NEW' and max_retries > 0:
            time.sleep(1) # Wait a second for the engine to catch up.
            response = client.get_order_status(symbol, oid)
            status = response.get('status')
            eqty = response.get('executedQty')
            max_retries -= 1
            logging.info(f"Checking order {oid}... status is {status}")

        # Recalculate average price (Futures gives us avgPrice directly)
        avg = response.get('avgPrice', 'N/A')
            
        result_msg = f"Order {oid} is {status}. Average Price: {avg}"
        logging.info(result_msg)
        
        # --- Persistent Audit Logging ---
        # We use append mode ('a') to maintain a complete history of trades.
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        base_name = "market_order.log" if order_type == "MARKET" else "limit_order.log"
        filename = os.path.join(log_dir, base_name)
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        env_label = "TESTNET" if client.use_testnet else "MAINNET"
        market_label = f"[{env_label}][{client.market.upper()}]"
        
        # Using "a" to append for trade history tracking.
        with open(filename, "a") as f:
            f.write(f"\n--- Order Session {now} ---\n")
            f.write(f"{now} - INFO - {market_label} Placing {side} {order_type}: {quantity} {symbol} @ {price or 'MARKET'}\n")
            f.write(f"{now} - INFO - {market_label} Result: {result_msg}\n")
            
        logging.info(f"Audit results appended to {filename}")
        # -------------------------------------------------------------------------

        # Terminal summary output.
        print("-" * 30)
        print(f"SUCCESS! (Saved to {filename})")
        print(f"Order ID: {oid}")
        print(f"Status:   {status}")
        print(f"Executed: {eqty}")
        print(f"Avg Price: {avg}")
        print("-" * 30)
        
        return response

    except Exception as e:
        # Exception capture to prevent silent failures.
        logging.error(f"Order failed during execution: {e}")
        raise
