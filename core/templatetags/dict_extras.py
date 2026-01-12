from django import template

register = template.Library()

def dict_get(d, key):
    return d.get(key, '')

register.filter('dict_get', dict_get)
