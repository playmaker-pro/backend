import factory
import pytest
from django.db.migrations.state import ProjectState
from django.db.models.base import ModelBase

from utils.factories import ClubProfileFactory, UserFactory


@pytest.mark.django_db()
def test_profile_custom_migrations(migrator) -> None:
    """
    Test if migration scripts works correctly:
    - 0100_clubprofile__temporary_field_club_role,
    - 0102_remove_clubprofile__temporary_field_club_role
    """
    old_mapping = dict(
        (
            (1, "Prezes"),
            (2, "Kierownik"),
            (3, "Członek zarządu"),
            (4, "Sztab szkoleniowy"),
            (5, "Trener"),
            (6, "V-ce prezes"),
            (7, "II trener"),
            (8, "Dyrektor sportowy"),
            (9, "Analityk"),
            (10, "Dyrektor skautingu"),
            (11, "Skaut"),
            (12, "Trener bramkarzy"),
            (13, "Koordynator"),
        )
    )
    new_mapping = {**old_mapping, 2: "Kierownik Drużyny"}
    old_state: ProjectState = migrator.apply_initial_migration(
        ("profiles", "0001_squashed_0072_auto_20220627_2313")
    )
    ClubProfile: ModelBase = old_state.apps.get_model("profiles", "ClubProfile")  # noqa

    User: ModelBase = old_state.apps.get_model("users", "User")  # noqa
    user: User = factory.create(User, FACTORY_CLASS=UserFactory)
    user2: User = factory.create(User, FACTORY_CLASS=UserFactory)
    user3: User = factory.create(User, FACTORY_CLASS=UserFactory)
    user4: User = factory.create(User, FACTORY_CLASS=UserFactory)

    first_obj: ClubProfile = factory.create(
        ClubProfile, FACTORY_CLASS=ClubProfileFactory, user=user, club_role=1
    )
    second_obj: ClubProfile = factory.create(
        ClubProfile, FACTORY_CLASS=ClubProfileFactory, user=user2, club_role=2
    )
    third_obj: ClubProfile = factory.create(
        ClubProfile, FACTORY_CLASS=ClubProfileFactory, user=user3, club_role=4
    )
    fourth_obj: ClubProfile = factory.create(
        ClubProfile, FACTORY_CLASS=ClubProfileFactory, user=user4, club_role=None
    )

    assert ClubProfile.objects.count() == 4
    assert ClubProfile.objects.filter(club_role=1).count() == 1

    # Second migration
    new_state: ProjectState = migrator.apply_tested_migration(
        ("profiles", "0100_clubprofile__temporary_field_club_role")
    )
    ClubProfileNewState: ModelBase = new_state.apps.get_model(  # noqa
        "profiles", "ClubProfile"
    )

    first_club: ClubProfile = ClubProfileNewState.objects.get(pk=first_obj.pk)
    second_club: ClubProfile = ClubProfileNewState.objects.get(pk=second_obj.pk)
    third_club: ClubProfile = ClubProfileNewState.objects.get(pk=third_obj.pk)
    fourth_club: ClubProfile = ClubProfileNewState.objects.get(pk=fourth_obj.pk)

    new_mapping_first_role = new_mapping[
        (first_mapped := first_club.club_role)  # noqa: E999
    ]
    new_mapping_second_role = new_mapping[
        (second_mapped := second_club.club_role)  # noqa: E999
    ]
    new_mapping_third_role = new_mapping[
        (third_mapped := third_club.club_role)  # noqa: E999
    ]

    assert first_club._temporary_field_club_role == new_mapping_first_role
    assert second_club._temporary_field_club_role == new_mapping_second_role
    assert third_club._temporary_field_club_role == new_mapping_third_role
    assert fourth_club._temporary_field_club_role is None

    # Third migration
    new_state: ProjectState = migrator.apply_tested_migration(
        ("profiles", "0102_remove_clubprofile__temporary_field_club_role")
    )
    ClubProfileNewState: ModelBase = new_state.apps.get_model(  # noqa
        "profiles", "ClubProfile"
    )

    first_club: ClubProfile = ClubProfileNewState.objects.get(pk=first_obj.pk)
    second_club: ClubProfile = ClubProfileNewState.objects.get(pk=second_obj.pk)
    third_club: ClubProfile = ClubProfileNewState.objects.get(pk=third_obj.pk)
    fourth_club: ClubProfile = ClubProfileNewState.objects.get(pk=fourth_obj.pk)

    assert not getattr(first_club, "_temporary_field_club_role", None)
    assert not getattr(second_club, "_temporary_field_club_role", None)
    assert not getattr(third_club, "_temporary_field_club_role", None)
    assert not getattr(third_club, "_temporary_field_club_role", None)

    assert first_club.club_role == new_mapping[first_mapped]
    assert second_club.club_role == new_mapping[second_mapped]
    assert third_club.club_role == new_mapping[third_mapped]
    assert fourth_club.club_role is None


@pytest.mark.django_db()
def test_0107_1008(migrator) -> None:
    """
    Test migration 0107_auto_20230926_1623,
    ensure that ownership is moved from CoachProfile to User.
    """
    init_state: ProjectState = migrator.apply_initial_migration(
        ("profiles", "0106_alter_licencetype_key")
    )
    User: ModelBase = init_state.apps.get_model("users", "User")
    CoachProfile: ModelBase = init_state.apps.get_model("profiles", "CoachProfile")
    CoachLicence: ModelBase = init_state.apps.get_model("profiles", "CoachLicence")
    LicenceType: ModelBase = init_state.apps.get_model("profiles", "LicenceType")

    user: User = User.objects.create(email="test@test.pl")
    coach: CoachProfile = CoachProfile.objects.create(user_id=user.pk)
    licence_type: LicenceType = LicenceType.objects.filter().first()

    assert licence_type

    licence: CoachLicence = CoachLicence.objects.create(
        coach_profile_id=coach.pk, licence_id=licence_type.pk
    )

    assert licence.coach_profile == coach

    new_state: ProjectState = migrator.apply_tested_migration(
        ("profiles", "0107_auto_20230926_2003")
    )
    CoachLicence: ModelBase = new_state.apps.get_model("profiles", "CoachLicence")
    licence = CoachLicence.objects.get(pk=licence.pk)

    assert licence.owner.pk == coach.user.pk
    assert licence.licence.pk == licence_type.pk

    new_state: ProjectState = migrator.apply_tested_migration(
        ("profiles", "0108_auto_20230926_2004")
    )
    CoachLicence: ModelBase = new_state.apps.get_model("profiles", "CoachLicence")
    licence = CoachLicence.objects.get(pk=licence.pk)

    assert not hasattr(licence, "coach_profile")
    assert licence.owner.pk == coach.user.pk
    assert licence.licence.pk == licence_type.pk

    migrator.reset()
