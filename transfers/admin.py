from django.contrib import admin

from transfers import models
from utils.functions import linkify


@admin.register(models.ProfileTransferStatus)
class ProfileTransferStatusAdmin(admin.ModelAdmin):
    """Admin for ProfileTransferStatus model."""

    list_display = (
        "pk",
        linkify("meta"),
        "created_at",
        "updated_at",
    )

    search_fields = (
        "meta__user__email",
        "meta__user__first_name",
        "meta__user__last_name",
    )
    autocomplete_fields = ("meta",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "anonymous_uuid",
    )


@admin.register(models.ProfileTransferRequest)
class ProfileTransferRequestAdmin(admin.ModelAdmin):
    """Admin for ProfileTransferRequest model."""

    list_display = (
        "pk",
        linkify("meta"),
        "created_at",
        "updated_at",
        "voivodeship",
    )

    search_fields = (
        "meta__user__email",
        "meta__user__first_name",
        "meta__user__last_name",
    )
    autocomplete_fields = ("meta",)
