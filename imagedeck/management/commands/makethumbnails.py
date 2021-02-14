from django.core.management.base import BaseCommand, CommandError
from imagedeck.models import DeckImageBase


class Command(BaseCommand):
    def handle(self, *args, **options):

        for image in DeckImageBase.objects.all():
            print(image.thumbnail())