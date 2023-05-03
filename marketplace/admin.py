from django.contrib import admin

from utils import linkify

from . import models


@admin.register(models.PlayerForClubAnnouncement)
class PlayerForClubAnnouncementAdmin(admin.ModelAdmin):
    search_fields = ("user__email",)


@admin.register(models.ClubForPlayerAnnouncement)
class ClubForPlayerAnnouncementAdmin(admin.ModelAdmin):
    search_fields = ("user__email",)


@admin.register(models.ClubForCoachAnnouncement)
class ClubForCoachAnnouncementAdmin(admin.ModelAdmin):
    search_fields = ("user__email",)


@admin.register(models.CoachForClubAnnouncement)
class CoachForClubAnnouncementAdmin(admin.ModelAdmin):
    search_fields = ("user__email",)


def reset_plan(modeladmin, request, queryset):
    for ui in queryset:
        ui.reset()  # save comes inside


reset_plan.short_description = "Reset plan"


@admin.register(models.AnnouncementUserQuota)
class AnnouncementUserQuotaAdmin(admin.ModelAdmin):
    search_fields = ("user__email",)
    list_display = ("user", linkify("plan"), "counter")
    actions = [reset_plan]


@admin.register(models.AnnouncementPlan)
class AnnouncementPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "default", "limit", "days")
