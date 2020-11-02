from django.db import models

class TestModel(models.Model):
    class Meta:
        ordering = ['pk',]
