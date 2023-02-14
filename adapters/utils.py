from pm_core.services.models import PlayerSeasonStatsSchema, PlayersSeasonStatsSchema


def resolve_stats_list(
    stats: PlayersSeasonStatsSchema,
) -> PlayerSeasonStatsSchema:
    """get most accurate stats based on played minutes in different leagues"""
    return max(stats, key=lambda obj: obj.minutes_played)
