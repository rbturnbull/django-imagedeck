# Generated by Django 3.0.9 on 2020-11-02 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("imagedeck", "0003_deckbase_images"),
    ]

    operations = [
        migrations.AddField(
            model_name="deckimageiiif",
            name="height",
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name="deckimageiiif",
            name="width",
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
    ]
