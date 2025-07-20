from django.contrib import admin

from mailing.models import UserEmailOutbox as _UserEmailOutbox





@admin.register(_UserEmailOutbox)
class UserEmailOutboxAdmin(admin.ModelAdmin):
    """User email outbox admin."""
