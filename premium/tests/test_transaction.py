import pytest

from payments.models import Transaction
from premium.models import Product
from utils.factories.profiles_factories import PlayerProfileFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def player_profile():
    yield PlayerProfileFactory.create()


@pytest.fixture
def product_5_inquiries():
    return Product.objects.get(name="PREMIUM_INQUIRIES_5")


@pytest.fixture
def product_10_inquiries():
    return Product.objects.get(name="PREMIUM_INQUIRIES_10")


@pytest.fixture
def product_25_inquiries():
    return Product.objects.get(name="PREMIUM_INQUIRIES_25")


@pytest.fixture
def product_premium():
    return Product.objects.get(name="PREMIUM")


def test_buy_5_inquiries(product_5_inquiries, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(product=product_5_inquiries, user=user)
    transaction.success()

    assert user.userinquiry.plan.type_ref == product_5_inquiries.name
    assert user.userinquiry.limit == 10
    assert user.userinquiry.left == 10


def test_buy_10_inquiries(product_10_inquiries, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(product=product_10_inquiries, user=user)
    transaction.success()

    assert user.userinquiry.plan.type_ref == product_10_inquiries.name
    assert user.userinquiry.limit == 15
    assert user.userinquiry.left == 15


def test_buy_25_inquiries(product_25_inquiries, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(product=product_25_inquiries, user=user)
    transaction.success()

    assert user.userinquiry.plan.type_ref == product_25_inquiries.name
    assert user.userinquiry.limit == 30
    assert user.userinquiry.left == 30


def test_buy_premium(product_premium, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(product=product_premium, user=user)
    transaction.success()

    assert player_profile.is_premium
    assert player_profile.user.userinquiry.limit == 25
    assert player_profile.is_promoted
    assert player_profile.premium_products.calculate_pm_score
    assert player_profile.user.userinquiry.plan.type_ref == "BASIC"


def test_buy_premium_for_profile_with_premium_inquiries(
    product_premium, player_profile, product_25_inquiries
):
    user = player_profile.user

    transaction_inquiries = Transaction.objects.create(
        product=product_25_inquiries, user=user
    )
    transaction_inquiries.success()

    assert player_profile.user.userinquiry.plan.type_ref == "PREMIUM_INQUIRIES_25"
    assert player_profile.user.userinquiry.limit == 30

    transaction_premium = Transaction.objects.create(product=product_premium, user=user)
    transaction_premium.success()

    assert player_profile.is_premium
    assert player_profile.user.userinquiry.plan.type_ref == "PREMIUM_INQUIRIES_25"
    assert player_profile.user.userinquiry.limit == 50
    assert player_profile.user.userinquiry.left == 50


def test_buy_inquries_for_profile_with_premium(
    product_25_inquiries, player_profile, product_premium
):
    user = player_profile.user

    transaction_premium = Transaction.objects.create(product=product_premium, user=user)
    transaction_premium.success()

    assert player_profile.is_premium
    assert player_profile.user.userinquiry.plan.type_ref == "BASIC"

    transaction_inquiries = Transaction.objects.create(
        product=product_25_inquiries, user=user
    )
    transaction_inquiries.success()

    assert player_profile.user.userinquiry.limit == 50
    assert player_profile.user.userinquiry.left == 50
