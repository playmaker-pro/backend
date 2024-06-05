from django.contrib import admin

from . import models


@admin.register(models.InquiryPlan)
class InquiryPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "default", "limit")


def reset_plan(modeladmin, request, queryset):
    for ui in queryset:
        ui.reset()  # save comes inside


def reset_inquiries(modeladmin, request, queryset):
    for ui in queryset:
        ui.reset_inquiries()


reset_plan.short_description = "Reset plan"
reset_inquiries.short_description = "Reset inquiries"


@admin.register(models.UserInquiry)
class UserInquiryAdmin(admin.ModelAdmin):
    search_fields = ("user__email",)
    list_display = ("user", "plan", "counter")
    actions = [reset_plan, reset_inquiries]
    autocomplete_fields = ("user",)


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
    )
    autocomplete_fields = (
        "sender",
        "recipient",
    )


@admin.register(models.InquiryLogMessage)
class InquiryLogMessageAdmin(admin.ModelAdmin):
    ...


@admin.register(models.UserInquiryLog)
class UserInquiryLogAdmin(admin.ModelAdmin):
    search_fields = ("log_owner__user__email",)
    autocomplete_fields = ("log_owner", "related_with", "ref")
