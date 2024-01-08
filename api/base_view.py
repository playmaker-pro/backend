from typing import Optional

from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework import viewsets

from api.pagination import PagePagination


class EndpointView(viewsets.GenericViewSet):
    """Base class for building views"""

    pagination_class = PagePagination

    def get_queryset(self) -> QuerySet:
        return super().get_queryset()

    def get_paginated_queryset(self, qs: QuerySet = None) -> Optional[list]:
        """Paginate queryset to optimize serialization"""
        qs: QuerySet = qs if qs is not None else self.get_queryset()
        return self.paginate_queryset(qs)


class EndpointViewWithFilter(EndpointView):
    """Base class for building views with filters"""

    filter_backends = (filters.DjangoFilterBackend,)
