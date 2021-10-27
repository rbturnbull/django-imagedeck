import re
import os
from django.db import models
from django.db.models.signals import post_save
from django.db.models import Max
from django.dispatch import receiver
from polymorphic.models import PolymorphicModel
from django.core.files import File as DjangoFile
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from filer.models import Image as FilerImage
from filer.models import File as FilerFile
from filer.models import Folder
from filer.settings import FILER_IS_PUBLIC_DEFAULT

from imagekit.models import ImageSpecField
from imagekit.processors import Thumbnail
from PIL import Image
import requests
from io import BytesIO
from django.contrib.auth import get_user_model
from pathlib import Path
import glob

from . import settings as imagedeck_settings


def check_owner(owner):
    if owner and type(owner) == str:
        owner = get_user_model().objects.get(username=owner)
    return owner


def create_filer_folder(destination, owner=None):
    """Recursively creates a folder structure in django-filer."""
    # Get owner if it is just a string
    owner = check_owner(owner)

    # Get destination folder
    dest_path = Path(destination)
    folder = None
    for folder_name in dest_path.parts:
        folder, created = Folder.objects.update_or_create(
            name=folder_name, parent=folder
        )
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
        iext = ""

    # Get owner if it is just a string
    owner = check_owner(owner)

    if iext in [".jpg", ".jpeg", ".png", ".gif"]:
        obj, created = FilerImage.objects.get_or_create(
            original_filename=file_obj.name,
            file=file_obj,
            folder=folder,
            owner=owner,
            is_public=FILER_IS_PUBLIC_DEFAULT,
        )
    else:
        obj, created = FilerFile.objects.get_or_create(
            original_filename=file_obj.name,
            file=file_obj,
            owner=owner,
            folder=folder,
            is_public=FILER_IS_PUBLIC_DEFAULT,
        )
    return obj


def import_file(file_path, folder, owner=None):
    """Imports a file from a path into a folder in Django Filer."""
    if type(file_path) == str:
        file_path = Path(file_path)
    dj_file = DjangoFile(open(file_path, mode="rb"), name=file_path.name)
    return import_django_file(dj_file, folder, owner)


def image_from_url(url):
    try:
        response = requests.get(url)
        return Image.open(BytesIO(response.content))
    except:
        return None


class DeckLicence(models.Model):
    name = models.CharField(max_length=255)
    logo = models.URLField(
        max_length=511, help_text="A URL for the image of the logo of this licence."
    )
    info = models.URLField(
        max_length=511, help_text="A URL for more information about this licence."
    )

    def __str__(self):
        return self.name


