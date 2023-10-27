from django.db.models import QuerySet
from rest_framework import viewsets

from api.pagination import PagePagination


class EndpointView(viewsets.GenericViewSet):
    """Base class for building views"""

    pagination_class = PagePagination

    def get_queryset(self) -> QuerySet:
        ...

    def get_paginated_queryset(self, qs: QuerySet = None) -> QuerySet:
        """Paginate queryset to optimize serialization"""
        qs: QuerySet = qs if qs is not None else self.get_queryset()
        return self.paginate_queryset(qs)
