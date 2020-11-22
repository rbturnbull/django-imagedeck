import re
from django.db import models
from django.db.models.signals import post_save
from django.db.models import Max
from django.dispatch import receiver
from polymorphic.models import PolymorphicModel
from django.core.files import File as DjangoFile

from filer.models import Image as FilerImage
from filer.models import File as FilerFile
from filer.models import Folder

from imagekit.models import ImageSpecField
from imagekit.processors import Thumbnail
from PIL import Image
import requests
from io import BytesIO
from django.contrib.auth import get_user_model
from pathlib import Path
import glob
from filer.settings import FILER_IS_PUBLIC_DEFAULT

from . import settings as imagedeck_settings


def create_filer_folder( destination, owner=None ):
    """ Recursively creates a folder structure in django-filer. """
    # Get owner if it is just a string
    if owner and type(owner) == str:
        owner = get_user_model().objects.get(username=owner)

    # Get destination folder
    dest_path = Path(destination)
    folder = None
    for folder_name in dest_path.parts:
        folder, created = Folder.objects.update_or_create( name=folder_name, parent=folder )
        if created and owner:
            folder.owner = owner
            folder.save()
    return folder

def import_django_file(file_obj, folder, owner=None):
    """
    Create a File or an Image into the given folder

    Adapted from filer.management.commands.import_files
    """    
    try:
        path = Path(file_obj.name)
        iext = path.suffix.lower()
    except Exception as err:  # noqa
        # print("exception", err)
        iext = ''

    if iext in ['.jpg', '.jpeg', '.png', '.gif']:
        obj, created = FilerImage.objects.get_or_create(
            original_filename=file_obj.name,
            file=file_obj,
            folder=folder,
            owner=owner,
            is_public=FILER_IS_PUBLIC_DEFAULT)
    else:
        obj, created = FilerFile.objects.get_or_create(
            original_filename=file_obj.name,
            file=file_obj,
            owner=owner,
            folder=folder,
            is_public=FILER_IS_PUBLIC_DEFAULT)
    return obj

def import_file(file_path, folder):
    if type(file_path) == str:
        file_path = Path(file_path)
    dj_file = DjangoFile(open(file_path, mode='rb'), name=file_path.name)    
    return import_django_file( dj_file, folder )

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

    def max_rank(self):
        """ Returns the highest rank of a membership in this deck. """
        self.deckmembership_set.aggregate(Max('rank'))['rank__max']

    def add_image(self, image, rank=None):
        if rank is None:
            rank = self.max_rank() + 1

        DeckMembership.objects.update_or_create( deck=self, image=image, rank=rank )

    @classmethod
    def import_glob( cls, destination, pattern, deck_name="", owner=None, rank_regex="(\d+)" ):
        folder = create_filer_folder(destination, owner=owner)
        
        if not deck_name:
            deck_name = str(folder)
        
        deck, _ = cls.objects.update_or_create( name=deck_name )

        for filename in glob.glob(pattern):
            print(f'Adding {filename}')

            # Create image
            file = import_file( filename, folder )
            if type(file) == FilerImage:
                # Get rank
                integer_matches = re.findall(rank_regex, filename)
                rank = int(integer_matches[-1]) if integer_matches else None

                # Add to deck
                deck.add_image( file.deckimagefiler, rank=rank )

        return deck

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


class DeckImageFiler(DeckImageBase):
    filer_image = models.OneToOneField(FilerImage, on_delete=models.CASCADE, related_name="deckimagefiler")

    def __str__(self):
        return str(self.filer_image)

    def get_width(self):
        return self.filer_image.width()

    def get_height(self):
        return self.filer_image.height()


@receiver(post_save, sender=FilerImage)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        DeckImageFiler.objects.create(filer_image=instance)
    instance.deckimagefiler.save()


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
