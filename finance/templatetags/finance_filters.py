from django import template
from decimal import Decimal, InvalidOperation
from django.db.models import QuerySet

register = template.Library()

@register.filter(name='sum_dict_values')
def sum_dict_values(dictionary, key):
    """
    Sum values from a dictionary of dictionaries based on a key
    
    Args:
        dictionary: Dictionary containing nested dictionaries or QuerySet
        key: Key to sum values for
        
    Returns:
        Sum of all values for the specified key
    """
    if not dictionary:
        return Decimal('0')
    
    total = Decimal('0')
    
    # Handle QuerySet
    if isinstance(dictionary, QuerySet):
        for item in dictionary:
            if hasattr(item, key):
                try:
                    total += Decimal(str(getattr(item, key)))
                except (TypeError, ValueError):
                    continue
        return total
    
    # Handle dictionary
    for item in dictionary.values():
        if isinstance(item, dict) and key in item:
            try:
                total += Decimal(str(item[key]))
            except (TypeError, ValueError):
                continue
    return total

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiply two values
    
    Args:
        value: First value
        arg: Second value
        
    Returns:
        Product of the two values
    """
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (TypeError, ValueError):
        return 0

@register.filter(name='divisibleby')
def divisibleby(value, arg):
    """
    Divide value by arg, handling division by zero and invalid input
    
    Args:
        value: Numerator
        arg: Denominator
        
    Returns:
        Result of division or 0 if division by zero or invalid input
    """
    try:
        if not arg or str(arg).strip() in ('', 'None'):
            return 0
        value_decimal = Decimal(str(value)) if value not in (None, '', 'None') else Decimal('0')
        arg_decimal = Decimal(str(arg)) if arg not in (None, '', 'None') else Decimal('0')
        if arg_decimal == 0:
            return 0
        return value_decimal / arg_decimal
    except (TypeError, ValueError, ArithmeticError, InvalidOperation, Exception):
        return 0 