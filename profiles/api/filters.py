from typing import List

from django.db.models import QuerySet
from django_filters import rest_framework as filters

from api.filters import MultipleFilter
from profiles.models import ProfileTransferRequest


class TransferRequestCatalogueFilter(filters.FilterSet):
    player_position = MultipleFilter()
    league = MultipleFilter()
    voivodeship = MultipleFilter()
    number_of_trainings = MultipleFilter()
    salary = MultipleFilter()
    benefits = MultipleFilter(method="filter_benefits")

    class Meta:
        model = ProfileTransferRequest
        fields = [
            "player_position",
            "league",
            "voivodeship",
            "number_of_trainings",
            "salary",
            "benefits",
        ]

    def filter_benefits(self, queryset: QuerySet, _, value: List[str]) -> QuerySet:
        """Filter queryset by benefits."""
        res = []
        for val in value:
            for obj in queryset:
                if val in obj.benefits:
                    res.append(obj.pk)
        return queryset.filter(pk__in=res)
