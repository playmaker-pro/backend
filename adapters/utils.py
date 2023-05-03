from pm_core.services.models import PlayerSeasonStatsListSchema, PlayerSeasonStatsSchema


def resolve_stats_list(
    stats: PlayerSeasonStatsListSchema,
) -> PlayerSeasonStatsSchema:
    """get most accurate stats based on played minutes in different leagues"""
    if stats:
        return max(stats, key=lambda obj: obj.minutes_played)
