import pytest
from django.db.migrations.state import ProjectState
from django.db.models.base import ModelBase


@pytest.mark.django_db()
def test_user_preferences_migration(migrator) -> None:
    """
    Test if migration script for UserPreferences works correctly.
    Specifically, testing the 0010_auto_20230918_0219 migration.
    """

    # Initial state and model creation
    init_state = migrator.apply_initial_migration(
        ("users", "0009_alter_userpreferences_citizenship")
    )

    PlayerProfile = init_state.apps.get_model("profiles", "PlayerProfile")
    CoachProfile = init_state.apps.get_model("profiles", "CoachProfile")
    ScoutProfile = init_state.apps.get_model("profiles", "ScoutProfile")
    User = init_state.apps.get_model("users", "User")
    UserPreferences = init_state.apps.get_model("users", "UserPreferences")

    # Create User instances directly
    user1 = User.objects.create(email="player@example.com", username="playerUser")
    user2 = User.objects.create(email="coach@example.com", username="coachUser")
    user3 = User.objects.create(email="scout@example.com", username="scoutUser")

    player = PlayerProfile.objects.create(country="PL", user=user1)
    UserPreferences.objects.create(user=player.user)

    coach = CoachProfile.objects.create(country="ES", user=user2)
    UserPreferences.objects.create(user=coach.user)

    scout = ScoutProfile.objects.create(country="DE", user=user3)
    UserPreferences.objects.create(user=scout.user)

    # Apply the tested migration
    new_state: ProjectState = migrator.apply_tested_migration(
        ("users", "0010_auto_20230918_0219")
    )
    UserPreferencesNewState: ModelBase = new_state.apps.get_model(  # noqa
        "users", "UserPreferences"
    )

    # Assertions
    player_prefs = UserPreferencesNewState.objects.get(user_id=player.user.id)
    assert player_prefs.citizenship == ["PL"]
    assert player_prefs.spoken_languages.count() == 1
    assert player_prefs.spoken_languages.first().code == "pl"

    coach_prefs = UserPreferencesNewState.objects.get(user_id=coach.user.id)
    assert coach_prefs.citizenship == ["ES"]
    assert coach_prefs.spoken_languages.count() == 1
    assert coach_prefs.spoken_languages.first().code == "es"

    scout_prefs = UserPreferencesNewState.objects.get(user_id=scout.user.id)
    assert scout_prefs.citizenship == ["DE"]
    assert scout_prefs.spoken_languages.count() == 1
    assert scout_prefs.spoken_languages.first().code == "de"
