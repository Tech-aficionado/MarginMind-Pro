import os
import time
import logging
import json
import threading
from binance.client import Client
from binance import ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException

class BinanceClient:
    def __init__(self, key_identity, secret_password):
        self.apiKeyVal = key_identity
        self.apiSecretVal = secret_password
        self.concurrencyLock = threading.Lock()
        self.isMarketType = "FUTURES"
        
        self.currentActiveStops = {}
        self.isTestnetMode = os.getenv("BINANCE_USE_TESTNET", "True").lower() == "true"
        self.websocketManager = None
        
        try:
            logging.info(f"Connecting to Binance {'Testnet' if self.isTestnetMode else 'Mainnet'}...")
            self.client = Client(key_identity, secret_password, testnet=self.isTestnetMode)
            self._sync_server_time()
            
            account_data = self.client.futures_account()
            logging.info(f"Connection Verified. Equity: {account_data.get('totalWalletBalance')} USDT")
            
        except Exception as error_msg:
            logging.error(f"Engine Startup Refused: {error_msg}")
            raise

    def _sync_server_time(self):
        try:
            server_info = self.client.futures_time()
            self.client.timestamp_offset = server_info['serverTime'] - int(time.time() * 1000)
            logging.info(f"Synchronized with Binance Cloud. Offset: {self.client.timestamp_offset}ms")
        except:
            pass

    def get_account_balance(self):
        try:
            balance_records = self.client.futures_account_balance()
            for balance_item in balance_records:
                if balance_item['asset'] == 'USDT':
                    return float(balance_item['balance'])
            return 0.0
        except Exception as api_error:
            logging.error(f"Balance poll failed: {api_error}")
            return 0.0

    def get_positions(self):
        try:
            position_info = self.client.futures_position_information()
            return [position_data for position_data in position_info if float(position_data['positionAmt']) != 0]
        except:
            return []

    def get_open_orders(self, symbol_key=None):
        try:
            return self.client.futures_get_open_orders(symbol=symbol_key)
        except:
            return []

    def get_order_history(self, target_symbol=None, result_limit=50):
        try:
            all_orders_data = self.client.futures_get_all_orders(symbol=target_symbol, limit=result_limit)
            return sorted(all_orders_data, key=lambda order_entry: order_entry['time'], reverse=True)
        except Exception as history_error:
            logging.error(f"Order History API Failure: {history_error}")
            return []

    def get_24h_tickers(self, selected_symbols=None):
        try:
            ticker_list = self.client.futures_ticker()
            if not selected_symbols:
                return ticker_list
            symbol_filter_set = {s.upper() for s in selected_symbols}
            return [{
                'symbol': ticker_item['symbol'].upper(), 
                'price': ticker_item['lastPrice'],
                'change': ticker_item['priceChangePercent'], 
                'volume': ticker_item['volume']
            } for ticker_item in ticker_list if ticker_item['symbol'].upper() in symbol_filter_set]
        except:
            return []

    def _ensure_active_socket_manager(self):
        with self.concurrencyLock:
            if not self.websocketManager or not self.websocketManager.is_alive():
                logging.info("Initializing ThreadedWebsocketManager...")
                self.websocketManager = ThreadedWebsocketManager(api_key=self.apiKeyVal, api_secret=self.apiSecretVal, testnet=self.isTestnetMode)
                self.websocketManager.start()
                return True
            return False

    def start_market_pulse_stream(self, monitored_assets, update_callback):
        self._ensure_active_socket_manager()
        active_streams_list = [asset_name.lower() + '@ticker' for asset_name in monitored_assets]
        
        def process_pulse_message(msg_payload):
            try:
                if "Read loop has been closed" in str(msg_payload):
                    return
                message_content = msg_payload.get('data') if isinstance(msg_payload, dict) and 'stream' in msg_payload else msg_payload
                if isinstance(message_content, dict) and "s" in message_content:
                    update_callback({
                        'symbol': message_content['s'].upper(), 
                        'price': message_content['c'],
                        'change': message_content['P'], 
                        'volume': message_content['v']
                    })
            except Exception as message_error:
                logging.debug(f"Pulse Error: {message_error}")

        logging.info(f"Opening Multiplex Pipeline [v{len(active_streams_list)} assets]")
        self.websocketManager.start_futures_multiplex_socket(callback=process_pulse_message, streams=active_streams_list)

    def start_user_data_stream(self, user_event_callback):
        self._ensure_active_socket_manager()
        
        def process_user_socket_message(raw_msg):
            try:
                data_payload = raw_msg.get('data') if isinstance(raw_msg, dict) and 'stream' in raw_msg else raw_msg
                if isinstance(data_payload, dict) and 'e' in data_payload:
                    user_event_callback(data_payload['e'])
            except:
                pass

        logging.info("Opening Private User Data Pipeline...")
        self.websocketManager.start_futures_user_socket(callback=process_user_socket_message)

    def stop_all_streams(self):
        with self.concurrencyLock:
            if self.websocketManager:
                logging.info("Closing all WebSocket pipelines...")
                self.websocketManager.stop()
                self.websocketManager = None

    def get_symbol_info(self, symbol_name):
        try:
            exchange_info_data = self.client.futures_exchange_info()
            for symbol_detail in exchange_info_data['symbols']:
                if symbol_detail['symbol'] == symbol_name:
                    filter_map = {f['filterType']: f for f in symbol_detail['filters']}
                    return {
                        'tickSize': float(filter_map['PRICE_FILTER']['tickSize']),
                        'stepSize': float(filter_map['LOT_SIZE']['stepSize']),
                        'minNotional': float(filter_map['MIN_NOTIONAL']['notional']) if 'MIN_NOTIONAL' in filter_map else 0.0
                    }
            return None
        except:
            return None

    def round_to_step(self, numeric_value, step_size_val):
        import decimal
        precision_step = decimal.Decimal(str(step_size_val)).normalize()
        return float(decimal.Decimal(str(numeric_value)).quantize(precision_step, rounding=decimal.ROUND_DOWN))

    def place_order(self, symbol_key, order_side, order_type_choice, quantity_val, price_val=None, stop_price_val=None):
        order_params = {'symbol': symbol_key, 'side': order_side, 'type': order_type_choice, 'quantity': quantity_val}
        
        if order_type_choice == 'LIMIT':
            order_params.update({'price': str(price_val), 'timeInForce': 'GTC'})
            
        if order_type_choice in ['STOP_MARKET', 'TAKE_PROFIT_MARKET']:
            order_params['stopPrice'] = str(stop_price_val)
            
        return self.client.futures_create_order(**order_params)

    def get_order_status(self, symbol_id, numeric_order_id):
        return self.client.futures_get_order(symbol=symbol_id, orderId=numeric_order_id)

    def register_local_stop(self, symbol_id, order_side, quantity_amt, sl_val=None, tp_val=None):
        self.currentActiveStops[symbol_id] = {'side': order_side, 'qty': quantity_amt, 'sl': sl_val, 'tp': tp_val}

    def change_leverage(self, asset_symbol, leverage_limit):
        try:
            return self.client.futures_change_leverage(symbol=asset_symbol, leverage=leverage_limit)
        except:
            pass

    def change_margin_mode(self, asset_symbol, margin_type_mode):
        try:
            return self.client.futures_change_margin_type(symbol=asset_symbol, marginType=margin_type_mode.upper())
        except:
            pass
