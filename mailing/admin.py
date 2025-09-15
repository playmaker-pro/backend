from django.contrib import admin

from mailing import models


class MailLogInline(admin.TabularInline):
    model = models.MailLog
    extra = 0
    readonly_fields = ("id", "subject", "sent_at", "status")
    fields = ("id", "subject", "sent_at", "status")
    can_delete = False


@admin.register(models.MailLog)
class MailLogAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "sent_at")
    search_fields = (
        "subject",
        "mailing__user__email",
        "mailing__user__first_name",
        "mailing__user__last_name",
    )

    autocomplete_fields = ("mailing",)


@admin.register(models.Mailing)
class MailingAdmin(admin.ModelAdmin):
    search_fields = ("user__email", "user__first_name", "user__last_name")
    autocomplete_fields = ("user",)
    inlines = [MailLogInline]
