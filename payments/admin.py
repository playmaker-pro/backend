import datetime

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils import timezone

from payments import models as _models


class CreatedAtFilter(SimpleListFilter):
    title = "Created At"
    parameter_name = "created_at"

    def lookups(self, request, model_admin):
        return (
            ("today", "Today"),
            ("last_week", "Last Week"),
            ("last_month", "Last Month"),
            ("last_year", "Last Year"),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == "today":
            return queryset.filter(created_at__date=now.date())
        if self.value() == "last_week":
            start_of_last_week = now - datetime.timedelta(days=now.weekday() + 7)
            end_of_last_week = start_of_last_week + datetime.timedelta(days=6)
            return queryset.filter(
                created_at__gte=start_of_last_week, created_at__lte=end_of_last_week
            )
        if self.value() == "last_month":
            first_day_of_current_month = now.replace(day=1)
            last_day_of_last_month = first_day_of_current_month - datetime.timedelta(
                days=1
            )
            start_of_last_month = last_day_of_last_month.replace(day=1)
            return queryset.filter(
                created_at__gte=start_of_last_month,
                created_at__lte=last_day_of_last_month,
            )
        if self.value() == "last_year":
            start_of_last_year = now.replace(year=now.year - 1, month=1, day=1)
            end_of_last_year = now.replace(year=now.year - 1, month=12, day=31)
            return queryset.filter(
                created_at__gte=start_of_last_year, created_at__lte=end_of_last_year
            )
        return queryset


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
    list_filter = ("product__ref", "transaction_status", CreatedAtFilter)
