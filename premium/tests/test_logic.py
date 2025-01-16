from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.utils.timezone import make_aware

from premium.models import (
    CalculatePMScoreProduct,
    PremiumInquiriesProduct,
    PremiumProduct,
    PremiumProfile,
    PremiumType,
    Product,
)
from premium.utils import get_date_days_after
from utils import factories

pytestmark = pytest.mark.django_db


@pytest.fixture
def timezone_now():
    with patch(
        "django.utils.timezone.now",
        return_value=make_aware(datetime(2020, 1, 1, 12, 00, 00)),
    ) as mock:
        yield mock


@pytest.fixture
def premium_product():
    return factories.PremiumProductFactory.create()


@pytest.fixture
def player_profile(premium_product):
    player = factories.PlayerProfileFactory.create(premium_products=premium_product)
    return player


@pytest.fixture
def coach_profile(premium_product):
    guest = factories.CoachProfileFactory.create(premium_products=premium_product)
    return guest


@pytest.fixture
def mock_refresh_inquiries():
    with patch("premium.models.PremiumInquiriesProduct.refresh") as mock:
        yield mock


@pytest.fixture
def mock_refresh_promotion():
    with patch("premium.models.PromoteProfileProduct.refresh") as mock:
        yield mock


@pytest.fixture
def mock_refresh_pm_score():
    with patch("premium.models.CalculatePMScoreProduct.refresh") as mock:
        yield mock


@pytest.fixture
def mock_refresh_premium():
    with patch("premium.models.PremiumProfile._refresh") as mock:
        yield mock


@pytest.fixture
def mock_setup_premium_products():
    with patch("premium.models.PremiumProduct.setup_premium_products") as mock:
        yield mock


class TestPremiumProduct:
    def test_premium_product_as_player(
        self,
        player_profile,
        # mock_refresh_inquiries,
        # mock_refresh_promotion,
        # mock_refresh_pm_score,
    ):
        products = player_profile.premium_products

        assert isinstance(products, PremiumProduct)
        assert products.is_profile_premium is False
        assert products.is_profile_promoted is False
        assert products.is_premium_inquiries_active is False
        assert str(products) == f"{player_profile} -- FREEMIUM"

        premium = products.setup_premium_profile()

        products.refresh_from_db()
        player_profile.refresh_from_db()

        assert products.is_profile_premium is True
        assert products.is_profile_promoted is True
        assert products.is_premium_inquiries_active is True
        assert products.calculate_pm_score
        assert products.promotion
        assert products.inquiries
        assert products.profile == player_profile
        assert str(products) == f"{player_profile} -- PREMIUM"

        # premium = products.setup_premium_profile(PremiumType.YEAR)

        # mock_refresh_inquiries.assert_has_calls(
        #     [call(PremiumType.TRIAL), call(PremiumType.YEAR)]
        # )
        # mock_refresh_promotion.assert_has_calls(
        #     [call(PremiumType.TRIAL), call(PremiumType.YEAR)]
        # )
        # mock_refresh_pm_score.assert_called_once()

    def test_premium_product_not_as_player(
        self,
        coach_profile,
        # mock_refresh_inquiries,
        # mock_refresh_promotion,
        # mock_refresh_pm_score,
    ):
        products = coach_profile.premium_products

        assert isinstance(products, PremiumProduct)
        assert products.is_premium_inquiries_active is False
        assert products.is_profile_promoted is False
        assert products.is_profile_premium is False
        assert str(products) == f"{coach_profile} -- FREEMIUM"

        premium = products.setup_premium_profile(PremiumType.MONTH)

        # mock_refresh_inquiries.assert_called_once()
        # mock_refresh_promotion.assert_called_once()
        # mock_refresh_pm_score.assert_not_called()

        products.refresh_from_db()
        coach_profile.refresh_from_db()

        assert products.is_profile_premium is True
        assert products.is_profile_promoted is True
        assert products.is_premium_inquiries_active is True
        with pytest.raises(AttributeError):
            products.calculate_pm_score
        assert products.promotion
        assert products.inquiries
        assert products.profile == coach_profile
        assert str(products) == f"{coach_profile} -- PREMIUM"

        # products.setup_premium_profile(PremiumType.MONTH)
        #
        # mock_refresh_inquiries.assert_has_calls(
        #     [call(PremiumType.MONTH), call(PremiumType.MONTH)]
        # )
        # mock_refresh_promotion.assert_has_calls(
        #     [call(PremiumType.MONTH), call(PremiumType.MONTH)]
        # )
        # mock_refresh_pm_score.assert_not_called()

    def test_setup_trial_twice(self, player_profile, mock_refresh_premium):
        products = player_profile.premium_products
        products.setup_premium_profile()

        with pytest.raises(ValueError):
            products.setup_premium_profile()

    def test_setup_trial_during_subscription(self, player_profile):
        products = player_profile.premium_products
        products.setup_premium_profile(PremiumType.MONTH)

        with pytest.raises(ValueError):
            products.setup_premium_profile(PremiumType.TRIAL)

    def test_paid_during_trial(self, player_profile):
        products = player_profile.premium_products
        products.setup_premium_profile(PremiumType.TRIAL)
        products.setup_premium_profile(PremiumType.MONTH)

        should_be_valid_until_date = make_aware(
            datetime.now()
            + timedelta(PremiumType.TRIAL.period + PremiumType.MONTH.period)
        ).date()
        products.refresh_from_db()

        assert products.premium.valid_until.date() == should_be_valid_until_date
        assert products.inquiries.valid_until.date() == should_be_valid_until_date
        assert products.promotion.valid_until.date() == should_be_valid_until_date


