from rest_framework import serializers
from django.utils.translation import gettext as _

from api.i18n import I18nSerializerMixin
from premium.models import PremiumProfile, Product, PromoteProfileProduct


class ProductSerializer(I18nSerializerMixin, serializers.ModelSerializer):
    price_per_cycle = serializers.DecimalField(max_digits=5, decimal_places=2)
    name_readable = serializers.SerializerMethodField()

    class Meta:
        model = Product
        exclude = ("visible",)

    def get_name_readable(self, obj):
        """Return translated name_readable"""
        return _(obj.name_readable)


class PromoteProfileProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoteProfileProduct
        fields = ("is_active", "days_count", "days_left")


class PremiumProfileProductSerializer(I18nSerializerMixin, serializers.ModelSerializer):
    inquiries_refresh = serializers.DateTimeField(
        source="product.inquiries.inquiries_refreshed_at"
    )

    class Meta:
        model = PremiumProfile
        fields = (
            "valid_since",
            "valid_until",
            "period",
            "is_active",
            "is_trial",
            "inquiries_refresh",
        )
