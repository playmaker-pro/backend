from django.contrib import admin
from . import models 


@admin.register(models.Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    pass 


@admin.register(models.AnnouncementUserQuota)
class AnnouncementUserQuotaAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AnnouncementPlan)
class AnnouncementPlanAdmin(admin.ModelAdmin):
    pass
