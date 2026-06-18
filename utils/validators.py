# ==============================================================
# Input Validators
# ==============================================================

import re


def validate_phone(phone):
    """Validate a 10-digit Indian phone number.
    Returns (is_valid, cleaned_phone_or_error_msg).
    """
    cleaned = re.sub(r"[\s\-\+]", "", phone)
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    if not cleaned.isdigit():
        return False, "Phone number must contain only digits."
    if len(cleaned) != 10:
        return False, "Phone number must be 10 digits."
    return True, cleaned


def validate_gst(gst):
    """Validate GST number format (15 chars: 2-digit state code + PAN + 1Z + check).
    Returns (is_valid, error_msg_or_None).
    """
    if not gst:
        return True, None  # GST is optional
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    if re.match(pattern, gst.upper()):
        return True, None
    return False, "Invalid GST format. Expected: 22AAAAA0000A1Z5"


def validate_positive_int(value, field_name="Value"):
    """Validate that value is a positive integer.
    Returns (is_valid, int_value_or_error_msg).
    """
    try:
        v = int(value)
        if v <= 0:
            return False, f"{field_name} must be greater than zero."
        return True, v
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number."


def validate_positive_decimal(value, field_name="Value"):
    """Validate that value is a positive decimal.
    Returns (is_valid, float_value_or_error_msg).
    """
    try:
        v = float(value)
        if v < 0:
            return False, f"{field_name} must not be negative."
        return True, v
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number."


def validate_not_empty(value, field_name="Field"):
    """Validate that a string is not empty.
    Returns (is_valid, error_msg_or_None).
    """
    if not value or not str(value).strip():
        return False, f"{field_name} is required."
    return True, None


def validate_quantity_against_stock(quantity, stock, product_name="Product"):
    """Validate that requested quantity doesn't exceed stock."""
    if quantity > stock:
        return False, (
            f"Insufficient stock for {product_name}. "
            f"Available: {stock}, Requested: {quantity}"
        )
    return True, None
