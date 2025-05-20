from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        # Convert to float first to handle any numeric format
        value_float = float(str(value))
        arg_float = float(str(arg))
        # Then convert to Decimal for precise arithmetic
        return Decimal(str(value_float)) - Decimal(str(arg_float))
    except (ValueError, TypeError, InvalidOperation):
        return 0

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key."""
    if dictionary is None:
        return 0
    if not isinstance(dictionary, dict):
        return 0
    return dictionary.get(key, 0) 