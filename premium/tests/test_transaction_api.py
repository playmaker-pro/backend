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
    api_client, player_profile, product_inquiries_L
):
    api_client.force_authenticate(user=player_profile.user)
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
    assert player_profile.premium.subscription_days == timedelta(days=30)
    assert player_profile.is_premium
    assert player_profile.premium_products.calculate_pm_score.awaiting_approval
    assert player_profile.is_promoted
    assert player_profile.has_premium_inquiries
    assert player_profile.user.userinquiry.limit_raw == 2
    assert player_profile.user.userinquiry.limit == 12
    assert player_profile.user.userinquiry.left == 12
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
    assert player_profile.premium.subscription_days == timedelta(days=365)
    assert player_profile.is_premium
    assert player_profile.premium_products.calculate_pm_score.awaiting_approval
    assert player_profile.is_promoted
    assert player_profile.has_premium_inquiries
    assert player_profile.user.userinquiry.limit_raw == 2
    assert player_profile.user.userinquiry.limit == 12
    assert player_profile.user.userinquiry.left == 12
    assert player_profile.premium_products.trial_tested


def test_buy_premium_month_other(
    api_client,
    coach_profile,
    product_premium_other_month,
):
    api_client.force_authenticate(user=coach_profile.user)
    url = create_transaction_url(product_premium_other_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])

    assert transaction.product == product_premium_other_month
    assert transaction.user == coach_profile.user
    assert coach_profile.premium.subscription_days == timedelta(days=30)
    assert coach_profile.is_premium
    assert not hasattr(coach_profile.premium_products, "calculate_pm_score")
    assert coach_profile.is_promoted
    assert coach_profile.has_premium_inquiries
    assert coach_profile.user.userinquiry.limit_raw == 2
    assert coach_profile.user.userinquiry.limit == 12
    assert coach_profile.user.userinquiry.left == 12
    assert not coach_profile.premium_products.trial_tested


def test_buy_premium_year_other(api_client, coach_profile, product_premium_other_year):
    api_client.force_authenticate(user=coach_profile.user)
    url = create_transaction_url(product_premium_other_year.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])

    assert transaction.product == product_premium_other_year
    assert transaction.user == coach_profile.user
    assert coach_profile.premium.subscription_days == timedelta(days=365)
    assert coach_profile.is_premium
    assert not hasattr(coach_profile.premium_products, "calculate_pm_score")
    assert coach_profile.is_promoted
    assert coach_profile.has_premium_inquiries
    assert coach_profile.user.userinquiry.limit_raw == 2
    assert coach_profile.user.userinquiry.limit == 12
    assert coach_profile.user.userinquiry.left == 12
    assert not coach_profile.premium_products.trial_tested