class TestPromoteProfileProduct:
    @pytest.fixture
    def promote_profile_product(self, premium_product, timezone_now):
        pp = PremiumProfile.objects.create(product=premium_product)
        pp.setup(PremiumType.TRIAL)
        return pp.product.promotion

    def test_promote_profile_product(self, promote_profile_product, timezone_now):
        assert promote_profile_product.days_count == 3
        assert promote_profile_product.is_active is True
        assert promote_profile_product.valid_since.date() == datetime(2020, 1, 1).date()
        assert promote_profile_product.valid_until.date() == datetime(2020, 1, 4).date()

        timezone_now.return_value = make_aware(datetime(2020, 2, 15, 12, 00, 00))

        assert promote_profile_product.is_active is False

        promote_profile_product.refresh(PremiumType.MONTH)
        promote_profile_product.refresh_from_db()

        assert promote_profile_product.is_active is True
        assert (
            promote_profile_product.valid_since.date() == datetime(2020, 2, 15).date()
        )

        assert (
            promote_profile_product.valid_until.date() == datetime(2020, 3, 16).date()
        )


class TestPremiumProfile:
    @pytest.fixture
    def premium_profile(self, premium_product, timezone_now):
        return premium_product.setup_premium_profile(PremiumType.TRIAL)

    def test_premium_profile(
        self, premium_profile, timezone_now, mock_setup_premium_products
    ):
        assert premium_profile.product.trial_tested
        assert premium_profile.is_active is True
        assert premium_profile.valid_since == make_aware(
            datetime(2020, 1, 1, 12, 00, 00)
        )
        assert premium_profile.valid_until == make_aware(
            datetime(2020, 1, 4, 12, 00, 00)
        )  # first is test for 7 days
        mock_setup_premium_products.assert_not_called()

        timezone_now.return_value = make_aware(datetime(2020, 2, 15, 12, 00, 00))

        assert premium_profile.is_active is False

        premium_profile.setup(PremiumType.MONTH)
        premium_profile.refresh_from_db()

        mock_setup_premium_products.assert_called_once()
        assert premium_profile.is_active is True
        assert premium_profile.valid_since == make_aware(
            datetime(2020, 2, 15, 12, 00, 00)
        )
        assert premium_profile.valid_until == make_aware(
            datetime(2020, 3, 16, 12, 00, 00)
        )

    def test_premium_profile_skip_trial(self, premium_product, timezone_now):
        premium = PremiumProfile.objects.create(product=premium_product)
        premium.setup(PremiumType.YEAR)

        assert premium.period == 365
        assert premium.is_active is True
        assert premium_product.trial_tested is False
        assert premium.valid_since == timezone_now()
        assert premium.valid_until == get_date_days_after(
            premium.valid_since, int(premium.period)
        )


