from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sub(value, arg):
    """Subtract the argument from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sum_quantity(items):
    """Sum the quantities of all items in the cart"""
    try:
        return sum(item.get('quantity', 0) for item in items)
    except (AttributeError, TypeError):
        return 0 