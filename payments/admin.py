from django.contrib import admin

from payments import models as _models


@admin.register(_models.Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "user",
        "transaction_type_readable_name",
        "transaction_status",
        "created_at",
        "updated_at",
    )
