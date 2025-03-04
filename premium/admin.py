from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.urls import reverse
from django.utils.html import format_html

from utils import linkify

from . import models
from .models import PremiumType


@admin.action(description="Update PM Score")
def update_pm_score(modeladmin, request, queryset):
    for record in queryset:
        player = record.player
        player.refresh_scoring()

        player.refresh_from_db()
        current_score = player.playermetrics.pm_score

        record.approve(request.user, current_score)


@admin.register(models.CalculatePMScoreProduct)
class CalculatePMScoreProductAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        linkify("player"),
        "player_team",
        "metrics",
        "created_at",
        "updated_at",
        "product_name",
        "old_value",
        "new_value",
        "done",
    )
    autocomplete_fields = ("player", "product", "approved_by")
    search_fields = ("player__user__first_name", "player__user__last_name")
    actions = [update_pm_score]
    list_filter = ("player__team_object__league",)
    exclude = ("old_value", "new_value", "approved_by")
    readonly_fields = ("product", "metrics")
    ordering = ("updated_at",)

    def product_name(self, obj):
        return PremiumType.get_period_type(obj.product.premium.period)

    def product_expiration_date(self, obj):
        return obj.product.premium.valid_until

    def done(self, obj):
        return not obj.awaiting_approval

    def player_team(self, obj):
        if team := obj.player.team_object:
            view_name = (
                f"admin:{team._meta.app_label}_"  # noqa
                f"{team.__class__.__name__.lower()}_change"
            )
            link_url = reverse(view_name, args=[team.pk])
            return format_html(f'<a href="{link_url}">{team}</a>')

    def metrics(self, obj):
        if obj.product.profile and obj.product.profile.playermetrics:
            metrics = obj.product.profile.playermetrics
            view_name = (
                f"admin:{metrics._meta.app_label}_"  # noqa
                f"{metrics.__class__.__name__.lower()}_change"
            )
            link_url = reverse(view_name, args=[metrics.pk])
            return format_html(f'<a href="{link_url}">{metrics}</a>')

    def has_change_permission(self, request, obj=None):
        return False

    done.short_description = "Done?"
    done.boolean = True


@admin.register(models.PromoteProfileProduct)
class PromoteProfileProductAdmin(admin.ModelAdmin):
    list_display = (
        "profile_object",
        linkify("product"),
        "product_name",
        "valid_since",
        "valid_until",
        "is_active",
        "days_left",
    )
    readonly_fields = ("product",)
    autocomplete_fields = ("product",)
    exclude = ("days_count",)
    search_fields = ("product__user__first_name", "product__user__last_name")

    def profile_object(self, obj):
        return obj.product.profile

    def product_name(self, obj):
        if obj.is_active:
            return PremiumType.get_period_type(obj.product.premium.period)


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
class PremiumProfileAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "profile_object",
        "joined",
        "product_name",
        "is_trial",
        "valid_since",
        "valid_until",
        "is_active",
    )
    list_filter = ("is_trial",)
    search_fields = ("product__user__first_name", "product__user__last_name")
    autocomplete_fields = ("product",)

    readonly_fields = ("period", "product")

    def profile_object(self, obj):
        if profile := obj.product.profile:
            view_name = (
                f"admin:{profile._meta.app_label}_"  # noqa
                f"{profile.__class__.__name__.lower()}_change"
            )
            link_url = reverse(view_name, args=[profile.pk])
            return format_html(f'<a href="{link_url}">{profile}</a>')

    def joined(self, obj):
        if obj.product.user:
            return obj.product.user.date_joined

    def product_name(self, obj):
        if obj.is_active:
            return PremiumType.get_period_type(obj.period)


@admin.register(models.PremiumProduct)
class PremiumProductAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "is_premium_inquiries_active",
        "is_profile_premium",
        "is_profile_promoted",
        "trial_tested",
    )
    search_fields = ("user__first_name", "user__last_name")
    autocomplete_fields = ("user",)
    readonly_fields = ("user",)


@admin.register(models.PremiumInquiriesProduct)
class PremiumInquiriesProductAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "valid_since",
        "valid_until",
        "is_active",
        "product_name",
        "current_counter",
        "counter_updated_at",
        "inquiries_refreshed_at",
    )
    search_fields = (
        "product__user__first_name",
        "product__user__last_name",
    )
    autocomplete_fields = ("product",)
    readonly_fields = ("product",)

    def product_name(self, obj):
        if obj.is_active:
            return PremiumType.get_period_type(obj.product.premium.period)