class DeckBase(PolymorphicModel):
    name = models.CharField(max_length=255, default="", blank=True)
    images = models.ManyToManyField("DeckImageBase", through="DeckMembership")

    class Meta:
        ordering = [
            "name",
        ]

    def __str__(self):
        return self.name

    def primary_image(self):
        return self.images.order_by("-deckmembership__primary").first()

    def images_ordered(self):
        """
        Returns the images in order.

        NB. This shouldn't be necessary. It should work from the ordering field on the DeckMembership class.
        """
        return self.images.order_by("deckmembership__rank")

    def memberships(self):
        return DeckMembership.objects.filter(deck=self).order_by("rank")

    # Don't add a __len__ function. For some reason it means that objects aren't saved in the database properly.
    # def __len__(self):
    #     return self.images.count()
    #
    # def __getitem__(self, i):
    #     return self.images_ordered()[i]

    def max_rank(self):
        """Returns the highest rank of a membership in this deck."""
        if self.deckmembership_set.count() == 0:
            return 0
        return self.deckmembership_set.aggregate(Max("rank"))["rank__max"]

    def images_before(self, image):
        membership = image.deckmembership_set.filter(deck=self)
        if not membership:
            return None
        return self.images.filter(deckmembership__rank__lt=membership.rank).order_by(
            "deckmembership__rank"
        )

    def images_after(self, image):
        membership = image.deckmembership_set.filter(deck=self)
        if not membership:
            return None
        return self.images.filter(deckmembership__rank__gt=membership.rank).order_by(
            "deckmembership__rank"
        )

    def save_image_file(self, file, owner=None):
        folder = create_filer_folder(self.name, owner=owner)
        file_image = import_django_file(file, folder, owner)
        image = file_image.deckimagefiler

        self.add_image(image)

        return image

    def add_image(self, image, rank=None):
        if rank is None:
            rank = self.max_rank() + 1

        membership, _ = DeckMembership.objects.update_or_create(
            deck=self, image=image, rank=rank
        )
        return membership

    def import_file(self, filename, folder, owner, rank_regex):
        # Create image
        file = import_file(filename, folder, owner=owner)
        if type(file) == FilerImage:
            # Get rank
            integer_matches = re.findall(rank_regex, str(filename))
            rank = int(integer_matches[-1]) if integer_matches else None

            # Add to deck
            self.add_image(file.deckimagefiler, rank=rank)
        return file

    @classmethod
    def combine(cls, new_deck, decks_to_combine):
        images = []
        for deck_to_combine in decks_to_combine:
            if type(deck_to_combine) == str:
                deck_to_combine = Deck.objects.get(name=deck_to_combine)
            images += list(deck_to_combine.images_ordered())

        if type(new_deck) == str:
            new_deck, _ = Deck.objects.update_or_create(name=new_deck)

        for image in images:
            new_deck.add_image(image)

        return new_deck

    @classmethod
    def import_glob(
        cls, destination, pattern, deck_name="", owner=None, rank_regex="(\d+)"
    ):
        """Import files using a glob pattern."""
        folder = create_filer_folder(destination, owner=owner)

        if not deck_name:
            deck_name = str(folder)

        deck, _ = Deck.objects.update_or_create(name=deck_name)
        deck.save()

        for filename in glob.glob(pattern):
            print(f"Adding {filename}")
            deck.import_file(filename, folder, owner, rank_regex)

        return deck


class Deck(DeckBase):
    @classmethod
    def import_regex(
        cls,
        destination,
        pattern,
        source_dir=".",
        deck_name="",
        owner=None,
        rank_regex="(\d+)",
    ):
        """Import files using a regex pattern."""
        folder = create_filer_folder(destination, owner=owner)

        if not deck_name:
            deck_name = str(folder)

        deck, _ = Deck.objects.update_or_create(name=deck_name)
        deck.save()

        if type(source_dir) == str:
            source_dir = Path(source_dir)

        for filename in os.listdir(source_dir):
            if re.match(pattern, filename):
                print(f"Adding {filename}")

                deck.import_file(source_dir / filename, folder, owner, rank_regex)

        return deck


class DeckGallica(DeckBase):
    base_url = models.URLField(max_length=511)


def images_in_iiif_json_element(element, result, prefix=""):
    """Recursively checks a JSON element from a IIIF Manifest for an image."""
    if type(element) == dict:
        if (
            "@type" in element
            and element["@type"] == "dctypes:Image"
            and "service" in element
            and "@id" in element["service"]
        ):
            result.append(element["service"]["@id"])

        for child in element:
            images_in_iiif_json_element(element[child], result, prefix=f"\t{prefix}")

    elif type(element) == list:
        for child in element:
            images_in_iiif_json_element(child, result, prefix=f"\t{prefix}")


def images_in_iiif_json(data):
    """Returns a list of all the images in a IIIF presentation."""
    result = []
    images_in_iiif_json_element(data, result)
    return result


class DeckIIIF(DeckBase):
    manifest_url = models.URLField(max_length=511)

    def get_manifest_text(self):
        f = requests.get(self.manifest_url)
        return f.text

    def get_manifest_json(self):
        f = requests.get(self.manifest_url)
        return f.json()

    def image_base_urls(self):
        return images_in_iiif_json(self.get_manifest_json())

    def images_from_manifest(self):
        urls = self.image_base_urls()

        for url in urls:
            image, _ = DeckImageIIIF.objects.update_or_create(base_url=url)
            if self.images.filter(id=image.id).count() == 0:
                self.add_image(image)

    # Override save to get the images from the manifest if there aren't already images there
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.images.count() == 0 and self.manifest_url:
            self.images_from_manifest()

    def split(self, width_pct: int = 50, rtl=False):
        new_deck = Deck.objects.create(
            name=f"{self.name} split width {width_pct}",
        )
        for image in self.images_ordered():
            new_images = image.split(width_pct=width_pct, rtl=rtl)
            for new_image in new_images:
                new_deck.add_image(new_image)
        return new_deck


