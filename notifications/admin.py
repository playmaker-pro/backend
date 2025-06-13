from django.contrib import admin

from . import models


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    search_fields = (
        "target__user__first_name",
        "target__user__last_name",
        "target__user__email",
    )
    autocomplete_fields = ("target",)
