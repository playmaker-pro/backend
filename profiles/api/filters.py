import typing
from decimal import Decimal
from typing import List

from django.db.models import ExpressionWrapper, F, FloatField, QuerySet
from django.db.models import functions as django_base_functions
from django_filters import rest_framework as filters

from api.filters import MultipleFilter
from profiles.models import CoachProfile, PlayerProfile, ProfileTransferRequest


class TransferRequestCatalogueFilter(filters.FilterSet):
    position = MultipleFilter()
    league = MultipleFilter()
    latitude = filters.NumberFilter(method="filter_by_location")
    longitude = filters.NumberFilter(method="filter_by_location")
    radius = filters.NumberFilter(method="filter_by_location")
    number_of_trainings = MultipleFilter()
    salary = MultipleFilter()
    benefits = MultipleFilter(method="filter_benefits")

    class Meta:
        model = ProfileTransferRequest
        fields = [
            "position",
            "league",
            "latitude",
            "longitude",
            "radius",
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

    def filter_by_location(
        self, queryset: QuerySet, name: str, value: typing.Any
    ) -> QuerySet:
        """
        Filter a queryset based on proximity to a specified geolocation.

        This method filters the queryset to include only items that are within a
        specified radius from a given latitude and longitude,
        using the Haversine formula.
        """

        latitude = self.data.get("latitude")
        longitude = self.data.get("longitude")
        radius = self.data.get("radius", 1)  # Default radius of 1 kilometer

        # Proceed only if latitude and longitude are provided
        if latitude and longitude:
            latitude = Decimal(latitude)
            longitude = Decimal(longitude)
            radius = Decimal(radius)
            earth_radius = 6371  # Earth's radius in kilometers

            # Use a default radius if not provided
            default_radius = 1  # Default radius in kilometers
            radius = Decimal(radius) if radius else default_radius

            return (
                queryset.annotate(
                    distance=ExpressionWrapper(
                        earth_radius
                        * django_base_functions.ACos(
                            django_base_functions.Cos(
                                django_base_functions.Radians(latitude)
                            )
                            * django_base_functions.Cos(
                                django_base_functions.Radians(
                                    F(
                                        "requesting_team__team_history__club__stadion_address__latitude"  # noqa 501
                                    )
                                )
                            )
                            * django_base_functions.Cos(
                                django_base_functions.Radians(
                                    F(
                                        "requesting_team__team_history__club__stadion_address__longitude"  # noqa 501
                                    )
                                )
                                - django_base_functions.Radians(longitude)
                            )
                            + django_base_functions.Sin(
                                django_base_functions.Radians(latitude)
                            )
                            * django_base_functions.Sin(
                                django_base_functions.Radians(
                                    F(
                                        "requesting_team__team_history__club__stadion_address__latitude"  # noqa 501
                                    )
                                )
                            )
                        ),
                        output_field=FloatField(),
                    )
                )
                .filter(distance__lt=radius)
                .distinct()
            )
        return queryset


class DefaultProfileFilter(filters.FilterSet):
    """
    Default filter set for profiles, primarily filtering based on gender.
    This filter set can be used as a fallback for profile types that do not require
    specialized filtering beyond gender.
    """

    gender = filters.CharFilter(field_name="user__userpreferences__gender")

    class Meta:
        fields = ["gender"]


class PlayerProfileFilter(filters.FilterSet):
    """
    Filter set for PlayerProfile models, allowing filtering by position and gender.
    This filter set is designed to accommodate the specific attributes of player profiles,
    such as their main playing position.
    """

    position = filters.CharFilter(field_name="player_positions__player_position_id")
    gender = filters.CharFilter(field_name="user__userpreferences__gender")

    class Meta:
        model = PlayerProfile
        fields = ["position", "gender"]


class CoachProfileFilter(filters.FilterSet):
    """
    Filter set for CoachProfile models, allowing filtering by coach role and gender.
    This filter set caters to the unique attributes of coach profiles,
    including their specific coaching roles.
    """

    coach_role = filters.CharFilter(field_name="coach_role")
    gender = filters.CharFilter(field_name="user__userpreferences__gender")

    class Meta:
        model = CoachProfile
        fields = ["coach_role", "gender"]


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
