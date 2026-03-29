import logging
import datetime
import os
import time

def place_order(trading_client, target_asset, trade_direction, execution_type, requested_amount, target_price=None, stop_loss_trigger=None, take_profit_trigger=None):
    try:
        asset_filters = trading_client.get_symbol_info(target_asset)
        
        if asset_filters:
            requested_amount = trading_client.round_to_step(requested_amount, asset_filters['stepSize'])
            if target_price:
                target_price = trading_client.round_to_step(target_price, asset_filters['tickSize'])
        
        logging.info(f"[TX] {trade_direction} {requested_amount} {target_asset} @ {execution_type}")
        
        order_response = trading_client.place_order(target_asset, trade_direction, execution_type, requested_amount, target_price)
        unique_order_id = order_response.get('orderId')
        
        time.sleep(1)
        
        order_status_result = trading_client.get_order_status(target_asset, unique_order_id)
        current_execution_status = order_status_result.get('status')
        realized_average_price = order_status_result.get('avgPrice', '0.00')
        
        logging.info(f"[CONFIRM] Order {unique_order_id} is {current_execution_status} (Avg PX: {realized_average_price})")
        
        if stop_loss_trigger or take_profit_trigger:
            trading_client.register_local_stop(target_asset, trade_direction, requested_amount, sl=stop_loss_trigger, tp=take_profit_trigger)
            
        _record_trade_history(trading_client, trade_direction, target_asset, requested_amount, realized_average_price, stop_loss_trigger, take_profit_trigger)
        
        return order_status_result

    except Exception as execution_error:
        logging.error(f"Order Execution Failure: {execution_error}")
        raise

def _record_trade_history(client_instance, direction, symbol, qty_val, px_val, sl_val, tp_val):
    history_log_path = "logs/trade_history.log"
    os.makedirs("logs", exist_ok=True)
    
    timestamp_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(history_log_path, "a") as history_file:
        history_file.write(f"[{timestamp_string}] {direction} {symbol} | Qty: {qty_val} | Px: {px_val} | SL: {sl_val} | TP: {tp_val}\n")

def calculate_position_size(client_ref, symbol_name, account_balance, risk_percentage, entry_price_val, leverage_multiple=1):
    try:
        trade_risk_amount = (float(account_balance) * (float(risk_percentage) / 100))
        notional_exposure = trade_risk_amount * float(leverage_multiple)
        
        raw_quantity = notional_exposure / float(entry_price_val)
        
        symbol_specifications = client_ref.get_symbol_info(symbol_name)
        
        if symbol_specifications:
            calculated_qty = client_ref.round_to_step(raw_quantity, symbol_specifications['stepSize'])
            
            minimum_notional_requirement = symbol_specifications.get('minNotional', 0)
            if calculated_qty * float(entry_price_val) < minimum_notional_requirement:
                calculated_qty = client_ref.round_to_step(minimum_notional_requirement / float(entry_price_val) + symbol_specifications['stepSize'], symbol_specifications['stepSize'])
                
            return calculated_qty
            
        return round(raw_quantity, 4)
        
    except Exception as sizing_error:
        logging.error(f"Sizing error: {sizing_error}")
        return 0.0
