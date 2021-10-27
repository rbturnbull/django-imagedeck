from django.core.management.base import BaseCommand, CommandError
from imagedeck.models import Deck


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "destination", type=str, help="The destination folder to store the images."
        )
        parser.add_argument(
            "pattern", type=str, help="The glob pattern to find the images."
        )
        parser.add_argument(
            "--deck",
            type=str,
            help="The name of the image deck. (Default is the name of the destination folder).",
        )
        parser.add_argument("--owner", type=str, help="The username of the folder.")

    def handle(self, *args, **options):
        Deck.import_glob(
            destination=options["destination"],
            pattern=options["pattern"],
            deck_name=options.get("deck"),
            owner=options.get("owner"),
        )
