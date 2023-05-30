from django.contrib import admin
from . import models


@admin.register(models.PremiumRequest)
class PremiumRequestAdmin(admin.ModelAdmin):
    ...
