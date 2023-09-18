from django.contrib import admin

from features.models import AccessPermission, Feature, FeatureElement


@admin.register(AccessPermission)
class AccessPermissionAdmin(admin.ModelAdmin):
    ...


@admin.register(FeatureElement)
class FeatureElementAdmin(admin.ModelAdmin):
    ...


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    ...
