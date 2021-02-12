from django.db import models

from imagedeck.models import ImageDeckModelMixin

class TestModel(models.Model):
    class Meta:
        ordering = ['pk',]


class ImageDeckModel(ImageDeckModelMixin):
    pass