from django.contrib import admin

from mailing.models import EmailTemplate as _EmailTemplate
from mailing.models import UserEmailOutbox as _UserEmailOutbox


@admin.register(_EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Email template admin."""

    list_display = ("email_type", "subject", "is_default")


@admin.register(_UserEmailOutbox)
class UserEmailOutboxAdmin(admin.ModelAdmin):
    """User email outbox admin."""
