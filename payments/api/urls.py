from django.urls import path as _path

from payments.api import views as _views

urlpatterns = [
    _path(
        "resolve/tpay/",
        _views.TpayWebhook.as_view({"post": "resolve_transaction"}),
        name="resolve_tpay_result",
    ),
]
