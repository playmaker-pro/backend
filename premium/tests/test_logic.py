from datetime import datetime
from unittest.mock import patch

import pytest
from django.utils.timezone import make_aware

from premium.models import (
    CalculatePMScoreProduct,
    PremiumInquiriesProduct,
    PremiumProduct,
    PremiumProfile,
    Product,
    PromoteProfileProduct,
)
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
    with patch("premium.models.PremiumProfile.refresh") as mock:
        yield mock


@pytest.fixture
def mock_setup_premium_products():
    with patch("premium.models.PremiumProduct.setup_premium_products") as mock:
        yield mock


class TestPremiumProduct:
    def test_premium_product_as_player(
        self,
        player_profile,
        mock_refresh_inquiries,
        mock_refresh_promotion,
        mock_refresh_pm_score,
        mock_refresh_premium,
    ):
        products = player_profile.premium_products

        assert isinstance(products, PremiumProduct)
        assert products.is_profile_premium is False
        assert products.is_profile_promoted is False
        assert products.is_premium_inquiries_active is False
        assert str(products) == f"{player_profile} -- FREEMIUM"

        premium = products.setup_premium_profile()
        premium.setup()

        mock_refresh_inquiries.assert_not_called()
        mock_refresh_promotion.assert_not_called()
        mock_refresh_pm_score.assert_not_called()
        mock_refresh_premium.assert_not_called()

        products.refresh_from_db()
        player_profile.refresh_from_db()

        assert products.is_profile_premium is True
        assert products.is_profile_promoted is True
        assert products.is_premium_inquiries_active is True
        assert products.calculate_pm_score
        assert products.promotion
        assert products.inquiries
        assert products.profile == player_profile
        assert products.user == player_profile.user
        assert str(products) == f"{player_profile} -- PREMIUM"

        premium.refresh()

        mock_refresh_premium.assert_called_once()

        premium.setup()

        mock_refresh_inquiries.assert_called_once()
        mock_refresh_promotion.assert_called_once()
        mock_refresh_pm_score.assert_called_once()

    def test_premium_product_not_as_player(
        self,
        coach_profile,
        mock_refresh_inquiries,
        mock_refresh_promotion,
        mock_refresh_pm_score,
        mock_refresh_premium,
    ):
        products = coach_profile.premium_products

        assert isinstance(products, PremiumProduct)
        assert products.is_premium_inquiries_active is False
        assert products.is_profile_promoted is False
        assert products.is_profile_premium is False
        assert str(products) == f"{coach_profile} -- FREEMIUM"

        premium = products.setup_premium_profile()
        premium.setup()

        mock_refresh_inquiries.assert_not_called()
        mock_refresh_promotion.assert_not_called()
        mock_refresh_pm_score.assert_not_called()
        mock_refresh_premium.assert_not_called()

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
        assert products.user == coach_profile.user
        assert str(products) == f"{coach_profile} -- PREMIUM"

        premium.refresh()

        mock_refresh_premium.assert_called_once()

        premium.setup()

        mock_refresh_inquiries.assert_called_once()
        mock_refresh_promotion.assert_called_once()
        mock_refresh_pm_score.assert_not_called()


class TestPromoteProfileProduct:
    @pytest.fixture
    def promote_profile_product(self, premium_product, timezone_now):
        return PromoteProfileProduct.objects.create(product=premium_product)

    def test_promote_profile_product(self, promote_profile_product, timezone_now):
        assert promote_profile_product.days_count == 30
        assert promote_profile_product.is_active is True
        assert promote_profile_product.valid_since == make_aware(
            datetime(2020, 1, 1, 12, 00, 00)
        )
        assert promote_profile_product.valid_until == make_aware(
            datetime(2020, 1, 31, 12, 00, 00)
        )

        timezone_now.return_value = make_aware(datetime(2020, 2, 15, 12, 00, 00))

        assert promote_profile_product.is_active is False

        promote_profile_product.refresh()
        promote_profile_product.refresh_from_db()

        assert promote_profile_product.is_active is True
        assert promote_profile_product.valid_since == make_aware(
            datetime(2020, 2, 15, 12, 00, 00)
        )
        assert promote_profile_product.valid_until == make_aware(
            datetime(2020, 3, 16, 12, 00, 00)
        )


class TestPremiumProfile:
    @pytest.fixture
    def premium_profile(self, premium_product, timezone_now):
        return PremiumProfile.objects.create(product=premium_product)

    def test_premium_profile(
        self, premium_profile, timezone_now, mock_setup_premium_products
    ):
        assert premium_profile.is_active is True
        assert premium_profile.valid_since == make_aware(
            datetime(2020, 1, 1, 12, 00, 00)
        )
        assert premium_profile.valid_until == make_aware(
            datetime(2020, 1, 31, 12, 00, 00)
        )
        mock_setup_premium_products.assert_not_called()

        timezone_now.return_value = make_aware(datetime(2020, 2, 15, 12, 00, 00))

        assert premium_profile.is_active is False

        premium_profile.refresh()
        premium_profile.refresh_from_db()

        mock_setup_premium_products.assert_called_once()
        assert premium_profile.is_active is True
        assert premium_profile.valid_since == make_aware(
            datetime(2020, 2, 15, 12, 00, 00)
        )
        assert premium_profile.valid_until == make_aware(
            datetime(2020, 3, 16, 12, 00, 00)
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
        return PremiumInquiriesProduct.objects.create(
            product=player_profile.premium_products
        )

    def test_premium_inquiries_product(self, premium_inquiries, timezone_now):
        user_inquiries = premium_inquiries.product.profile.user.userinquiry

        assert premium_inquiries.is_active is True
        assert premium_inquiries.valid_since == make_aware(
            datetime(2020, 1, 1, 12, 00, 00)
        )
        assert premium_inquiries.valid_until == make_aware(
            datetime(2020, 1, 31, 12, 00, 00)
        )
        assert user_inquiries.limit == 25

        timezone_now.return_value = make_aware(datetime(2020, 2, 15, 12, 00, 00))
        user_inquiries.refresh_from_db()

        assert premium_inquiries.is_active is False
        assert user_inquiries.limit == 5

        premium_inquiries.refresh()
        user_inquiries.refresh_from_db()

        assert premium_inquiries.is_active is True
        assert premium_inquiries.valid_since == make_aware(
            datetime(2020, 2, 15, 12, 00, 00)
        )
        assert premium_inquiries.valid_until == make_aware(
            datetime(2020, 3, 16, 12, 00, 00)
        )
        assert user_inquiries.limit == 25


class TestProduct:
    def test_inquiry_products_qs(self):
        inquiry_products = Product.objects.filter(visible=True, ref="INQUIRIES")

        assert [product.name for product in inquiry_products] == [
            "PREMIUM_INQUIRIES_5",
            "PREMIUM_INQUIRIES_10",
            "PREMIUM_INQUIRIES_25",
        ]
        assert inquiry_products.count() == 3

    def test_premium_product(self):
        premium_product = Product.objects.get(ref="PREMIUM", visible=True)

        assert premium_product.name == "PREMIUM"
        assert premium_product.name_readable == "Profil Premium"
