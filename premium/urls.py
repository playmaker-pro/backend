from django.urls import path
from .views import ProductView


app_name = "premium"

urlpatterns = [
    path(
        "",
        ProductView.as_view(),
        name="main_page",
    ),
]
