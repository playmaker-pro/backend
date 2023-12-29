import pytest
from django.apps import apps


@pytest.mark.django_db(transaction=True)
def test_clear_data_migration(migrator) -> None:
    """
     Tests the 'clear_data' migration in the 'followers' app to ensure it correctly
     clears all data from the FollowTeam table.
    """
    old_state = migrator.apply_initial_migration([('followers', '0003_followteam')])

    # Get the old state models
    FollowTeam = old_state.apps.get_model("followers", "FollowTeam")
    User = old_state.apps.get_model("users", "User")
    Team = old_state.apps.get_model("clubs", "Team")

    user = User.objects.create(username="testuser")
    team = Team.objects.create(name="Test Team")
    for _ in range(5):
        FollowTeam.objects.create(user=user, target=team)

    # Apply the tested migration
    migrator.apply_tested_migration([('followers', '0004_follow_team_clear_data')])

    # Get the FollowTeam model from the new state after migration
    FollowTeam = apps.get_model("followers", "FollowTeam")

    # Assert that all data is cleared
    assert FollowTeam.objects.count() == 0
