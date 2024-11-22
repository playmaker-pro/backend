from django.urls import path

from .views import ProductInfoView

app_name = "premium"

urlpatterns = [
    path(
        "products/inquiries/",
        ProductInfoView.as_view({"get": "list_inquiry_products"}),
        name="list_inquiry_products",
    ),
    path(
        "products/premium/",
        ProductInfoView.as_view({"get": "get_premium_product"}),
        name="get_premium_product",
    ),
    path(
        "transaction/<int:product_id>/create/",
        ProductInfoView.as_view({"post": "create_transaction"}),
        name="create_transaction",
    ),
]
