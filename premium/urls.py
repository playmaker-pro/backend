from django.urls import path
from .views import ProductView
from .api_views import PremiumRequestAPIView

app_name = "premium"

urlpatterns = [
    path(
        "",
        ProductView.as_view(),
        name="main_page",
    ),
    path(
        "create/",
        PremiumRequestAPIView.as_view(),
        name="create_request",
    ),
]