class DeckImageBase(PolymorphicModel):
    licence = models.ForeignKey(
        DeckLicence, on_delete=models.SET_DEFAULT, default=None, null=True, blank=True
    )
    source_url = models.URLField(
        max_length=511,
        default="",
        blank=True,
        help_text="The URL for the source of this image.",
    )
    attribution = models.CharField(
        max_length=255,
        default="",
        blank=True,
    )

    # TODO add permissions
    # https://django-guardian.readthedocs.io/en/stable/userguide/assign.html ?

    def url(self, width=None, height=None):
        """
        Returns a URL to a version of this image.

        If width and height are null then it returns the fullsized image.
        """
        return None

    def thumbnail_dimensions(self):
        width = imagedeck_settings.IMAGEDECK_THUMBNAIL_WIDTH
        height = imagedeck_settings.IMAGEDECK_THUMBNAIL_HEIGHT

        if not width and not height:
            width = 250

        # Try to keep aspect ratio
        if not height:
            height = width / self.get_width() * self.get_height()

        if not width:
            width = height / self.get_height() * self.get_width()

        return width, height

    def thumbnail(self):
        """Returns a URL to a thumbnail of this image."""
        width, height = self.thumbnail_dimensions()
        return self.url(width=width, height=height)

    def get_width(self):
        return imagedeck_settings.IMAGEDECK_DEFAULT_WIDTH

    def get_height(self):
        return imagedeck_settings.IMAGEDECK_DEFAULT_HEIGHT

    def get_caption(self):
        components = []
        if self.attribution:
            components.append(f"Attribution: {self.attribution}")
        if self.source_url:
            components.append(f"Source: {self.source_url}.")
        if self.licence:
            components.append(f"Licence: {self.licence}.")
        return " ".join(components)