def test_buy_L_inquiries(api_client, trial_premium_player_profile, product_inquiries_L):
    api_client.force_authenticate(user=trial_premium_player_profile.user)
    trial_premium_player_profile.user.userinquiry.counter = 2
    trial_premium_player_profile.user.userinquiry.premium_inquiries.current_counter = 10
    trial_premium_player_profile.user.userinquiry.save()
    trial_premium_player_profile.user.userinquiry.premium_inquiries.save()
    url = create_transaction_url(product_inquiries_L.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_player_profile.refresh_from_db()

    assert transaction.product == product_inquiries_L
    assert transaction.user == trial_premium_player_profile.user
    assert (
        trial_premium_player_profile.user.userinquiry.plan.type_ref
        == product_inquiries_L.name
    )
    assert trial_premium_player_profile.user.userinquiry.limit_raw == 5
    assert trial_premium_player_profile.user.userinquiry.limit == 15
    assert trial_premium_player_profile.user.userinquiry.left == 3
    assert trial_premium_player_profile.user.userinquiry.counter_raw == 2
    assert trial_premium_player_profile.user.userinquiry.limit_to_show == 12
    assert trial_premium_player_profile.user.userinquiry.left_to_show == 3
    assert trial_premium_player_profile.premium_products.trial_tested


def test_buy_XL_inquiries(
    api_client, trial_premium_player_profile, product_inquiries_XL
):
    api_client.force_authenticate(user=trial_premium_player_profile.user)
    trial_premium_player_profile.user.userinquiry.counter = 2
    trial_premium_player_profile.user.userinquiry.premium_inquiries.current_counter = 10
    trial_premium_player_profile.user.userinquiry.save()
    trial_premium_player_profile.user.userinquiry.premium_inquiries.save()
    url = create_transaction_url(product_inquiries_XL.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_player_profile.refresh_from_db()

    assert transaction.product == product_inquiries_XL
    assert transaction.user == trial_premium_player_profile.user
    assert (
        trial_premium_player_profile.user.userinquiry.plan.type_ref
        == product_inquiries_XL.name
    )
    assert trial_premium_player_profile.user.userinquiry.limit_raw == 7
    assert trial_premium_player_profile.user.userinquiry.limit == 17
    assert trial_premium_player_profile.user.userinquiry.left == 5
    assert trial_premium_player_profile.user.userinquiry.left_to_show == 5
    assert trial_premium_player_profile.user.userinquiry.limit_to_show == 12
    assert trial_premium_player_profile.premium_products.trial_tested


def test_buy_inquiries_with_some_left(
    api_client, trial_premium_player_profile, product_inquiries_L
):
    api_client.force_authenticate(user=trial_premium_player_profile.user)
    url = create_transaction_url(product_inquiries_L.id)
    response = api_client.post(url)

    assert response.status_code == 400
    assert response.json() == "You need to use all inquiries before buying new ones."


def test_buy_XXL_inquiries(
    api_client, trial_premium_player_profile, product_inquiries_XXL
):
    api_client.force_authenticate(user=trial_premium_player_profile.user)
    trial_premium_player_profile.user.userinquiry.counter = 2
    trial_premium_player_profile.user.userinquiry.premium_inquiries.current_counter = 10
    trial_premium_player_profile.user.userinquiry.save()
    trial_premium_player_profile.user.userinquiry.premium_inquiries.save()

    url = create_transaction_url(product_inquiries_XXL.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_player_profile.refresh_from_db()

    assert transaction.product == product_inquiries_XXL
    assert transaction.user == trial_premium_player_profile.user
    assert (
        trial_premium_player_profile.user.userinquiry.plan.type_ref
        == product_inquiries_XXL.name
    )
    assert trial_premium_player_profile.user.userinquiry.limit_raw == 12
    assert trial_premium_player_profile.user.userinquiry.counter_raw == 2
    assert trial_premium_player_profile.user.userinquiry.limit == 22
    assert trial_premium_player_profile.user.userinquiry.left == 10
    assert trial_premium_player_profile.user.userinquiry.left_to_show == 10
    assert trial_premium_player_profile.user.userinquiry.limit_to_show == 12
    assert trial_premium_player_profile.premium_products.trial_tested


def test_extend_premium_during_trial(
    api_client, trial_premium_player_profile, product_premium_player_month
):
    assert trial_premium_player_profile.premium_products.trial_tested

    api_client.force_authenticate(user=trial_premium_player_profile.user)
    url = create_transaction_url(product_premium_player_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_player_profile.refresh_from_db()

    assert transaction.product == product_premium_player_month
    assert transaction.user == trial_premium_player_profile.user
    assert trial_premium_player_profile.premium.subscription_days == timedelta(days=33)
    assert trial_premium_player_profile.is_premium
    assert trial_premium_player_profile.premium_products.calculate_pm_score.awaiting_approval
    assert trial_premium_player_profile.is_promoted
    assert trial_premium_player_profile.has_premium_inquiries
    assert trial_premium_player_profile.user.userinquiry.limit_raw == 2
    assert trial_premium_player_profile.user.userinquiry.limit == 12
    assert trial_premium_player_profile.user.userinquiry.left == 12
    assert trial_premium_player_profile.user.userinquiry.plan.type_ref == "BASIC"


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
    assert player_profile.premium.subscription_days == timedelta(days=30)
    assert player_profile.is_premium
    assert player_profile.premium_products.calculate_pm_score.awaiting_approval
    assert player_profile.is_promoted
    assert player_profile.has_premium_inquiries
    assert player_profile.user.userinquiry.limit_raw == 2
    assert player_profile.user.userinquiry.limit == 12
    assert player_profile.user.userinquiry.left == 12
    assert player_profile.premium_products.trial_tested

    with pytest.raises(ValueError) as exc:
        player_profile.premium_products.setup_premium_profile(PremiumType.TRIAL)

    assert str(exc.value) == "Trial already tested or cannot be set."


def test_buy_premium_for_player_after_trial_expiration(
    api_client,
    trial_premium_player_profile,
    product_premium_player_month,
    mck_timezone_now,
):
    profile = trial_premium_player_profile

    assert profile.premium_products.trial_tested
    assert profile.premium.subscription_days == timedelta(days=3)
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
    assert profile.premium.subscription_days == timedelta(days=30)
    assert profile.is_premium
    assert profile.premium_products.calculate_pm_score.awaiting_approval
    assert profile.is_promoted
    assert profile.has_premium_inquiries
    assert profile.user.userinquiry.limit_raw == 2
    assert profile.user.userinquiry.limit == 12
    assert profile.user.userinquiry.left == 12
    assert profile.premium_products.trial_tested


def test_buy_premium_for_other_after_trial_expiration(
    api_client,
    trial_premium_coach_profile,
    product_premium_other_month,
    mck_timezone_now,
):
    profile = trial_premium_coach_profile

    assert profile.premium_products.trial_tested
    assert profile.premium.subscription_days == timedelta(days=3)
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
    url = create_transaction_url(product_premium_other_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    transaction = approve_transaction(response.json()["uuid"])
    trial_premium_coach_profile.refresh_from_db()

    assert transaction.product == product_premium_other_month
    assert transaction.user == profile.user
    assert profile.premium.subscription_days == timedelta(days=30)
    assert profile.is_premium
    assert not hasattr(profile.premium_products, "calculate_pm_score")
    assert profile.is_promoted
    assert profile.has_premium_inquiries
    assert profile.user.userinquiry.limit_raw == 2
    assert profile.user.userinquiry.limit == 12
    assert profile.user.userinquiry.left == 12
    assert profile.premium_products.trial_tested


def test_buy_premium_for_guest(api_client, guest_profile, product_premium_other_month):
    api_client.force_authenticate(user=guest_profile.user)
    url = create_transaction_url(product_premium_other_month.id)
    response = api_client.post(url)

    assert response.status_code == 200

    approve_transaction(response.json()["uuid"])

    assert guest_profile.is_premium
    assert guest_profile.is_promoted
    assert guest_profile.has_premium_inquiries
