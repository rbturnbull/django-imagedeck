from django.contrib import admin
from adminsortable2.admin import SortableInlineAdminMixin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter
from .models import * 


class DeckMembershipInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DeckMembership
    extra = 0


class DeckMembershipNonSortableInline(admin.TabularInline):
    model = DeckMembership
    extra = 0

class DeckBaseChildAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all child models """
    base_model = DeckBase
    show_in_index = True  # makes child model admin visible in main admin site
    inlines = (DeckMembershipInline,)


@admin.register(Deck)
class DeckAdmin(DeckBaseChildAdmin):
    base_model = Deck


@admin.register(DeckGallica)
class DeckGallicaAdmin(DeckBaseChildAdmin):
    base_model = DeckGallica


@admin.register(DeckBase)
class DeckBaseParentAdmin(PolymorphicParentModelAdmin):
    """ The parent model admin """
    base_model = DeckBase  # Optional, explicitly set here.
    child_models = (Deck, DeckGallica)
    list_filter = (PolymorphicChildModelFilter,)  # This is optional.


class DeckImageBaseChildAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all child models """
    base_model = DeckImageBase
    show_in_index = True  # makes child model admin visible in main admin site
    inlines = (DeckMembershipNonSortableInline,)


@admin.register(DeckImage)
class DeckImageAdmin(DeckImageBaseChildAdmin):
    base_model = DeckImage


@admin.register(DeckImageIIIF)
class DeckImageIIIFAdmin(DeckImageBaseChildAdmin):
    base_model = DeckImageIIIF


@admin.register(DeckImageExternal)
class DeckImageExternalAdmin(DeckImageBaseChildAdmin):
    base_model = DeckImageExternal


@admin.register(DeckImageBase)
class DeckImageBaseParentAdmin(PolymorphicParentModelAdmin):
    """ The parent model admin """
    base_model = DeckImageBase  # Optional, explicitly set here.
    child_models = (DeckImage, DeckImageIIIF, DeckImageExternal)
    list_filter = (PolymorphicChildModelFilter,)  # This is optional.

@admin.register(DeckLicence)
class DeckLicenceAdmin(admin.ModelAdmin):
    pass