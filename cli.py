# -----------------------------------------------------------------------------
# Module: cli
# Description: Command-Line Interface for the Binance Futures Bot.
# -----------------------------------------------------------------------------

import argparse
import os
import logging
from bot.logging_config import setup_logging
from bot.validators import validate_side, validate_order_type, validate_quantity, validate_price
from bot.client import BinanceClient
from bot.orders import place_order
from dotenv import load_dotenv

# Ensure environment variables are loaded relative to the script location.
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

def start():
    """
    Entry point for the CLI application.
    Supports both direct command-line arguments and interactive mode.
    """
    # Initialize the global logging configuration.
    setup_logging()
    
    # Define command-line arguments for non-interactive execution.
    p = argparse.ArgumentParser(description="My custom Binance Trading Bot")
    p.add_argument("--symbol", help="The pair you want to trade, like BTCUSDT")
    p.add_argument("--side", help="Are you buying or selling? (BUY/SELL)")
    p.add_argument("--type", help="Market or Limit?")
    p.add_argument("--quantity", help="How many coins?")
    p.add_argument("--price", help="Required for Limit orders only")
    
    args = p.parse_args()

    # Fallback to Interactive Mode if arguments are missing.
    sym = args.symbol or input("Enter Symbol (e.g., BTCUSDT): ").strip().upper()
    side = args.side or input("Enter Side (BUY/SELL): ").strip().upper()
    ot = args.type or input("Enter Type (MARKET/LIMIT): ").strip().upper()
    qty = args.quantity or input("Enter Quantity: ").strip()
    pr = args.price
    
    if ot == 'LIMIT' and not pr:
        pr = input("Enter Price for Limit order: ").strip()
    
    # Retrieve API credentials from environment variables.
    if not key or not sec:
        print("Wait! I couldn't find your keys in .env. Please enter them here:")
        key = input("API Key: ").strip()
        sec = input("Secret Key: ").strip()

    try:
        # Step 1: Input Validation.
        side = validate_side(side)
        ot = validate_order_type(ot)
        qty = validate_quantity(qty)
        pr = validate_price(pr, ot)
        
        # Step 2: Initialize Client and Execute Order.
        bot = BinanceClient(key, sec)
        place_order(bot, sym, side, ot, qty, pr)
        
        print("\nAll done! Check your logs/ folder for the breakdown.")

    except Exception as err:
        # Global exception handling to prevent erratic CLI crashes.
        print(f"\nOops! Something went wrong: {err}")
        logging.error(f"Global crash: {err}")

if __name__ == "__main__":
    start()
