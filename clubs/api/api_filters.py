from django.db.models import Exists, OuterRef, QuerySet
from django_filters import rest_framework as filters

from clubs import models


class ClubFilter(filters.FilterSet):
    """
    A filterset class for the Club model, allowing filtering by season, gender, and name.  # noqa 501
    """

    season = filters.CharFilter(method="filter_season")
    gender = filters.CharFilter(method="filter_gender")
    name = filters.CharFilter(field_name="short_name", lookup_expr="icontains")

    class Meta:
        model = models.Club
        fields = ["season", "name", "gender"]

    def filter_season(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filter the queryset by the season.

        This method constructs a subquery to filter clubs based on the season
        of the related teams. Only clubs that have at least one team playing
        in the specified season are included in the final queryset.
        """
        if value:
            teams_subquery = models.Team.objects.filter(
                club=OuterRef("pk"), league_history__season__name=value
            )
            return queryset.annotate(has_season_team=Exists(teams_subquery)).filter(
                has_season_team=True
            )
        return queryset

    def filter_gender(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filter the queryset by gender.

        This method constructs a subquery to filter clubs based on the gender
        of the related teams. Only clubs that have at least one team matching
        the specified gender are included in the final queryset.
        """
        if value.upper() in ["M", "F"]:
            gender_filter = (
                models.Gender.get_male_object()
                if value.upper() == models.Gender.MALE
                else models.Gender.get_female_object()
            )
            teams_subquery = models.Team.objects.filter(
                club=OuterRef("pk"), gender=gender_filter
            )
            return queryset.annotate(has_gender_team=Exists(teams_subquery)).filter(
                has_gender_team=True
            )
        return queryset

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Filter the queryset based on the provided filters.
        """
        return super().filter_queryset(queryset)
