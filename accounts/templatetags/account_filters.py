from django import template
from django.template.defaultfilters import floatformat
import math
from decimal import Decimal

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value."""
    try:
        return value - arg
    except (ValueError, TypeError):
        try:
            return Decimal(value) - Decimal(arg)
        except:
            return 0

@register.filter
def abs(value):
    """Returns absolute value."""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Gets an item from a dictionary. Returns None if dictionary is None or key doesn't exist."""
    if dictionary is None:
        return None
    return dictionary.get(key, None)

@register.filter
def replace(value, arg):
    """Replaces all occurrences of arg[0] with arg[1] in the given string."""
    if isinstance(value, str):
        return value.replace("_", " ")
    return value

@register.filter
def format_expense_name(value):
    """Formats expense name by replacing underscores with spaces and title casing."""
    try:
        return value.replace('_', ' ').title()
    except (ValueError, TypeError):
        return value 

fields = ['name', 'code', 'type', 'category', 'expense_category', 'description'] 