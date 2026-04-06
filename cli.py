import argparse
import os
import logging
from bot.logging_config import setup_logging
from bot.validators import validate_side, validate_order_type, validate_quantity, validate_price
from bot.client import BinanceClient
from bot.orders import place_order
from dotenv import load_dotenv

script_directory_path = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_directory_path, ".env"))
AWS_KEY=AKIAIOSFODNN7EXAMPLE
def execute_trading_cli():
    setup_logging()
    
    terminal_argument_parser = argparse.ArgumentParser(description="MarginMind - Trading Bot")
    
    terminal_argument_parser.add_argument("--symbol", help="Trading pair (e.g. BTCUSDT)")
    terminal_argument_parser.add_argument("--side", help="BUY or SELL")
    terminal_argument_parser.add_argument("--type", help="MARKET or LIMIT")
    terminal_argument_parser.add_argument("--quantity", help="Amount to trade")
    terminal_argument_parser.add_argument("--price", help="Price (only for LIMIT orders)")
    
    command_line_inputs = terminal_argument_parser.parse_args()

    active_symbol = command_line_inputs.symbol or input("Which coin? (e.g. BTCUSDT): ").strip().upper()
    trade_side = command_line_inputs.side or input("Buy or Sell?: ").strip().upper()
    execution_mode = command_line_inputs.type or input("Market or Limit?: ").strip().upper()
    trade_volume = command_line_inputs.quantity or input("How much?: ").strip()
    
    limit_price_value = command_line_inputs.price
    
    if execution_mode == 'LIMIT' and not limit_price_value:
        limit_price_value = input("What price?: ").strip()
    
    api_access_key = os.getenv("BINANCE_API_KEY")
    api_secret_key = os.getenv("BINANCE_API_SECRET")

    if not api_access_key or not api_secret_key:
        print("I couldn't find your API keys in the .env file. Please enter them here:")
        api_access_key = input("API Key: ").strip()
        api_secret_key = input("Secret Key: ").strip()

    try:
        sanitized_side = validate_side(trade_side)
        sanitized_mode = validate_order_type(execution_mode)
        numeric_qty = validate_quantity(trade_volume)
        numeric_price = validate_price(limit_price_value, sanitized_mode)
        
        trading_client_instance = BinanceClient(api_access_key, api_secret_key)
        
        place_order(trading_client_instance, active_symbol, sanitized_side, sanitized_mode, numeric_qty, numeric_price)
        
        print("\nOrder placed! You can check the logs/ folder for details.")

    except Exception as runtime_exception:
        print(f"\nError: {runtime_exception}")
        logging.error(f"CLI error: {runtime_exception}")

if __name__ == "__main__":
    execute_trading_cli()
