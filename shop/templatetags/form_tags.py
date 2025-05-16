from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_attrs')
def add_attrs(field, attrs):
    """
    Add HTML attributes to a form field.
    Usage: {{ field|add_attrs:"class:form-control,aria-label:Enter name" }}
    """
    if not attrs:
        return field
    
    attrs_dict = {}
    for attr in attrs.split(','):
        if ':' in attr:
            key, value = attr.split(':', 1)
            attrs_dict[key.strip()] = value.strip()
    
    return field.as_widget(attrs=attrs_dict) 