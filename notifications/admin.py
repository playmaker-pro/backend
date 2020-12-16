from django.contrib import admin

from . import models


@admin.register(models.NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    pass
