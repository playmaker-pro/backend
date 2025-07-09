import pytest
from django.contrib.auth import get_user_model

from utils.factories.profiles_factories import PlayerProfileFactory

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_profile_should_be_hidden() -> None:
    same_name = PlayerProfileFactory.create(
        user__first_name="foo", user__last_name="foo"
    )
    no_name = PlayerProfileFactory.create(user__first_name="", user__last_name="")

    assert same_name.user.display_status == User.DisplayStatus.NOT_SHOWN
    assert no_name.user.display_status == User.DisplayStatus.NOT_SHOWN
    assert same_name.meta.notifications.filter(
        title="Profil tymczasowo ukryty"
    ).exists()
    assert no_name.meta.notifications.filter(title="Profil tymczasowo ukryty").exists()


def test_profile_should_not_be_hidden() -> None:
    """
    Test that profiles with different first and last names are not hidden.
    """
    profile = PlayerProfileFactory.create(
        user__first_name="John", user__last_name="Doe"
    )

    assert profile.user.display_status != User.DisplayStatus.NOT_SHOWN
    assert not profile.meta.notifications.filter(
        title="Profil tymczasowo ukryty"
    ).exists()
