"""
Tests for premium product internationalization (i18n) functionality.

Tests the translation of product names in both API responses and TPay transactions
to ensure consistent language support across the application.
"""

import pytest
from django.utils import translation
from django.urls import reverse
from rest_framework.test import APIClient

from utils.factories import ProductFactory, TransactionFactory
from premium.models import Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def premium_product():
    return ProductFactory.create(
        name="TEST_PREMIUM_PRODUCT",
        name_readable="Miesięczne konto premium dla profilu",
        price=99.99,
        ref=Product.ProductReference.PREMIUM,
        visible=True
    )

@pytest.fixture
def transaction(premium_product, player_profile):
    return TransactionFactory.create(
        user=player_profile.user,
        product=premium_product
    )

class TestProductTranslation:
    """Test product name translation in API responses."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.mark.parametrize("language,expected", [
        ('pl', 'Miesięczne konto premium dla profilu'),
        ('en', 'Monthly premium account for profile'), 
        ('de', 'Monatliches Premium-Konto für Profil'),
        ('uk-UA', 'Місячний преміум акаунт для профілю'),
    ])
    def test_product_api_translation_with_headers(self, api_client, premium_product, language, expected):
        """Test API endpoint returns translated product names based on X-Language header."""
        url = reverse("api:premium:get_premium_product")
        
        response = api_client.get(url, HTTP_X_LANGUAGE=language)
        
        assert response.status_code == 200
        
        data = response.json()
        results = data.get('results', data) if isinstance(data, dict) else data
        
        test_product = next(
            (item for item in results if item['name'] == 'TEST_PREMIUM_PRODUCT'),
            None
        )
        
        assert test_product is not None, f"Test product not found in API response"
        assert test_product['name_readable'] == expected


class TestTransactionTranslation:
    @pytest.mark.parametrize("language,expected", [
        ('pl', 'PLAYMAKER.PRO | Miesięczne konto premium dla profilu Piłkarz'),
        ('en', 'PLAYMAKER.PRO | Monthly premium account for profile Player'),
        ('de', 'PLAYMAKER.PRO | Monatliches Premium-Konto für Profil Spieler'),
        ('uk-UA', 'PLAYMAKER.PRO | Місячний преміум акаунт для профілю Гравець'),
    ])
    def test_transaction_description_translation(self, transaction, language, expected):
        """Test that transaction descriptions are properly translated for TPay with dynamic profile types."""
        with translation.override(language):
            description = transaction.get_localized_description()
            assert description == expected
    
    def test_transaction_uses_active_language(self, transaction):
        """Test that translation uses the currently active Django language."""
        translation.activate('de')
        description = transaction.get_localized_description()
        assert description == 'PLAYMAKER.PRO | Monatliches Premium-Konto für Profil Spieler'
        
    def test_different_profile_types_generate_different_descriptions(self, premium_product):
        """Test that different profile types generate appropriate profile-specific descriptions."""
        from utils.factories import UserFactory
        from profiles.models import PlayerProfile, GuestProfile, ClubProfile, ScoutProfile
        from payments.models import Transaction
        
        # Test with different profile types
        profiles_and_expected = [
            (PlayerProfile, 'PLAYMAKER.PRO | Miesięczne konto premium dla profilu Piłkarz'),
            (GuestProfile, 'PLAYMAKER.PRO | Miesięczne konto premium dla profilu Kibic'),
            (ClubProfile, 'PLAYMAKER.PRO | Miesięczne konto premium dla profilu Działacz klubu'),
            (ScoutProfile, 'PLAYMAKER.PRO | Miesięczne konto premium dla profilu Skaut'),
        ]
        
        for profile_class, expected_description in profiles_and_expected:
            # Create user and profile
            user = UserFactory.create()
            profile_class.objects.create(user=user)
            
            # Create transaction
            transaction = Transaction.objects.create(
                user=user,
                product=premium_product
            )
            
            with translation.override('pl'):
                description = transaction.get_localized_description()
                assert description == expected_description
