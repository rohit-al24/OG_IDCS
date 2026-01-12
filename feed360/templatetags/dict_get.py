from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    """Get value from dict by key in template."""
    if isinstance(d, dict):
        return d.get(key, '')
    return ''
