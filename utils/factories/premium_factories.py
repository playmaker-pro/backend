import factory

from premium import models


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Product
        django_get_or_create = ("name",)

    name = "Test Type"
    name_readable = "Test Type Readable"
    price = 10.00
    ref = models.Product.ProductReference.INQUIRIES


class PremiumProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PremiumProduct
