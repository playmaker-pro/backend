from django.urls import path as _path

from payments.api import views as _views

urlpatterns = [
    _path(
        "create/<int:transaction_type_id>/",
        _views.TransactionAPI.as_view({"post": "create_transaction_for_type"}),
        name="create_transaction",
    ),
    _path(
        "inquiries/list-types/",
        _views.TransactionAPI.as_view({"get": "list_inquiry_transaction_types"}),
        name="list_inquiry_types",
    ),
    _path(
        "resolve/tpay/",
        _views.TpayReceiverAPI.as_view({"post": "resolve_transaction"}),
        name="resolve_tpay_result",
    ),
]
