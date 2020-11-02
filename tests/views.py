from django.views.generic import (
    CreateView,
    UpdateView,
    DetailView,
    ListView,
    DeleteView,
    FormView,
)
from .models import TestModel



class TestListView(ListView):
    model = TestModel
    paginate_by = 10
