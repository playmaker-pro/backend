from unittest.mock import patch

import pytest
from django.utils import timezone

from premium.models import PremiumType, Product
from utils.factories import (
    CoachProfileFactory,
    GuestProfileFactory,
    PlayerProfileFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def mck_timezone_now():
    with patch("django.utils.timezone.now", return_value=timezone.now()) as mck:
        yield mck


@pytest.fixture
def player_profile():
    yield PlayerProfileFactory.create()


@pytest.fixture
def guest_profile():
    yield GuestProfileFactory.create()


@pytest.fixture
def trial_premium_player_profile(player_profile):
    player_profile.premium_products.setup_premium_profile(PremiumType.TRIAL)
    return player_profile


@pytest.fixture
def coach_profile():
    yield CoachProfileFactory.create()


@pytest.fixture
def trial_premium_coach_profile(coach_profile):
    coach_profile.premium_products.setup_premium_profile(PremiumType.TRIAL)
    return coach_profile


@pytest.fixture
def product_inquiries_L():
    return Product.objects.get(name="PREMIUM_INQUIRIES_L")


@pytest.fixture
def product_inquiries_XL():
    return Product.objects.get(name="PREMIUM_INQUIRIES_XL")


@pytest.fixture
def product_inquiries_XXL():
    return Product.objects.get(name="PREMIUM_INQUIRIES_XXL")


@pytest.fixture
def product_premium_player_month():
    return Product.objects.get(name="PLAYER_PREMIUM_PROFILE_MONTH")


@pytest.fixture
def product_premium_player_year():
    return Product.objects.get(name="PLAYER_PREMIUM_PROFILE_YEAR")


@pytest.fixture
def product_premium_other_month():
    return Product.objects.get(name="PREMIUM_PROFILE_MONTH")


@pytest.fixture
def product_premium_other_year():
    return Product.objects.get(name="PREMIUM_PROFILE_YEAR")
