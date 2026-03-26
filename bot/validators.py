# -----------------------------------------------------------------------------
# Module: bot.validators
# Description: Input guarding and validation logic to ensure API compatibility.
# -----------------------------------------------------------------------------

def validate_side(side):
    """Ensure the trading side is either BUY or SELL."""
    # Only BUY or SELL allowed!
    s = side.upper().strip()
    if s not in ["BUY", "SELL"]:
        raise ValueError("Side must be BUY or SELL!")
    return s

def validate_order_type(ot):
    """Ensure the order type is supported (MARKET or LIMIT)."""
    # Keeping it simple for the assignment.
    t = ot.upper().strip()
    if t not in ["MARKET", "LIMIT"]:
        raise ValueError("Only MARKET and LIMIT orders are supported for now.")
    return t

def validate_quantity(qty):
    """Validate that the quantity is a positive numeric value."""
    # Quantity needs to be a number.
    try:
        val = float(qty)
        if val <= 0:
            raise ValueError("Quantity must be more than zero!")
        return val
    except ValueError:
        raise ValueError(f"'{qty}' is not a valid number for quantity.")

def validate_price(price, order_type):
    """Ensure price is provided and valid for LIMIT orders."""
    # If it's a LIMIT order, we MUST have a price.
    if order_type == "LIMIT":
        if not price:
            raise ValueError("Limit orders need a price!")
        try:
            val = float(price)
            if val <= 0:
                raise ValueError("Price must be more than zero!")
            return val
        except ValueError:
            raise ValueError(f"'{price}' is not a valid number for price.")
    return None # Market orders don't need a price.