class DeckImage(DeckImageBase):
    image = models.ImageField()
    thumbnail_generator = ImageSpecField(
        source="image",
        processors=[
            Thumbnail(
                imagedeck_settings.IMAGEDECK_THUMBNAIL_WIDTH,
                imagedeck_settings.IMAGEDECK_THUMBNAIL_HEIGHT,
            )
        ],
        format=imagedeck_settings.IMAGEDECK_THUMBNAIL_FORMAT,
        options={"quality": imagedeck_settings.IMAGEDECK_THUMBNAIL_QUALITY},
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
    filer_image = models.OneToOneField(
        FilerImage, on_delete=models.CASCADE, related_name="deckimagefiler"
    )

    def __str__(self):
        return str(self.filer_image)

    def get_width(self):
        return self.filer_image.width

    def get_height(self):
        return self.filer_image.height

    def thumbnail(self):
        width, height = self.thumbnail_dimensions()

        return self.url(width=width, height=height)

    def url(self, width=None, height=None):
        if width == None and height == None:
            return self.filer_image.url

        if height == None:
            height = 0

        if width == None:
            width = 0

        thumbnail_name = f"{width}x{height}"
        required_thumbnails = {
            thumbnail_name: {
                "size": (width, height),
                "crop": True,
                "upscale": True,
                "subject_location": self.filer_image.subject_location,
            }
        }
        thumbnails = self.filer_image._generate_thumbnails(required_thumbnails)

        return thumbnails[thumbnail_name]


@receiver(post_save, sender=FilerImage)
def create_or_update_filer_image(sender, instance, created, **kwargs):
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
        self.set_dimensions()
        if self.height:
            return self.height
        return imagedeck_settings.IMAGEDECK_DEFAULT_HEIGHT

    def set_dimensions(self):
        img = image_from_url(self.url())
        if img:
            self.width = img.width
            self.height = img.height
            self.save()


class DeckImageIIIF(DeckImageBase):
    base_url = models.URLField(max_length=511)
    width = models.PositiveIntegerField(default=0, blank=True)
    height = models.PositiveIntegerField(default=0, blank=True)
    region = models.CharField(
        max_length=255,
        default="full",
        help_text="A way to crop the region of an image. In the form of 'full', 'x,y,w,h' or 'pct:x,y,w,h'.",
    )

    def __str__(self):
        return self.base_url

    def iiif_url(
        self, region=None, size="full", rotation="0", quality="default", format="jpg"
    ):
        region = region or self.region
        return f"{self.base_url}/{region}/{size}/{rotation}/{quality}.{format}"

    def url(self, width=None, height=None):
        if width is None and height is None:
            size = "full"
        else:
            if width is None:
                width = ""
            if height is None:
                height = ""
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

    def info_json_url(self):
        return f"{self.base_url}/info.json"

    def get_info_json(self):
        f = requests.get(self.info_json_url())
        return f.json()

    def set_dimensions(self):
        info_json = self.get_info_json()
        save = False
        if "width" in info_json:
            self.width = info_json["width"]
            save = True
        if "height" in info_json:
            self.height = info_json["height"]
            save = True
        if save:
            self.save()

    def thumbnail_dimensions(self):
        width = imagedeck_settings.IMAGEDECK_THUMBNAIL_WIDTH or 250
        return width, None

    def split(self, width_pct: int = 50, rtl=False):
        """
        Creates two new IIIF images.

        Useful for imgaes of an open page spread that needs to be divided.

        Returns a list of two DeckImageIIIF objects.
        """
        regions = (
            f"pct:0,0,{width_pct},100",
            f"pct:{100-width_pct},0,100,100",
        )
        if rtl:
            regions = (regions[1], regions[0])

        result = []
        for region in regions:
            width = int(self.width * width_pct * 100) if self.width else self.width
            image, _ = type(self).objects.update_or_create(
                base_url=self.base_url,
                width=width,
                height=self.height,
                region=region,
            )
            result.append(image)
        return result


class DeckMembership(models.Model):
    deck = models.ForeignKey(DeckBase, on_delete=models.CASCADE)
    image = models.ForeignKey(DeckImageBase, on_delete=models.CASCADE)
    rank = models.PositiveIntegerField(
        default=0, help_text="The rank of the image in the ordering of the deck."
    )
    primary = models.BooleanField(
        default=False,
        help_text="Whether or not this image should be conisdered the primary image for the deck.",
    )

    def __str__(self):
        return f"{self.deck}, {self.image}, {self.rank}"

    class Meta:
        ordering = [
            "rank",
        ]

    def index(self):
        """
        Returns the index of this image in the deck.

        TODO: check if this is this always the same as rank-1?
        """
        return DeckMembership.objects.filter(deck=self.deck, rank__lt=self.rank).count()

    def thumbnail(self):
        return self.image.thumbnail()

    def url(self, **kwargs):
        return self.image.url(**kwargs)


class ImageDeckModelMixin(models.Model):
    """
    Mixin to enable Django models to include an image deck.
    """

    # imagedeck = models.ForeignKey(Deck, on_delete=models.SET_DEFAULT, default=None, null=True, blank=True,)
    imagedeck = models.ForeignKey(
        DeckBase,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
    )  # This is better. It may break dcodex though

    class Meta:
        abstract = True

    def default_imagedeck_name(self):
        """Hook to get a default name for the image deck if it needs to be created."""
        return str(self)

    def get_imagedeck(self):
        """
        Returns the image deck associated with this object.

        Creates the image deck if necessary and saves it to this object.
        """
        if not self.imagedeck:
            self.imagedeck = Deck.objects.create(name=self.default_imagedeck_name())
            self.imagedeck.save()
            self.save()

        return self.imagedeck

    def save_image_file(self, file):
        """
        Saves a new image from a file and adds it to this object's image deck.

        Creates the image deck if necessary.
        """
        imagedeck = self.get_imagedeck()

        return imagedeck.save_image_file(file)

    def get_image_upload_url(self):
        return reverse(
            "imagedeck:upload",
            kwargs={
                "content_type_id": ContentType.objects.get_for_model(self).id,
                "pk": self.pk,
            },
        )
