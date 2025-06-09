from django.contrib import admin

from transfers import models


@admin.register(models.ProfileTransferStatus)
class ProfileTransferStatusAdmin(admin.ModelAdmin):
    """Admin for ProfileTransferStatus model."""

    # list_display = (
    #     "pk",
    #     "get_user_email",
    #     "get_content_type",
    #     "get_profile_uuid",
    #     "profile_type",
    #     "created_at",
    #     "updated_at",
    # )


@admin.register(models.ProfileTransferRequest)
class ProfileTransferRequestAdmin(admin.ModelAdmin):
    """Admin for ProfileTransferRequest model."""

    # list_display = (
    #     "pk",
    #     "get_user_email",
    #     "get_content_type",
    #     "get_profile_uuid",
    #     "profile_type",
    #     "created_at",
    #     "updated_at",
    #     "voivodeship",
    # )
