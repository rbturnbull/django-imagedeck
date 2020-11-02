from django.test import TestCase
from django.template import Context, Template
from django.test import RequestFactory

from .models import TestModel
from .views import TestListView

class ImagedeckTest(TestCase):
    def setUp(self):
        pass
        
