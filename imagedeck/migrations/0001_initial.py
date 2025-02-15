# Generated by Django 3.0.9 on 2020-11-02 01:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeckBase",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(default="", max_length=255)),
                (
                    "polymorphic_ctype",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="polymorphic_imagedeck.deckbase_set+",
                        to="contenttypes.ContentType",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
        ),
        migrations.CreateModel(
            name="DeckImageBase",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
        ),
        migrations.CreateModel(
            name="DeckLicense",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "logo",
                    models.CharField(
                        help_text="A URL for the image of the logo of this licence.",
                        max_length=1023,
                    ),
                ),
                (
                    "info",
                    models.CharField(
                        help_text="A URL for more information about this licence.",
                        max_length=1023,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Deck",
            fields=[
                (
                    "deckbase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="imagedeck.DeckBase",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("imagedeck.deckbase",),
        ),
        migrations.CreateModel(
            name="DeckGallica",
            fields=[
                (
                    "deckbase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="imagedeck.DeckBase",
                    ),
                ),
                ("base_url", models.CharField(max_length=1023)),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("imagedeck.deckbase",),
        ),
        migrations.CreateModel(
            name="DeckImage",
            fields=[
                (
                    "deckimagebase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="imagedeck.DeckImageBase",
                    ),
                ),
                ("image", models.ImageField(upload_to="")),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("imagedeck.deckimagebase",),
        ),
        migrations.CreateModel(
            name="DeckImageExternal",
            fields=[
                (
                    "deckimagebase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="imagedeck.DeckImageBase",
                    ),
                ),
                ("external_url", models.CharField(max_length=1023)),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("imagedeck.deckimagebase",),
        ),
        migrations.CreateModel(
            name="DeckImageIIIF",
            fields=[
                (
                    "deckimagebase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="imagedeck.DeckImageBase",
                    ),
                ),
                ("base_url", models.CharField(max_length=1023)),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("imagedeck.deckimagebase",),
        ),
        migrations.CreateModel(
            name="DeckMembership",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "rank",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="The rank of the image in the ordering of the deck.",
                    ),
                ),
                (
                    "deck",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="imagedeck.DeckBase",
                    ),
                ),
                (
                    "image",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="imagedeck.DeckImageBase",
                    ),
                ),
            ],
            options={
                "ordering": ("rank", "deck"),
            },
        ),
        migrations.AddField(
            model_name="deckimagebase",
            name="license",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_DEFAULT,
                to="imagedeck.DeckLicense",
            ),
        ),
        migrations.AddField(
            model_name="deckimagebase",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_imagedeck.deckimagebase_set+",
                to="contenttypes.ContentType",
            ),
        ),
    ]
