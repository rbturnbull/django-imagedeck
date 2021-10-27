from django.core.management.base import BaseCommand, CommandError
from imagedeck.models import Deck


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "new_deck",
            type=str,
            help="The name of the deck to combine all the other decks.",
        )
        parser.add_argument(
            "decks_to_combine",
            nargs="+",
            type=str,
            help="The name of the other decks to combine.",
        )

    def handle(self, *args, **options):
        Deck.combine(
            new_deck=options["new_deck"], decks_to_combine=options["decks_to_combine"]
        )
