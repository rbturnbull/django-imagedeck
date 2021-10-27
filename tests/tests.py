from django.test import TestCase
from django.template import Context, Template
from django.test import RequestFactory

from .models import TestModel, ImageDeckModel
from .views import TestListView
from django.db import models

from imagedeck.models import Deck, DeckBase, DeckGallica, DeckImageBase, DeckImageIIIF, DeckIIIF
    

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
        self.assertEquals( model2.imagedeck.pk, imagedeck.pk )


class DeckImageIIIFTest(TestCase):
    def setUp(self):
        self.image = DeckImageIIIF.objects.create(base_url="http://www.example.org/image-service/abcd1234")

    def test_url(self):
        self.assertEqual(
            "http://www.example.org/image-service/abcd1234/full/full/0/default.jpg",
            self.image.url(),
        )

    def test_split(self):
        images = self.image.split(width_pct=60)
        self.assertEqual(len(images), 2)
        self.assertEqual(
            "http://www.example.org/image-service/abcd1234/pct:0,0,60,100/full/0/default.jpg",
            images[0].url(),
        )
        self.assertEqual(
            "http://www.example.org/image-service/abcd1234/pct:40,0,100,100/full/0/default.jpg",
            images[1].url(),
        )


class DeckIIIFTest(TestCase):
    def setUp(self):
        self.images = [
            DeckImageIIIF.objects.create(base_url="http://www.example.org/image-service/image1"),
            DeckImageIIIF.objects.create(base_url="http://www.example.org/image-service/image2"),
        ]
        self.deck = DeckIIIF.objects.create(name="Test Deck IIIF")
        for image in self.images:
            self.deck.add_image(image)

    def test_split(self):
        new_deck = self.deck.split(width_pct=60)
        self.assertEqual(new_deck.name, "Test Deck IIIF split width 60")
        images = new_deck.images_ordered()
        gold_urls = [
            "http://www.example.org/image-service/image1/pct:0,0,60,100/full/0/default.jpg",
            "http://www.example.org/image-service/image1/pct:40,0,100,100/full/0/default.jpg",
            "http://www.example.org/image-service/image2/pct:0,0,60,100/full/0/default.jpg",
            "http://www.example.org/image-service/image2/pct:40,0,100,100/full/0/default.jpg",
        ]
        self.assertEqual(len(images), len(gold_urls))
        for image, gold_url in zip(images, gold_urls):
            self.assertEqual(
                gold_url,
                image.url(),
            )




