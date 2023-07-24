from rest_framework import serializers
from products.models import Product, Request


class TestFormSerializer(serializers.ModelSerializer):
    raw_body = serializers.DictField()

    class Meta:
        model = Request
        fields = ["product", "user", "raw_body"]
