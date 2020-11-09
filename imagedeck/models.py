from django.db import models
from polymorphic.models import PolymorphicModel
from imagekit.models import ImageSpecField
from imagekit.processors import Thumbnail
from PIL import Image
import requests
from io import BytesIO

from . import settings as imagedeck_settings

def image_from_url(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))


class DeckLicence(models.Model):
    name = models.CharField(max_length=255)
    logo = models.URLField(max_length=511, help_text="A URL for the image of the logo of this licence.")
    info = models.URLField(max_length=511, help_text="A URL for more information about this licence.")

    def __str__(self):
        return self.name
    

class DeckBase(PolymorphicModel):
    name = models.CharField(max_length=255, default="", blank=True)
    images = models.ManyToManyField( 'DeckImageBase', through='DeckMembership')

    def __str__(self):
        return self.name

    def primary_image(self):
        return self.images.order_by( '-deckmembership__primary' ).first()

    def images_ordered(self):
        """
        Returns the images in order.

        NB. This shouldn't be necessary. It should work from the ordering field on the DeckMembership class.
        """
        return self.images.order_by( 'deckmembership__rank' )


class Deck(DeckBase):
    pass


class DeckGallica(DeckBase):
    base_url = models.URLField(max_length=511)
    


class DeckImageBase(PolymorphicModel):
    licence = models.ForeignKey(DeckLicence, on_delete=models.SET_DEFAULT, default=None, null=True, blank=True)
    source_url = models.URLField(max_length=511, default="", blank=True, help_text="The URL for the source of this image.")
    attribution = models.CharField(max_length=255, default="", blank=True, )

    # TODO add permissions 
    # https://django-guardian.readthedocs.io/en/stable/userguide/assign.html ?

    def url(self, width=None, height=None):
        """ 
        Returns a URL to a version of this image.
        
        If width and height are null then it returns the fullsized image.
        """
        return None

    def thumbnail(self):
        """ Returns a URL to a thumbnail of this image. """

        # Try to keep aspect ratio
        width = imagedeck_settings.IMAGEDECK_THUMBNAIL_WIDTH
        height = imagedeck_settings.IMAGEDECK_THUMBNAIL_HEIGHT

        if not width and not height:
            width = 250

        if not height:
            height = width/self.get_width() * self.get_height()

        if not width:
            width = height/self.get_height() * self.get_width()

        return self.url(width=imagedeck_settings.IMAGEDECK_THUMBNAIL_WIDTH, height=imagedeck_settings.IMAGEDECK_THUMBNAIL_HEIGHT)

    def get_width(self):
        return imagedeck_settings.IMAGEDECK_DEFAULT_WIDTH

    def get_height(self):
        return imagedeck_settings.IMAGEDECK_DEFAULT_HEIGHT

    def get_caption(self):
        components = []
        if self.attribution:
            components.append( f"Attribution: {self.attribution}")
        if self.source_url:
            components.append( f"Source: {self.source_url}.")
        if self.licence:
            components.append( f"Licence: {self.licence}.")
        return " ".join(components)



class DeckImage(DeckImageBase):
    image = models.ImageField()
    thumbnail_generator = ImageSpecField(
        source='image', 
        processors=[Thumbnail(imagedeck_settings.IMAGEDECK_THUMBNAIL_WIDTH, imagedeck_settings.IMAGEDECK_THUMBNAIL_HEIGHT)], 
        format=imagedeck_settings.IMAGEDECK_THUMBNAIL_FORMAT, 
        options={'quality': imagedeck_settings.IMAGEDECK_THUMBNAIL_QUALITY}
    )

    def __str__(self):
        return self.image.name

    def url(self, width=None, height=None):
        return self.image.url

    def thumbnail(self):
        return self.image.url
        # See issue https://github.com/matthewwithanm/django-imagekit/issues/391#issuecomment-275367006
        return self.thumbnail_generator.url

    def get_width(self):
        return self.image.width

    def get_height(self):
        return self.image.height




class DeckImageExternal(DeckImageBase):
    external_url = models.URLField(max_length=511)
    width = models.PositiveIntegerField(default=0, blank=True)
    height = models.PositiveIntegerField(default=0, blank=True)

    def __str__(self):
        return self.external_url

    def url(self, width=None, height=None):
        return self.external_url

    def get_width(self):
        if self.width:
            return self.width
        self.set_dimensions()
        if self.width:
            return self.width
        return imagedeck_settings.IMAGEDECK_DEFAULT_WIDTH

    def get_height(self):
        if self.height:
            return self.height
        return imagedeck_settings.IMAGEDECK_DEFAULT_HEIGHT

    def set_dimensions(self):
        img = image_from_url(self.url())
        self.width = img.width
        self.height = img.height
        self.save()


class DeckImageIIIF(DeckImageBase):
    base_url = models.URLField(max_length=511)
    width = models.PositiveIntegerField(default=0, blank=True)
    height = models.PositiveIntegerField(default=0, blank=True)

    def __str__(self):
        return self.base_url

    def iiif_url(self, region="full", size="full", rotation="0", quality="default", format="jpg"):
        return f"{self.base_url}/{region}/{size}/{rotation}/{quality}.{format}"

    def url(self, width=None, height=None):
        if width is None and height is None:
            size = "full"
        else:
            if width is None: width = ""
            if height is None: height = ""
            size = f"{width},{height}"
            
        return self.iiif_url(size=size)

    def get_width(self):
        if self.width:
            return self.width
        self.set_dimensions()
        if self.width:
            return self.width
        return imagedeck_settings.IMAGEDECK_DEFAULT_WIDTH

    def get_height(self):
        if self.height:
            return self.height
        return imagedeck_settings.IMAGEDECK_DEFAULT_HEIGHT

    def set_dimensions(self):
        img = image_from_url(self.url())
        self.width = img.width
        self.height = img.height
        self.save()


class DeckMembership(models.Model):
    deck = models.ForeignKey(DeckBase, on_delete=models.CASCADE)
    image = models.ForeignKey(DeckImageBase, on_delete=models.CASCADE)
    rank = models.PositiveIntegerField( default=0, help_text="The rank of the image in the ordering of the deck.")
    primary = models.BooleanField(default=False, help_text="Whether or not this image should be conisdered the primary image for the deck.")

    class Meta:
        ordering = ['rank',]
