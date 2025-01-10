from rest_framework import serializers

from premium.models import PremiumProfile, Product, PromoteProfileProduct


class ProductSerializer(serializers.ModelSerializer):
    price_per_cycle = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = Product
        exclude = ("visible",)


class PromoteProfileProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoteProfileProduct
        fields = ("is_active", "days_count", "days_left")


class PremiumProfileProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = PremiumProfile
        fields = ("valid_since", "valid_until", "period", "is_active", "is_trial")
