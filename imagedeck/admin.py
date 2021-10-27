from django.contrib import admin
from adminsortable2.admin import SortableInlineAdminMixin
from polymorphic.admin import (
    PolymorphicParentModelAdmin,
    PolymorphicChildModelAdmin,
    PolymorphicChildModelFilter,
)
from filer.admin.imageadmin import ImageAdmin
from filer.models import Image as FilerImage
from .models import *


class DeckMembershipInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DeckMembership
    extra = 0
    raw_id_fields = ("image",)


class DeckMembershipNonSortableInline(admin.TabularInline):
    model = DeckMembership
    extra = 0
    raw_id_fields = ("image",)


class DeckBaseChildAdmin(PolymorphicChildModelAdmin):
    """Base admin class for all child models"""

    base_model = DeckBase
    show_in_index = True  # makes child model admin visible in main admin site
    inlines = (DeckMembershipInline,)


@admin.register(Deck)
class DeckAdmin(DeckBaseChildAdmin):
    base_model = Deck


@admin.register(DeckGallica)
class DeckGallicaAdmin(DeckBaseChildAdmin):
    base_model = DeckGallica


@admin.register(DeckIIIF)
class DeckIIIFAdmin(DeckBaseChildAdmin):
    base_model = DeckIIIF


@admin.register(DeckBase)
class DeckBaseParentAdmin(PolymorphicParentModelAdmin):
    """The parent model admin"""

    base_model = DeckBase  # Optional, explicitly set here.
    child_models = (Deck, DeckGallica, DeckIIIF)
    list_filter = (PolymorphicChildModelFilter,)  # This is optional.


class DeckImageBaseChildAdmin(PolymorphicChildModelAdmin):
    """Base admin class for all child models"""

    base_model = DeckImageBase
    show_in_index = True  # makes child model admin visible in main admin site
    inlines = (DeckMembershipNonSortableInline,)


@admin.register(DeckImage)
class DeckImageAdmin(DeckImageBaseChildAdmin):
    base_model = DeckImage


@admin.register(DeckImageFiler)
class DeckImageAdmin(DeckImageBaseChildAdmin):
    base_model = DeckImageFiler


@admin.register(DeckImageIIIF)
class DeckImageIIIFAdmin(DeckImageBaseChildAdmin):
    base_model = DeckImageIIIF


@admin.register(DeckImageExternal)
class DeckImageExternalAdmin(DeckImageBaseChildAdmin):
    base_model = DeckImageExternal


@admin.register(DeckImageBase)
class DeckImageBaseParentAdmin(PolymorphicParentModelAdmin):
    """The parent model admin"""

    base_model = DeckImageBase  # Optional, explicitly set here.
    child_models = (DeckImage, DeckImageFiler, DeckImageIIIF, DeckImageExternal)
    list_filter = (PolymorphicChildModelFilter,)  # This is optional.


@admin.register(DeckLicence)
class DeckLicenceAdmin(admin.ModelAdmin):
    pass


class DeckImageFilerInline(admin.StackedInline):
    model = DeckImageFiler
    can_delete = False
    verbose_name_plural = "Deck Image"
    fk_name = "filer_image"


class CustomFilerImageAdmin(ImageAdmin):
    inlines = (DeckImageFilerInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomFilerImageAdmin, self).get_inline_instances(request, obj)


admin.site.unregister(FilerImage)
admin.site.register(FilerImage, CustomFilerImageAdmin)
