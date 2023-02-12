import typing
from pm_core.services.models import PlayerSeasonStatsSchema


def resolve_stats_list(
    stats: typing.List[PlayerSeasonStatsSchema],
) -> PlayerSeasonStatsSchema:
    """get most accurate stats based on played minutes in different leagues"""
    return max(stats, key=lambda obj: obj.minutes_played)
