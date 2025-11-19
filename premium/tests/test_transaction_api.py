from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from payments.models import Transaction
from premium.models import PremiumType

pytestmark = pytest.mark.django_db

create_transaction_url = lambda product_id: reverse(
    "api:premium:create_transaction", kwargs={"product_id": product_id}
)


@pytest.fixture
def api_client():
    return APIClient()


def approve_transaction(transaction_uuid):
    transaction = Transaction.objects.get(uuid=transaction_uuid)
    transaction.success()

    return transaction


def test_impossible_to_buy_inquiries_without_premium(
    api_client, coach_profile, product_inquiries_L
):
    api_client.force_authenticate(user=coach_profile.user)
    url = create_transaction_url(product_inquiries_L.id)
    response = api_client.post(url)

    assert response.status_code == 400
    assert response.json() == "Product is available only for premium users."


def test_buy_premium_month_player(
    api_client,
    player_profile,
    product_premium_player_month,
):
    api_client.force_authenticate(user=player_profile.user)
    url = create_transaction_url(product_premium_player_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    player_profile.refresh_from_db()

    assert transaction.product == product_premium_player_month
    assert transaction.user == player_profile.user
    assert player_profile.premium.subscription_lifespan == timedelta(days=30)
    assert player_profile.is_premium
    assert player_profile.premium_products.calculate_pm_score.awaiting_approval
    assert player_profile.is_promoted
    assert player_profile.has_premium_inquiries
    assert player_profile.user.userinquiry.limit_raw == 10
    assert player_profile.user.userinquiry.limit == 30
    assert player_profile.user.userinquiry.left == 30
    assert player_profile.premium_products.trial_tested


def test_buy_premium_year_player(
    api_client,
    player_profile,
    product_premium_player_year,
):
    api_client.force_authenticate(user=player_profile.user)
    url = create_transaction_url(product_premium_player_year.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    player_profile.refresh_from_db()

    assert transaction.product == product_premium_player_year
    assert transaction.user == player_profile.user
    assert player_profile.premium.subscription_lifespan == timedelta(days=365)
    assert player_profile.is_premium
    assert player_profile.premium_products.calculate_pm_score.awaiting_approval
    assert player_profile.is_promoted
    assert player_profile.has_premium_inquiries
    assert player_profile.user.userinquiry.limit_raw == 10
    assert player_profile.user.userinquiry.limit == 30
    assert player_profile.user.userinquiry.left == 30
    assert player_profile.premium_products.trial_tested


def test_buy_premium_quarter_other(
    api_client,
    coach_profile,
    product_premium_other_quarter,
):
    api_client.force_authenticate(user=coach_profile.user)
    url = create_transaction_url(product_premium_other_quarter.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    coach_profile.refresh_from_db()
    assert transaction.product == product_premium_other_quarter
    assert transaction.user == coach_profile.user
    assert coach_profile.premium.subscription_lifespan == timedelta(days=90)
    assert coach_profile.is_premium
    assert not hasattr(coach_profile.premium_products, "calculate_pm_score")
    assert coach_profile.is_promoted
    assert coach_profile.has_premium_inquiries
    assert coach_profile.user.userinquiry.limit_raw == 5  # Coach freemium limit (Club-like)
    assert coach_profile.user.userinquiry.limit == 30  # Coach premium limit (Club-like)
    assert coach_profile.user.userinquiry.left == 30
    assert coach_profile.premium_products.trial_tested


def test_buy_premium_year_other(api_client, coach_profile, product_premium_other_year_new):
    api_client.force_authenticate(user=coach_profile.user)
    url = create_transaction_url(product_premium_other_year_new.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    coach_profile.refresh_from_db()
    assert transaction.product == product_premium_other_year_new
    assert transaction.user == coach_profile.user
    assert coach_profile.premium.subscription_lifespan == timedelta(days=365)
    assert coach_profile.is_premium
    assert not hasattr(coach_profile.premium_products, "calculate_pm_score")
    assert coach_profile.is_promoted
    assert coach_profile.has_premium_inquiries
    assert coach_profile.user.userinquiry.limit_raw == 5  # Coach freemium limit (Club-like)
    assert coach_profile.user.userinquiry.limit == 30  # Coach premium limit (Club-like)
    assert coach_profile.user.userinquiry.left == 30
    assert coach_profile.premium_products.trial_tested


def test_buy_L_inquiries(api_client, trial_premium_coach_profile, product_inquiries_L):
    api_client.force_authenticate(user=trial_premium_coach_profile.user)
    ui = trial_premium_coach_profile.user.userinquiry
    pi = trial_premium_coach_profile.user.userinquiry.premium_inquiries
    # Set counter to exhaust premium limit (30) so user can buy packages
    ui.counter_raw = 5  # Use all freemium for coach
    pi.current_counter = 25  # Use 25 of 30 premium
    ui.save()
    pi.save()
    url = create_transaction_url(product_inquiries_L.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_coach_profile.refresh_from_db()

    assert transaction.product == product_inquiries_L
    assert transaction.user == trial_premium_coach_profile.user
    assert (
        trial_premium_coach_profile.user.userinquiry.plan.type_ref
        == product_inquiries_L.name
    )
    # Counter setup: 5 freemium + 25 premium = 30 total (all used)
    # Buying L adds 3 to limit_raw (5 + 3 = 8) AND to total limit
    # New limit: 30 (base) + 3 (package bonus from 8-5) = 33
    assert trial_premium_coach_profile.user.userinquiry.limit_raw == 8  # 5 + 3 from L
    assert trial_premium_coach_profile.user.userinquiry.limit == 33  # Premium (30) + package (3)
    assert trial_premium_coach_profile.user.userinquiry.left == 3  # 33 - 30 used = 3 new inquiries
    assert trial_premium_coach_profile.user.userinquiry.counter_raw == 5  # All freemium used
    assert trial_premium_coach_profile.user.userinquiry.limit_to_show == 33
    assert trial_premium_coach_profile.user.userinquiry.left_to_show == 3
    assert trial_premium_coach_profile.premium_products.trial_tested


def test_buy_XL_inquiries(
    api_client, trial_premium_coach_profile, product_inquiries_XL
):
    api_client.force_authenticate(user=trial_premium_coach_profile.user)
    ui = trial_premium_coach_profile.user.userinquiry
    pi = trial_premium_coach_profile.user.userinquiry.premium_inquiries
    # Set counter to exhaust premium limit (30) so user can buy packages
    ui.counter_raw = 5  # Use all freemium for coach
    pi.current_counter = 25  # Use 25 of 30 premium
    ui.save()
    pi.save()
    url = create_transaction_url(product_inquiries_XL.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_coach_profile.refresh_from_db()

    assert transaction.product == product_inquiries_XL
    assert transaction.user == trial_premium_coach_profile.user
    assert (
        trial_premium_coach_profile.user.userinquiry.plan.type_ref
        == product_inquiries_XL.name
    )
    # Counter setup: 5 freemium + 25 premium = 30 total (all used)
    # Buying XL adds 5 to limit_raw (5 + 5 = 10) AND to total limit
    # New limit: 30 (base) + 5 (package bonus from 10-5) = 35
    assert trial_premium_coach_profile.user.userinquiry.limit_raw == 10  # 5 + 5 from XL
    assert trial_premium_coach_profile.user.userinquiry.limit == 35  # Premium (30) + package (5)
    assert trial_premium_coach_profile.user.userinquiry.left == 5  # 35 - 30 used = 5 new inquiries
    assert trial_premium_coach_profile.user.userinquiry.left_to_show == 5
    assert trial_premium_coach_profile.user.userinquiry.limit_to_show == 35
    assert trial_premium_coach_profile.premium_products.trial_tested


def test_buy_inquiries_with_some_left(
    api_client, trial_premium_coach_profile, product_inquiries_L
):
    api_client.force_authenticate(user=trial_premium_coach_profile.user)
    url = create_transaction_url(product_inquiries_L.id)
    response = api_client.post(url)

    assert response.status_code == 400
    assert response.json() == "You need to use all inquiries before buying new ones."


def test_buy_XXL_inquiries(
    api_client, trial_premium_coach_profile, product_inquiries_XXL
):
    api_client.force_authenticate(user=trial_premium_coach_profile.user)
    ui = trial_premium_coach_profile.user.userinquiry
    pi = trial_premium_coach_profile.user.userinquiry.premium_inquiries
    # Set counter to exhaust premium limit (30) so user can buy packages
    ui.counter_raw = 5  # Use all freemium for coach
    pi.current_counter = 25  # Use 25 of 30 premium
    ui.save()
    pi.save()

    url = create_transaction_url(product_inquiries_XXL.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_coach_profile.refresh_from_db()

    assert transaction.product == product_inquiries_XXL
    assert transaction.user == trial_premium_coach_profile.user
    assert (
        trial_premium_coach_profile.user.userinquiry.plan.type_ref
        == product_inquiries_XXL.name
    )
    # Counter setup: 5 freemium + 25 premium = 30 total (all used)
    # Buying XXL adds 10 to limit_raw (5 + 10 = 15) AND to total limit
    # New limit: 30 (base) + 10 (package bonus from 15-5) = 40
    assert trial_premium_coach_profile.user.userinquiry.limit_raw == 15  # 5 + 10 from XXL
    assert trial_premium_coach_profile.user.userinquiry.counter_raw == 5  # All freemium used
    assert trial_premium_coach_profile.user.userinquiry.limit == 40  # Premium (30) + package (10)
    assert trial_premium_coach_profile.user.userinquiry.left == 10  # 40 - 30 used = 10 new inquiries
    assert trial_premium_coach_profile.user.userinquiry.left_to_show == 10
    assert trial_premium_coach_profile.user.userinquiry.limit_to_show == 40
    assert trial_premium_coach_profile.premium_products.trial_tested


def test_extend_premium_during_trial(
    api_client, trial_premium_player_profile, product_premium_player_month
):
    trial_premium_player_profile.refresh_from_db()
    assert trial_premium_player_profile.premium_products.trial_tested

    api_client.force_authenticate(user=trial_premium_player_profile.user)
    url = create_transaction_url(product_premium_player_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_player_profile.refresh_from_db()

    assert transaction.product == product_premium_player_month
    assert transaction.user == trial_premium_player_profile.user
    # Trial is replaced, not extended - should be 30 days, not 33
    assert trial_premium_player_profile.premium.subscription_lifespan == timedelta(
        days=30
    )
    assert trial_premium_player_profile.is_premium
    assert not trial_premium_player_profile.premium.is_trial  # No longer trial
    assert (
        trial_premium_player_profile.premium_products.calculate_pm_score.awaiting_approval
    )
    assert trial_premium_player_profile.is_promoted
    assert trial_premium_player_profile.has_premium_inquiries
    assert trial_premium_player_profile.user.userinquiry.limit_raw == 10
    assert trial_premium_player_profile.user.userinquiry.limit == 30
    assert trial_premium_player_profile.user.userinquiry.left == 30  # Fresh premium (0 used)
    # Plan should be PREMIUM_PLAYER when premium is active
    assert trial_premium_player_profile.user.userinquiry.plan.type_ref == "PREMIUM_PLAYER"


def test_extend_premium_with_trial(
    api_client, player_profile, product_premium_player_month
):
    api_client.force_authenticate(user=player_profile.user)
    url = create_transaction_url(product_premium_player_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    player_profile.refresh_from_db()

    assert transaction.product == product_premium_player_month
    assert transaction.user == player_profile.user
    assert player_profile.premium.subscription_lifespan == timedelta(days=30)
    assert player_profile.is_premium
    assert player_profile.premium_products.calculate_pm_score.awaiting_approval
    assert player_profile.is_promoted
    assert player_profile.has_premium_inquiries
    assert player_profile.user.userinquiry.limit_raw == 10
    assert player_profile.user.userinquiry.limit == 30
    assert player_profile.user.userinquiry.left == 30
    assert player_profile.premium_products.trial_tested

    with pytest.raises(ValueError) as exc:
        player_profile.setup_premium_profile(PremiumType.TRIAL)

    assert str(exc.value) == "Trial already tested or cannot be set."


def test_buy_premium_for_player_after_trial_expiration(
    api_client,
    trial_premium_player_profile,
    product_premium_player_month,
    mck_timezone_now,
):
    profile = trial_premium_player_profile
    profile.refresh_from_db()

    assert profile.premium_products.trial_tested
    assert profile.premium.subscription_lifespan.days == 3
    assert profile.is_premium
    assert profile.premium_products.calculate_pm_score.awaiting_approval
    assert profile.is_promoted
    assert profile.has_premium_inquiries

    mck_timezone_now.return_value += timedelta(days=10)
    profile.refresh_from_db()

    assert not profile.is_premium
    assert profile.premium_products.calculate_pm_score.awaiting_approval
    assert not profile.is_promoted
    assert not profile.has_premium_inquiries

    api_client.force_authenticate(user=profile.user)
    url = create_transaction_url(product_premium_player_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_player_profile.refresh_from_db()

    assert transaction.product == product_premium_player_month
    assert transaction.user == profile.user
    assert profile.premium.subscription_lifespan == timedelta(days=30)
    assert profile.is_premium
    assert profile.premium_products.calculate_pm_score.awaiting_approval
    assert profile.is_promoted
    assert profile.has_premium_inquiries
    assert profile.user.userinquiry.limit_raw == 10
    assert profile.user.userinquiry.limit == 30
    assert profile.user.userinquiry.left == 30  # Fresh premium (0 used after renewal)
    assert profile.premium_products.trial_tested


def test_buy_premium_for_other_after_trial_expiration(
    api_client,
    trial_premium_coach_profile,
    product_premium_other_quarter,
    mck_timezone_now,
):
    profile = trial_premium_coach_profile
    profile.refresh_from_db()

    assert profile.premium_products.trial_tested
    assert profile.premium.subscription_lifespan.days == 3
    assert profile.is_premium
    assert not hasattr(profile.premium_products, "calculate_pm_score")
    assert profile.is_promoted
    assert profile.has_premium_inquiries

    mck_timezone_now.return_value += timedelta(days=10)
    profile.refresh_from_db()

    assert not profile.is_premium
    assert not hasattr(profile.premium_products, "calculate_pm_score")
    assert not profile.is_promoted
    assert not profile.has_premium_inquiries

    api_client.force_authenticate(user=profile.user)
    url = create_transaction_url(product_premium_other_quarter.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_coach_profile.refresh_from_db()

    assert transaction.product == product_premium_other_quarter
    assert transaction.user == profile.user
    assert profile.premium.subscription_lifespan == timedelta(days=90)
    assert profile.is_premium
    assert not hasattr(profile.premium_products, "calculate_pm_score")
    assert profile.is_promoted
    assert profile.has_premium_inquiries
    assert profile.user.userinquiry.limit_raw == 5  # Coach freemium limit (Club-like)
    assert profile.user.userinquiry.limit == 30  # Coach premium limit (Club-like)
    assert profile.user.userinquiry.left == 30  # Fresh premium (0 used after renewal)
    assert profile.premium_products.trial_tested


def test_buy_premium_for_guest(api_client, guest_profile, product_premium_guest_month):
    """Test Guest buying GUEST_PREMIUM_PROFILE_MONTH (new product)"""
    api_client.force_authenticate(user=guest_profile.user)
    url = create_transaction_url(product_premium_guest_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])

    guest_profile.refresh_from_db()
    assert transaction.product == product_premium_guest_month
    assert guest_profile.is_premium
    assert guest_profile.is_promoted
    assert guest_profile.has_premium_inquiries
    assert guest_profile.premium.subscription_lifespan == timedelta(days=30)
    # Guest has same inquiry limits as Club-like (not Player)
    assert guest_profile.user.userinquiry.limit == 30
