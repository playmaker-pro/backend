import pytest

from utils.factories import (
    ClubFactory,
    LeagueFactory,
    LeagueHistoryFactory,
    TeamFactory,
    TeamHistoryFactory,
)


@pytest.mark.django_db(transaction=True)
def test_clear_data_migration(migrator) -> None:
    old_state = migrator.apply_initial_migration([
        ("clubs", "0090_auto_20231226_2335")
    ])
    ClubFactory.create_batch(5)
    TeamFactory.create_batch(5)
    TeamHistoryFactory.create_batch(5)
    LeagueFactory.create_batch(5)
    LeagueHistoryFactory.create_batch(5)


    # Create sample data using old state
    Club = old_state.apps.get_model("clubs", "Club")
    Team = old_state.apps.get_model("clubs", "Team")
    TeamHistory = old_state.apps.get_model("clubs", "TeamHistory")
    League = old_state.apps.get_model("clubs", "League")
    LeagueHistory = old_state.apps.get_model("clubs", "LeagueHistory")

    # Apply the clear_data migration
    migrator.apply_tested_migration([
        ("clubs", "0091_clear_data")
    ])

    # Assert all data is cleared
    assert Club.objects.count() == 0
    assert Team.objects.count() == 0
    assert TeamHistory.objects.count() == 0
    assert League.objects.count() == 0
    assert LeagueHistory.objects.count() == 0
