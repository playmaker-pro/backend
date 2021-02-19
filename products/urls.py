from django.urls import path
from . import views
# from . import api


app_name = "products"


urlpatterns = [

    path("", views.ProductTailsView.as_view(), name="products"),
    path("<int:id>/", views.ProductView.as_view(), name="detail"),
    path("send/<int:id>/", views.SendRequestView.as_view(), name='send')
]
