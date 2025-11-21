"""
Tests for new premium products structure:
- GUEST_PREMIUM_PROFILE_MONTH/YEAR (Guest-specific products)
- OTHER_PREMIUM_PROFILE_QUARTER/YEAR (Club/Coach/etc. products with 90-day quarter option)
"""
from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from payments.models import Transaction

pytestmark = pytest.mark.django_db

create_transaction_url = lambda product_id: reverse(
    "api:premium:create_transaction", kwargs={"product_id": product_id}
)


def approve_transaction(transaction_uuid):
    transaction = Transaction.objects.get(uuid=transaction_uuid)
    transaction.success()
    return transaction


@pytest.fixture
def api_client():
    return APIClient()


# ========== GUEST PREMIUM TESTS ==========

def test_guest_buy_monthly_premium(api_client, guest_profile, product_premium_guest_month):
    """Test Guest buying monthly premium (GUEST_PREMIUM_PROFILE_MONTH)"""
    api_client.force_authenticate(user=guest_profile.user)
    url = create_transaction_url(product_premium_guest_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    guest_profile.refresh_from_db()

    assert transaction.product == product_premium_guest_month
    assert transaction.user == guest_profile.user
    assert guest_profile.premium.subscription_lifespan == timedelta(days=30)
    assert guest_profile.is_premium
    assert not guest_profile.premium.is_trial  # Check premium.is_trial, not profile.is_trial
    assert guest_profile.is_promoted
    assert guest_profile.has_premium_inquiries
    # Guest has Club-like inquiry limits (30/90days), not Player (30/30days)
    assert guest_profile.user.userinquiry.limit == 30
    assert guest_profile.user.userinquiry.left == 30
    assert guest_profile.premium_products.trial_tested


def test_guest_buy_yearly_premium(api_client, guest_profile, product_premium_guest_year):
    """Test Guest buying yearly premium (GUEST_PREMIUM_PROFILE_YEAR)"""
    api_client.force_authenticate(user=guest_profile.user)
    url = create_transaction_url(product_premium_guest_year.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    guest_profile.refresh_from_db()

    assert transaction.product == product_premium_guest_year
    assert guest_profile.premium.subscription_lifespan == timedelta(days=365)
    assert guest_profile.is_premium
    assert guest_profile.is_promoted
    assert guest_profile.has_premium_inquiries


def test_guest_cannot_buy_player_product(api_client, guest_profile, product_premium_player_month):
    """Test Guest cannot buy Player-specific product"""
    api_client.force_authenticate(user=guest_profile.user)
    url = create_transaction_url(product_premium_player_month.id)
    response = api_client.post(url)

    assert response.status_code == 403
    assert "only available for Player profiles" in response.json()["detail"]


def test_guest_cannot_buy_other_product(api_client, guest_profile, product_premium_other_quarter):
    """Test Guest cannot buy Other-specific product (OTHER_PREMIUM_PROFILE_QUARTER)"""
    api_client.force_authenticate(user=guest_profile.user)
    url = create_transaction_url(product_premium_other_quarter.id)
    response = api_client.post(url)

    assert response.status_code == 403
    assert "not available for Player or Guest profiles" in response.json()["detail"]


# ========== OTHER (CLUB/COACH/ETC.) PREMIUM TESTS ==========

def test_club_buy_quarterly_premium(api_client, club_profile, product_premium_other_quarter):
    """Test Club buying quarterly premium (OTHER_PREMIUM_PROFILE_QUARTER - 90 days)"""
    api_client.force_authenticate(user=club_profile.user)
    url = create_transaction_url(product_premium_other_quarter.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    club_profile.refresh_from_db()

    assert transaction.product == product_premium_other_quarter
    assert transaction.user == club_profile.user
    assert club_profile.premium.subscription_lifespan == timedelta(days=90)  # Quarter = 90 days
    assert club_profile.is_premium
    assert not club_profile.premium.is_trial  # Check premium.is_trial, not profile.is_trial
    assert club_profile.is_promoted
    assert club_profile.has_premium_inquiries
    # Club has 30 inquiries / 90 days reset period
    assert club_profile.user.userinquiry.limit == 30
    assert club_profile.user.userinquiry.left == 30
    assert club_profile.premium_products.inquiries.get_reset_period() == 90  # 3 months
    assert club_profile.premium_products.trial_tested


def test_coach_buy_quarterly_premium(api_client, coach_profile, product_premium_other_quarter):
    """Test Coach buying quarterly premium (OTHER_PREMIUM_PROFILE_QUARTER)"""
    api_client.force_authenticate(user=coach_profile.user)
    url = create_transaction_url(product_premium_other_quarter.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    coach_profile.refresh_from_db()

    assert transaction.product == product_premium_other_quarter
    assert coach_profile.premium.subscription_lifespan == timedelta(days=90)
    assert coach_profile.is_premium
    assert coach_profile.premium_products.inquiries.get_reset_period() == 90


def test_club_buy_yearly_premium(api_client, club_profile, product_premium_other_year_new):
    """Test Club buying yearly premium (OTHER_PREMIUM_PROFILE_YEAR)"""
    api_client.force_authenticate(user=club_profile.user)
    url = create_transaction_url(product_premium_other_year_new.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    club_profile.refresh_from_db()

    assert transaction.product == product_premium_other_year_new
    assert club_profile.premium.subscription_lifespan == timedelta(days=365)
    assert club_profile.is_premium
    assert club_profile.has_premium_inquiries


def test_club_cannot_buy_player_product(api_client, club_profile, product_premium_player_month):
    """Test Club cannot buy Player-specific product"""
    api_client.force_authenticate(user=club_profile.user)
    url = create_transaction_url(product_premium_player_month.id)
    response = api_client.post(url)

    assert response.status_code == 403
    assert "only available for Player profiles" in response.json()["detail"]


def test_club_cannot_buy_guest_product(api_client, club_profile, product_premium_guest_month):
    """Test Club cannot buy Guest-specific product"""
    api_client.force_authenticate(user=club_profile.user)
    url = create_transaction_url(product_premium_guest_month.id)
    response = api_client.post(url)

    assert response.status_code == 403
    assert "only available for Guest profiles" in response.json()["detail"]


# ========== PLAYER VALIDATION TESTS ==========

def test_player_cannot_buy_guest_product(api_client, player_profile, product_premium_guest_month):
    """Test Player cannot buy Guest-specific product"""
    api_client.force_authenticate(user=player_profile.user)
    url = create_transaction_url(product_premium_guest_month.id)
    response = api_client.post(url)

    assert response.status_code == 403
    assert "only available for Guest profiles" in response.json()["detail"]


def test_player_cannot_buy_other_product(api_client, player_profile, product_premium_other_quarter):
    """Test Player cannot buy Other-specific product"""
    api_client.force_authenticate(user=player_profile.user)
    url = create_transaction_url(product_premium_other_quarter.id)
    response = api_client.post(url)

    assert response.status_code == 403
    assert "not available for Player or Guest profiles" in response.json()["detail"]


# ========== INQUIRY RESET PERIOD TESTS ==========

def test_club_inquiry_reset_period_90_days(club_profile, product_premium_other_quarter):
    """Test Club premium has 90-day inquiry reset period (not 30)"""
    club_profile.setup_premium_profile("QUARTER")
    club_profile.refresh_from_db()

    # Club should have 90-day reset period
    assert club_profile.products.inquiries.get_reset_period() == 90
    assert club_profile.products.inquiries.INQUIRIES_LIMIT == 30


def test_player_inquiry_reset_period_30_days(player_profile, product_premium_player_month):
    """Test Player premium has 30-day inquiry reset period"""
    player_profile.setup_premium_profile("MONTH")
    player_profile.refresh_from_db()

    # Player should have 30-day reset period
    assert player_profile.products.inquiries.get_reset_period() == 30
    assert player_profile.products.inquiries.INQUIRIES_LIMIT == 30


def test_guest_inquiry_reset_period_90_days(guest_profile, product_premium_guest_month):
    """Test Guest premium has 90-day inquiry reset period (Club-like)"""
    guest_profile.setup_premium_profile("MONTH")
    guest_profile.refresh_from_db()

    # Guest should have 90-day reset period (Club-like, not Player)
    assert guest_profile.products.inquiries.get_reset_period() == 90
    assert guest_profile.products.inquiries.INQUIRIES_LIMIT == 30
