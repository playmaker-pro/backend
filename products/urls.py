from django.urls import path, include
from . import views

app_name = "products"


urlpatterns = [
    path("", views.ProductTailsView.as_view(), name="products"),
    path("transfer/", include("landingpage.urls"), name="products"),
    path("premium/", include("premium.urls"), name="premium"),
    path("<slug:slug>/", views.ProductView.as_view(), name="detail"),
    path("send/<int:id>/", views.SendRequestView.as_view(), name="send"),
]
