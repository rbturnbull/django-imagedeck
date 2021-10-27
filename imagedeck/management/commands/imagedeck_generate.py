from django.core.management.base import BaseCommand, CommandError
from imagedeck.models import DeckImageBase


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "widths", nargs="+", type=str, help="The widths to generate."
        )

    def handle(self, *args, **options):

        for image in DeckImageBase.objects.all():
            print(image)
            print("Thumbnail:", image.thumbnail())

            for width in options["widths"]:
                print(f"{width} wide:", image.url(width=width))
