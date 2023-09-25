from django.db.models import QuerySet
from django_filters import rest_framework as filters

from clubs import models


class ClubFilter(filters.FilterSet):
    """
    A filterset class for the Club model.
    It includes filters for season, name, and gender.
    """

    season = filters.CharFilter(method="filter_by_season")
    name = filters.CharFilter(field_name="short_name", lookup_expr="icontains")
    gender = filters.CharFilter(method="filter_gender")

    class Meta:
        model = models.Club
        fields = ["season", "name", "gender"]

    def filter_by_season(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filters the queryset by the season.
        """
        return queryset.filter(
            teams__historical__league_history__season__name=value
        ).distinct()

    def filter_gender(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filters the queryset by the gender.
        """

        if value.upper() == models.Gender.MALE:
            return queryset.filter(teams__gender=models.Gender.get_male_object())
        elif value.upper() == models.Gender.FEMALE:
            return queryset.filter(teams__gender=models.Gender.get_female_object())
        else:
            return queryset
