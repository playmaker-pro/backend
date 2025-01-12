from django.contrib import admin

from . import models


@admin.action(description="Update PM Score")
def update_pm_score(modeladmin, request, queryset):
    for record in queryset:
        player = record.player
        player.refresh_scoring()

        player.refresh_from_db()
        current_score = player.playermetrics.pm_score

        record.approve(request.user, current_score)


@admin.action(description="Refresh product(s)")
def refresh_product(modeladmin, request, queryset):
    for record in queryset:
        record.refresh()


@admin.register(models.CalculatePMScoreProduct)
class CalculatePMScoreProductAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "created_at",
        "updated_at",
        "approved_by",
        "old_value",
        "new_value",
        "awaiting_approval",
    )
    autocomplete_fields = ("player",)
    search_fields = ("player",)
    actions = [update_pm_score, refresh_product]


@admin.register(models.PromoteProfileProduct)
class PromoteProfileProductAdmin(admin.ModelAdmin):
    list_display = ("profile_object", "valid_since", "valid_until")
    actions = ("refresh_product",)

    def profile_object(self, obj):
        return obj.product.profile


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "visible",
        "ref",
        "price",
    )
    list_filter = ("visible", "ref")
    search_fields = ("name", "ref")


@admin.register(models.PremiumProfile)
class PremiumProfileAdmin(admin.ModelAdmin): ...


@admin.register(models.PremiumProduct)
class PremiumProductAdmin(admin.ModelAdmin): ...
