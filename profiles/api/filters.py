from typing import List

from django.db.models import QuerySet
from django_filters import rest_framework as filters

from api.filters import MultipleFilter
from profiles.models import PlayerProfile, ProfileTransferRequest


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


class PlayerProfileFilters(filters.FilterSet):
    # FIXME: lremkowicz: think about moving to django-filter in the future
    #  for profiles/ endpoint. Class not used right now
    positions = MultipleFilter(method="filter_position")
    class Meta:
        model = PlayerProfile
        fields = ["player_positions"]

    def filter_position(self, queryset: QuerySet, _, value: List[int]) -> QuerySet:
        values = [int(val) for val in value if val.isdigit()]
        if values:
            return queryset.filter(player_positions__player_position_id__in=values)
        return queryset