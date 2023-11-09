from django.db.models import QuerySet, OuterRef, Exists
from django_filters import rest_framework as filters

from clubs import models


class ClubFilter(filters.FilterSet):
    """
    A filterset class for the Club model, allowing filtering by season, gender, and name.
    """

    season = filters.CharFilter(method="filter_by_criteria")
    gender = filters.CharFilter(method="filter_by_criteria")
    name = filters.CharFilter(field_name="short_name", lookup_expr="icontains")

    class Meta:
        model = models.Club
        fields = ["season", "name", "gender"]

    def filter_by_criteria(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filter the queryset by season and gender criteria.
        This method constructs a subquery to filter clubs based on related team attributes.

        Note: The 'name' and 'value' parameters are part of the standard
        signature for filter methods in Django Filters, but in this case,
        they are not used because the method relies on self.data to access filter criteria.
        """
        teams_subquery = models.Team.objects.filter(club=OuterRef("pk"))

        # Filter by season
        if "season" in self.data:
            teams_subquery = teams_subquery.filter(
                historical__league_history__season__name=self.data["season"]
            )

        # Filter by gender
        if "gender" in self.data:
            gender_filter = (
                models.Gender.get_male_object()
                if self.data["gender"].upper() == models.Gender.MALE
                else models.Gender.get_female_object()
            )
            teams_subquery = teams_subquery.filter(gender=gender_filter)

        # Apply filter
        queryset = queryset.annotate(has_matching_team=Exists(teams_subquery)).filter(
            has_matching_team=True
        )

        return queryset.distinct()

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Filter the queryset based on the provided filters.
        """
        return super().filter_queryset(queryset)
