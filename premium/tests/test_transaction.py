from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from payments.models import Transaction
from premium.models import Product
from utils.factories.profiles_factories import PlayerProfileFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mck_tpay_parser():
    with patch("payments.providers.tpay.parsers.TpayTransactionParser") as mck:
        yield mck


@pytest.fixture
def player_profile():
    yield PlayerProfileFactory.create()


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
def product_premium_player():
    return Product.objects.get(name="PLAYER_PREMIUM_PROFILE_MONTH")


@pytest.fixture
def product_premium_other():
    return Product.objects.get(name="PREMIUM_PROFILE_MONTH")


def test_buy_L_inquiries(product_inquiries_L, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
    transaction.success()

    assert user.userinquiry.plan.type_ref == product_inquiries_L.name
    assert user.userinquiry.limit == 5
    assert user.userinquiry.left == 5


def test_buy_XL_inquiries(product_inquiries_XL, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(product=product_inquiries_XL, user=user)
    transaction.success()

    assert user.userinquiry.plan.type_ref == product_inquiries_XL.name
    assert user.userinquiry.limit == 7
    assert user.userinquiry.left == 7


def test_buy_XXL_inquiries(product_inquiries_XXL, player_profile):
    user = player_profile.user
    transaction = Transaction.objects.create(product=product_inquiries_XXL, user=user)
    transaction.success()

    assert user.userinquiry.plan.type_ref == product_inquiries_XXL.name
    assert user.userinquiry.limit == 12
    assert user.userinquiry.left == 12


def test_buy_premium(product_premium_player, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(product=product_premium_player, user=user)
    transaction.success()

    assert player_profile.is_premium
    assert player_profile.user.userinquiry.limit == 12
    assert player_profile.is_promoted
    assert player_profile.premium_products.calculate_pm_score
    assert player_profile.user.userinquiry.plan.type_ref == "BASIC"


def test_buy_inquiries_for_profile_with_premium(player_profile, product_premium_player):
    user = player_profile.user
    transaction_premium = Transaction.objects.create(
        product=product_premium_player, user=user
    )
    transaction_premium.success()

    assert player_profile.is_premium
    assert player_profile.user.userinquiry.plan.type_ref == "BASIC"


def test_impossible_to_buy_inquiries_without_premium(
    api_client, player_profile, product_inquiries_L
):
    api_client.force_authenticate(user=player_profile.user)
    url = reverse(
        "api:premium:create_transaction", kwargs={"product_id": product_inquiries_L.id}
    )
    response = api_client.post(url)

    assert response.status_code == 400
    assert response.json() == "Product is available only for premium users."
