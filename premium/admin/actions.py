from django.contrib import admin

from premium.models import PremiumType


@admin.action(description="Update PM Score")
def update_pm_score(modeladmin, request, queryset):
    for record in queryset:
        player = record.player
        player.refresh_scoring()

        player.refresh_from_db()
        current_score = player.playermetrics.pm_score

        record.approve(request.user, current_score)


@admin.action(description="Activate 1 MONTH premium")
def activate_1_month_premium(modeladmin, request, queryset):
    for pp in queryset:
        pp.setup_premium_profile(PremiumType.MONTH)


@admin.action(description="Activate 1 DAY premium")
def activate_1_day_premium(modeladmin, request, queryset):
    for pp in queryset:
        pp.setup_premium_profile(PremiumType.CUSTOM, 1)


@admin.action(description="Activate 10 DAYS premium")
def activate_10_days_premium(modeladmin, request, queryset):
    for pp in queryset:
        pp.setup_premium_profile(PremiumType.CUSTOM, 10)


@admin.action(description="Activate 1 YEAR premium")
def activate_1_year_premium(modeladmin, request, queryset):
    for pp in queryset:
        pp.setup_premium_profile(PremiumType.YEAR)
