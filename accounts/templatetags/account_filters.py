from django import template
from django.template.defaultfilters import floatformat
import math

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def abs(value):
    """Return the absolute value."""
    try:
        return math.fabs(float(value))
    except (ValueError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary."""
    return dictionary.get(key, 0) if dictionary else 0 