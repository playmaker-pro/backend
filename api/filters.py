import abc
from typing import Protocol

from django.db.models import QuerySet
from django_filters import rest_framework as filters
from django_filters.fields import MultipleChoiceField
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


class MultipleField(MultipleChoiceField):
    """Custom multiple choice field."""

    def valid_value(self, value) -> bool:
        return True


class MultipleFilter(filters.MultipleChoiceFilter):
    """Custom multiple choice filter needed for filtering by multiple values."""

    field_class = MultipleField


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    """
    A custom filter class that extends django-filters to allow filtering
    by multiple numeric values.
    """

    pass
