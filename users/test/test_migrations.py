import pytest
from django.db.migrations.state import ProjectState
from django.db.models.base import ModelBase
from utils.factories import (
    PlayerProfileFactory,
    CoachProfileFactory,
    ScoutProfileFactory,
    UserPreferencesFactory,
)


@pytest.mark.django_db()
def test_user_preferences_migration(migrator) -> None:
    """
    Test if migration script for UserPreferences works correctly.
    Specifically, testing the 0010_auto_20230918_0219 migration.
    """

    # Initial state and model creation
    old_state: ProjectState = migrator.apply_initial_migration(
        ("users", "0009_alter_userpreferences_citizenship")
    )

    # Using factories for data creation before migration
    player = PlayerProfileFactory(country="PL")
    player_preferences = UserPreferencesFactory(user=player.user)

    coach = CoachProfileFactory(country="ES")
    coach_preferences = UserPreferencesFactory(user=coach.user)

    scout = ScoutProfileFactory(country="DE")
    scout_preferences = UserPreferencesFactory(user=scout.user)
    new_state: ProjectState = migrator.apply_tested_migration(
        ("users", "0010_auto_20230918_0219")
    )
    UserPreferencesNewState: ModelBase = new_state.apps.get_model(
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
