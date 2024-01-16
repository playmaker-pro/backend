import pytest


@pytest.mark.mute(
    "This test is slow. Mute it by default. Can be run with --allow-skipped flag."
)
@pytest.mark.django_db(transaction=True)
def test_clear_data_migration(migrator) -> None:
    # Apply the initial migration to set the state before the tested migration
    old_state = migrator.apply_initial_migration([("clubs", "0090_auto_20231226_2335")])
    # Fetch model classes using old_state
    Club = old_state.apps.get_model("clubs", "Club")
    Team = old_state.apps.get_model("clubs", "Team")
    TeamHistory = old_state.apps.get_model("clubs", "TeamHistory")
    League = old_state.apps.get_model("clubs", "League")
    LeagueHistory = old_state.apps.get_model("clubs", "LeagueHistory")

    # Create instances using the direct model creation
    for index in range(5):
        club = Club.objects.create(name=f"Club {index}")
        league = League.objects.create(name=f"League {index}")
        team = Team.objects.create(name=f"Team {index}", club=club)
        TeamHistory.objects.create(
            team=team,
        )
        LeagueHistory.objects.create(
            league=league,
        )

    # Apply the clear_data migration
    migrator.apply_tested_migration([("clubs", "0091_clear_data")])

    # Assert that all data is cleared
    assert Club.objects.count() == 0
    assert Team.objects.count() == 0
    assert TeamHistory.objects.count() == 0
    assert League.objects.count() == 0
    assert LeagueHistory.objects.count() == 0
