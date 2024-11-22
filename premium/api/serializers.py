from rest_framework import serializers

from premium.models import Product, PromoteProfileProduct


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = ("visible",)


class PromoteProfileProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoteProfileProduct
        fields = ("is_active", "days_count", "days_left")