class TestCalculatePMScoreProduct:
    @pytest.fixture
    def calculate_pm_score_product(self, player_profile, timezone_now):
        return CalculatePMScoreProduct.objects.create(
            product=player_profile.premium_products
        )

    def test_calculate_pm_score_product_invalid_profile(self, coach_profile):
        with pytest.raises(ValueError) as e:
            CalculatePMScoreProduct.objects.create(
                product=coach_profile.premium_products
            )
        assert str(e.value) == "Product is available only for PlayerProfile."

    def test_calculate_pm_score_product(
        self, calculate_pm_score_product, timezone_now, system_user
    ):
        assert calculate_pm_score_product.awaiting_approval is True
        assert calculate_pm_score_product.created_at == timezone_now()
        assert (
            calculate_pm_score_product.player
            == calculate_pm_score_product.product.profile
        )
        assert calculate_pm_score_product.old_value is None
        assert calculate_pm_score_product.updated_at == timezone_now()

        timezone_now.return_value = make_aware(datetime(2020, 2, 11, 12, 00, 00))
        calculate_pm_score_product.approve(system_user, 10)
        calculate_pm_score_product.refresh_from_db()

        assert calculate_pm_score_product.created_at != timezone_now()
        assert calculate_pm_score_product.awaiting_approval is False
        assert calculate_pm_score_product.approved_by == system_user
        assert calculate_pm_score_product.new_value == 10
        assert calculate_pm_score_product.updated_at == timezone_now()

        timezone_now.return_value = make_aware(datetime(2020, 2, 15, 12, 00, 00))
        calculate_pm_score_product.refresh()
        calculate_pm_score_product.refresh_from_db()

        assert calculate_pm_score_product.created_at == timezone_now()
        assert calculate_pm_score_product.awaiting_approval is True
        assert calculate_pm_score_product.approved_by is None
        assert calculate_pm_score_product.new_value is None
        assert calculate_pm_score_product.old_value == 10


class TestPremiumInquiriesProduct:
    @pytest.fixture
    def premium_inquiries(self, timezone_now, player_profile):
        pi = PremiumInquiriesProduct.objects.create(
            product=player_profile.premium_products
        )
        pi.refresh(PremiumType.MONTH)
        return pi

    def test_premium_inquiries_product(self, premium_inquiries, timezone_now):
        user_inquiries = premium_inquiries.product.profile.user.userinquiry
        assert premium_inquiries.is_active is True
        assert premium_inquiries.valid_since == make_aware(
            datetime(2020, 1, 1, 12, 00, 00)
        )
        assert premium_inquiries.valid_until == make_aware(
            datetime(2020, 1, 31, 12, 00, 00)
        )
        assert user_inquiries.limit == 12

        timezone_now.return_value = make_aware(datetime(2020, 2, 15, 12, 00, 00))
        user_inquiries.refresh_from_db()

        assert premium_inquiries.is_active is False
        assert user_inquiries.limit == 2

        premium_inquiries.refresh(PremiumType.MONTH)
        user_inquiries.refresh_from_db()
        premium_inquiries.refresh_from_db()

        assert premium_inquiries.is_active is True
        assert premium_inquiries.valid_since == make_aware(
            datetime(2020, 2, 15, 12, 00, 00)
        )
        assert premium_inquiries.valid_until == make_aware(
            datetime(2020, 3, 16, 12, 00)
        )
        assert user_inquiries.limit == 12


class TestProduct:
    def test_inquiry_products_qs(self):
        inquiry_products = Product.objects.filter(visible=True, ref="INQUIRIES")

        assert [product.name for product in inquiry_products] == [
            "PREMIUM_INQUIRIES_L",
            "PREMIUM_INQUIRIES_XL",
            "PREMIUM_INQUIRIES_XXL",
        ]
        assert inquiry_products.count() == 3

    def test_premium_products(self):
        premium_products = Product.objects.filter(ref="PREMIUM", visible=True)

        assert premium_products.count() == 4
        assert [product.name for product in premium_products] == [
            "PLAYER_PREMIUM_PROFILE_MONTH",
            "PLAYER_PREMIUM_PROFILE_YEAR",
            "PREMIUM_PROFILE_MONTH",
            "PREMIUM_PROFILE_YEAR",
        ]
