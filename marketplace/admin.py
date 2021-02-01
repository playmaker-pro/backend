from django.contrib import admin
from . import models 


@admin.register(models.Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    search_fields = ('user__email',)


def reset_plan(modeladmin, request, queryset):
    for ui in queryset:
        ui.reset()  # save comes inside


reset_plan.short_description = "Reset plan"


@admin.register(models.AnnouncementUserQuota)
class AnnouncementUserQuotaAdmin(admin.ModelAdmin):
    search_fields = ('user__email',)
    list_display = ('user', 'plan', 'counter')
    actions = [reset_plan]


@admin.register(models.AnnouncementPlan)
class AnnouncementPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'default', 'limit', 'days')
