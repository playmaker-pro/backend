from django.contrib import admin
from . import models 


@admin.register(models.Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    search_fields = ('user__email',)


@admin.register(models.AnnouncementUserQuota)
class AnnouncementUserQuotaAdmin(admin.ModelAdmin):
    search_fields = ('user__email',)
    list_display = ('user', 'plan', 'counter')


@admin.register(models.AnnouncementPlan)
class AnnouncementPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'default', 'limit', 'days')
