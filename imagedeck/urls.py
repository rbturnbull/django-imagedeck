from django.urls import path, include

from . import views
from .models import *
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.urls import reverse_lazy

app_name = "imagedeck"
urlpatterns = [
    path(
        "image-upload/<int:content_type_id>/<int:pk>/",
        views.image_upload,
        name="upload",
    ),
]
