import pytest
from django.contrib.auth import get_user_model

from mailing.utils import build_email_context

User = get_user_model()


@pytest.fixture
def coach_profile(coach_profile):
    """Create a coach profile for testing"""
    coach_profile.user.userpreferences.gender = "K"
    coach_profile.user.userpreferences.save()
    coach_profile.user.first_name = "Karolina"
    coach_profile.user.last_name = "Nowak"
    coach_profile.user.save()
    return coach_profile


@pytest.fixture
def player_profile(player_profile):
    """Create a player profile for testing"""
    player_profile.user.userpreferences.gender = "M"
    player_profile.user.userpreferences.save()
    player_profile.user.first_name = "Jan"
    player_profile.user.last_name = "Kowalski"
    player_profile.user.save()
    return player_profile


@pytest.mark.django_db
class TestEmailContextBuilder:
    def test_build_email_context_with_user_only(self, player_profile, coach_profile):
        context = build_email_context(player_profile.user, coach_profile.user)
        assert "user" in context
        assert context["user"] == player_profile.user

    def test_build_email_context_with_extra_kwargs(self, player_profile, coach_profile):
        context = build_email_context(
            player_profile.user, coach_profile.user, extra_data="some_value"
        )
        assert "user" in context
        assert context["user"] == player_profile.user
        assert context["user2"] == coach_profile.user
        assert "extra_data" in context
        assert context["extra_data"] == "some_value"

    def test_build_email_context_with_log_and_gendered_data(
        self,
        player_profile,
        coach_profile,
    ):
        context = build_email_context(player_profile.user, coach_profile.user)

        assert "user" in context
        assert context["user"] == player_profile.user
        assert context["recipient_full_name"] == "Jan Kowalski"
        assert context["related_full_name"] == "Karolina Nowak"
        assert context["related_user"] == coach_profile.user
        assert context["related_role"] == "Trenerka"
        assert context["related_role_biernik"] == "trenerkę"

    def test_build_email_context_with_log_and_female_gendered_data(
        self,
        player_profile,
        coach_profile,
    ):
        context = build_email_context(player_profile.user, coach_profile.user)

        assert context["related_role"] == "Trenerka"
        assert context["related_role_biernik"] == "trenerkę"

    def test_build_email_context_with_custom_context(
        self, player_profile, coach_profile
    ):
        custom_context = {"custom_key": "custom_value"}
        context = build_email_context(
            player_profile.user, coach_profile.user, context=custom_context
        )
        assert "user" in context
        assert context["custom_key"] == "custom_value"
