def validate_side(trade_side_input):
    sanitized_side = trade_side_input.upper().strip()
    
    if sanitized_side not in ["BUY", "SELL"]:
        raise ValueError("Side needs to be either BUY or SELL.")
        
    return sanitized_side

def validate_order_type(order_type_input):
    sanitized_type = order_type_input.upper().strip()
    
    if sanitized_type not in ["MARKET", "LIMIT"]:
        raise ValueError("Only MARKET and LIMIT orders are supported right now.")
        
    return sanitized_type

def validate_quantity(quantity_string):
    try:
        numeric_value = float(quantity_string)
        if numeric_value <= 0:
            raise ValueError("Quantity has to be greater than zero.")
        return numeric_value
    except ValueError:
        raise ValueError(f"'{quantity_string}' isn't a valid number for quantity.")

def validate_price(price_input, selected_type):
    if selected_type == "LIMIT":
        if not price_input:
            raise ValueError("Limit orders need a price.")
            
        try:
            numeric_price = float(price_input)
            if numeric_price <= 0:
                raise ValueError("Price has to be greater than zero.")
            return numeric_price
        except ValueError:
            raise ValueError(f"'{price_input}' isn't a valid number for price.")
            
    return None

def validate_sl_tp_ratios(trade_side, entry_price_val, sl_price_val, tp_price_val):
    if sl_price_val:
        stop_loss_numeric = float(sl_price_val)
        
        if trade_side == "BUY" and stop_loss_numeric >= float(entry_price_val):
            raise ValueError("Stop Loss for a BUY order must be below the entry price.")
            
        if trade_side == "SELL" and stop_loss_numeric <= float(entry_price_val):
            raise ValueError("Stop Loss for a SELL order must be above the entry price.")
            
    if tp_price_val:
        take_profit_numeric = float(tp_price_val)
        
        if trade_side == "BUY" and take_profit_numeric <= float(entry_price_val):
            raise ValueError("Take Profit for a BUY order must be above the entry price.")
            
        if trade_side == "SELL" and take_profit_numeric >= float(entry_price_val):
            raise ValueError("Take Profit for a SELL order must be below the entry price.")
            
    return True
