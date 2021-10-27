from django.conf import settings


def get_setting(key, default):
    if hasattr(settings, key):
        return getattr(settings, key)
    return default


IMAGEDECK_THUMBNAIL_WIDTH = get_setting("IMAGEDECK_THUMBNAIL_WIDTH", 250)
IMAGEDECK_THUMBNAIL_HEIGHT = get_setting("IMAGEDECK_THUMBNAIL_HEIGHT", None)
IMAGEDECK_THUMBNAIL_QUALITY = get_setting("IMAGEDECK_THUMBNAIL_QUALITY", 60)
IMAGEDECK_THUMBNAIL_FORMAT = get_setting("IMAGEDECK_THUMBNAIL_FORMAT", "JPEG")
IMAGEDECK_DEFAULT_WIDTH = get_setting("IMAGEDECK_DEFAULT_WIDTH", 250)
IMAGEDECK_DEFAULT_HEIGHT = get_setting("IMAGEDECK_DEFAULT_HEIGHT", 250)
