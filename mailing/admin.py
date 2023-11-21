from django.contrib import admin

from mailing.models import EmailTemplate as _EmailTemplate


@admin.register(_EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Email template admin."""

    list_display = ("email_type", "subject", "is_default")
