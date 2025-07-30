from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from mailing.utils import build_email_context

User = get_user_model()


@pytest.fixture
def test_user():
    user, _ = User.objects.get_or_create(email="test_user@example.com")
    return user


@pytest.fixture
def mock_log(test_user):
    log = MagicMock()
    log.log_owner.user = test_user
    log.related_with.user.display_full_name = "Related User Full Name"
    log.related_with.user.userpreferences.gender = "M"
    log.related_with.user.declared_role = "player"
    return log


@pytest.mark.django_db
class TestEmailContextBuilder:
    def test_build_email_context_with_user_only(self, test_user):
        context = build_email_context(test_user)
        assert "user" in context
        assert context["user"] == test_user
        assert "log" not in context

    def test_build_email_context_with_extra_kwargs(self, test_user):
        context = build_email_context(test_user, extra_data="some_value")
        assert "user" in context
        assert context["user"] == test_user
        assert "extra_data" in context
        assert context["extra_data"] == "some_value"

    def test_build_email_context_with_log_and_gendered_data(self, test_user, mock_log):
        with (
            patch("mailing.utils.GENDER_BASED_ROLES", {"player": ["Gracz", "Graczka"]}),
            patch(
                "mailing.utils.OBJECTIVE_GENDER_BASED_ROLES",
                {"player": ["Gracza", "Graczki"]},
            ),
        ):
            context = build_email_context(test_user, log=mock_log)

            assert "user" in context
            assert context["user"] == test_user
            assert "log" in context
            assert context["log"] == mock_log
            assert context["recipient_full_name"] == test_user.display_full_name
            assert context["related_full_name"] == "Related User Full Name"
            assert context["related_user"] == mock_log.related_with.user
            assert context["related_role"] == "Gracz"
            assert context["related_role_biernik"] == "Gracza"

    def test_build_email_context_with_log_and_female_gendered_data(
        self, test_user, mock_log
    ):
        mock_log.related_with.user.userpreferences.gender = "K"
        with (
            patch("mailing.utils.GENDER_BASED_ROLES", {"player": ["Gracz", "Graczka"]}),
            patch(
                "mailing.utils.OBJECTIVE_GENDER_BASED_ROLES",
                {"player": ["Gracza", "Graczki"]},
            ),
        ):
            context = build_email_context(test_user, log=mock_log)

            assert context["related_role"] == "Graczka"
            assert context["related_role_biernik"] == "Graczki"

    def test_build_email_context_with_custom_context(self, test_user):
        custom_context = {"custom_key": "custom_value"}
        context = build_email_context(test_user, context=custom_context)
        assert "user" in context
        assert context["custom_key"] == "custom_value"
