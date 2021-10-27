# Generated by Django 3.2.6 on 2021-09-01 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("imagedeck", "0010_deckiiif"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="deckbase",
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="deckimageiiif",
            name="region",
            field=models.CharField(
                default="full",
                help_text="A way to crop the region of an image. In the form of 'full', 'x,y,w,h' or 'pct:x,y,w,h'.",
                max_length=255,
            ),
        ),
    ]
