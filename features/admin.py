from django.contrib import admin

from features.models import FeatureElement


@admin.register(FeatureElement)
class FeatureElementAdmin(admin.ModelAdmin):
    ...
