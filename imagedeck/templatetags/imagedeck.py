from django import template
import logging

register = template.Library()


@register.filter
def url_with_width(image, width=None):
    # return str(type(image))
    try:
        return image.url(width=width)
    except:
        return str(image)
