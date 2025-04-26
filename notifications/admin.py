from django.contrib import admin

from . import models


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    search_fields = (
        "meta__user__first_name",
        "meta__user__last_name",
        "meta__user__email",
    )
    autocomplete_fields = ("target",)
