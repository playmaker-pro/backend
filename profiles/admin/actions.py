from notifications.services import NotificationService


def trigger_refresh_data_player_stats(modeladmin, request, queryset):
    for pp in queryset:
        pp.trigger_refresh_data_player_stats()  # save comes inside


trigger_refresh_data_player_stats.short_description = (
    "1. Refresh metric data_player on -->  s38"
)


def calculate_metrics(modeladmin, request, queryset):
    for pp in queryset:
        pp.playermetrics.refresh_metrics()  # save comes inside


calculate_metrics.short_description = "2. Calculate Playermeteics <-- s38"


def calculate_fantasy(modeladmin, request, queryset):
    for pp in queryset:
        pp.calculate_fantasy_object()  # save comes inside


calculate_fantasy.short_description = "Calculate fantasy"


def fetch_data_player_meta(modeladmin, request, queryset):
    for pp in queryset:
        pp.fetch_data_player_meta()  # save comes inside


fetch_data_player_meta.short_description = "3. update meta  <--- s38"


def set_team_object_based_on_meta(modeladmin, request, queryset):
    for pp in queryset:
        pp.set_team_object_based_on_meta()  # save comes inside


set_team_object_based_on_meta.short_description = "4. set team_object based on .meta"


def refresh(modeladmin, request, queryset):
    for pp in queryset:
        pp.trigger_refresh_data_player_stats()  # save not relevant
        pp.fetch_data_player_meta(save=False)  # save comes inside
        pp.set_team_object_based_on_meta()  # saving
        pp.playermetrics.refresh_metrics()  # save not relevant


refresh.short_description = "0. Refresh( 1, 2,3,4 )"


def update_with_profile_data(modeladmin, request, queryset):
    for ver in queryset:
        ver.update_with_profile_data(requestor=request.user)


update_with_profile_data.short_description = (
    "Updated selected verification object with Profles data"
)


def update_pm_score(modeladmin, request, queryset) -> None:
    """Update PlayMaker Score only"""
    for player_profile in queryset:
        player_profile.playermetrics.get_and_update_pm_score()


update_pm_score.short_description = "Update PlayMaker Score"


def update_season_score(modeladmin, request, queryset) -> None:
    """Update Season Score only"""
    for player_profile in queryset:
        player_profile.playermetrics.get_and_update_season_score()


update_season_score.short_description = "Update Season Score"


def update_scoring(modeladmin, request, queryset) -> None:
    """Update everything related with scoring"""
    for player_profile in queryset:
        player_profile.refresh_scoring()


update_scoring.short_description = "Update scoring (PlayMaker, Season, .etc score)"


def bind_reccurrent_notifications(modeladmin, request, queryset) -> None:
    """
    Bind notifications to the selected profiles.
    """
    for profile_meta in queryset:
        NotificationService(profile_meta).bind_all_reccurrent_notifications()
