import abc
from typing import Protocol

from django.db.models import QuerySet
from rest_framework.request import Request


class APIFilter(Protocol):
    """Base interface for API filters"""

    request: Request
    query_params: dict
    queryset: QuerySet

    @abc.abstractmethod
    def get_queryset(self) -> QuerySet:
        """Get queryset for view"""
        ...

    @abc.abstractmethod
    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """Filter queryset for view"""
        ...
