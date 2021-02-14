from django import template
import logging

register = template.Library()

@register.filter
def url_with_width(image, width=None):
    return image.url(width=width)
