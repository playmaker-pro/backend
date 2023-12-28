from django.urls import path as _path

from payments.api.views import TransactionAPI as _TransactionAPI

urlpatterns = [
    _path(
        "transaction/create/",
        _TransactionAPI.as_view({"post": "create_transaction"}),
    ),
    _path(
        "transaction/resolve/",
        _TransactionAPI.as_view({"post": "resolve_transaction"}),
    ),
]
