from django.test import TestCase
from django.template import Context, Template
from django.test import RequestFactory

from .models import TestModel, ImageDeckModel
from .views import TestListView
from django.db import models

from imagedeck.models import Deck, DeckBase, DeckGallica, DeckImageBase
    

class DeckTest(TestCase):
    def test_create(self):
        deck_base = DeckBase.objects.create(name="test deck2")        
        deck = Deck.objects.create(name="test deck")        
        deck_gallica = DeckGallica.objects.create(name='DeckGallica', base_url="http://www.example.com")

        self.assertEquals( DeckBase.objects.count(), 3 )        
        self.assertEquals( Deck.objects.count(), 1 )        
        self.assertEquals( DeckGallica.objects.count(), 1 )        


class ImageDeckModelTest(TestCase):
    def setUp(self):
        self.model = ImageDeckModel.objects.create()
        
    def test_get_imagedeck(self):
        imagedeck = self.model.get_imagedeck()
        self.assertEquals( str(imagedeck), "ImageDeckModel object (1)" )
        self.assertEquals( type(imagedeck), Deck )

        model2 = ImageDeckModel.objects.get(pk=self.model.pk)
        self.assertEquals( model2.image_deck.pk, imagedeck.pk )