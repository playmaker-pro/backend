from django.contrib import admin
from . import models


@admin.register(models.InquiryPlan)
class InquiryPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "default", "limit")


def reset_plan(modeladmin, request, queryset):
    for ui in queryset:
        ui.reset()  # save comes inside


reset_plan.short_description = "Reset plan"


@admin.register(models.UserInquiry)
class UserInquiryAdmin(admin.ModelAdmin):
    search_fields = ("user__email",)
    list_display = ("user", "plan", "counter")
    actions = [reset_plan]


@admin.register(models.InquiryRequest)
class InquiryRequestAdmin(admin.ModelAdmin):
    search_fields = (
        "recipient__email",
        "sender__email",
        "sender__username",
        "sender__first_name",
        "sender__last_name",
        "recipient__username",
        "recipient__first_name",
        "recipient__last_name",
    )
    list_display = (
        "sender",
        "status",
        "recipient",
        "created_at",
        "category",
        "body",
        "body_recipient",
    )
