from functools import cached_property

from django.db.models import QuerySet

from api import errors as api_errors
from api import utils as api_utils
from api.errors import InvalidAPIRequestParam
from api.filters import APIFilter
from profiles import errors as profile_errors

from . import models, services


class ProfileListAPIFilter(APIFilter):
    profile_service = services.ProfileService()

    PARAMS_PARSERS = {
        "youth": api_utils.convert_bool,
        "min_age": api_utils.convert_int,
        "max_age": api_utils.convert_int,
        "position": api_utils.convert_str_list,
        "league": api_utils.convert_int_list,
        "latitude": api_utils.convert_float,
        "longitude": api_utils.convert_float,
        "radius": api_utils.convert_int,
        "country": api_utils.convert_str_list,
        "language": api_utils.convert_str_list,
        # define other filter params requiring validation here
    }

    @cached_property
    def model(self) -> models.PROFILE_MODELS:
        """Get Profile class based on role defined within params"""
        role: str = self.request.query_params.get("role")
        try:
            return self.profile_service.get_model_by_role(role)
        except ValueError:
            raise profile_errors.InvalidProfileRole

    def get_queryset(self) -> QuerySet:
        """Get queryset based on role"""
        self.queryset: QuerySet = self.model.objects.all().order_by("pk")
        self.filter_queryset(self.queryset)
        return self.queryset

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """Filter given queryset based on validated query_params"""
        self.define_query_params()
        self.queryset = self.queryset or queryset

        if self.model is models.PlayerProfile:
            self.player_filters()
        elif self.model is models.CoachProfile:
            self.coach_filters()
        self.common_filters()

        return self.queryset

    def player_filters(self) -> None:
        """Filters related with PlayerProfile"""
        self.filter_youth()
        self.filter_position()
        self.filter_league()

    def coach_filters(self) -> QuerySet:
        """Filters related with GuestProfile"""
        ...

    def common_filters(self) -> None:
        """Common filters for each type of profile"""
        if not (
            self.query_params.get("youth", False) and self.model is models.PlayerProfile
        ):
            self.filter_age()

        self.filter_localization()
        self.filter_country()
        self.filter_language()

    def define_query_params(self) -> None:
        """Validate query_params and save as self.query_params"""
        params: dict = {}

        for key, parser in self.PARAMS_PARSERS.items():
            value = (
                self.request.query_params.getlist(key)
                if parser in api_utils.LIST_PARSERS
                else self.request.query_params.get(key)
            )
            if key_in_params := value:
                try:
                    params[key] = parser(key, key_in_params)
                except ValueError as e:
                    raise InvalidAPIRequestParam(e)
        self.query_params = params

    def filter_language(self) -> None:
        """Filter queryset by language"""
        if language := self.query_params.get("language"):
            try:
                self.queryset = self.profile_service.filter_language(
                    self.queryset, language
                )
            except ValueError as e:
                raise api_errors.InvalidLanguageCode(e)

    def filter_country(self) -> None:
        """Filter queryset by language"""
        if country := self.query_params.get("country"):
            try:
                self.queryset = self.profile_service.filter_country(
                    self.queryset, country
                )
            except ValueError as e:
                raise api_errors.InvalidCountryCode(e)

    def filter_localization(self) -> None:
        """Filter queryset by localization"""
        longitude, latitude, radius = (
            self.query_params.get("longitude"),
            self.query_params.get("latitude"),
            self.query_params.get("radius", 1),
        )
        if longitude and latitude:
            self.queryset = self.profile_service.filter_localization(
                self.queryset, latitude, longitude, radius
            )

    def filter_league(self) -> None:
        """Filter queryset by player league"""
        if league := self.query_params.get("league"):
            self.queryset = self.profile_service.filter_player_league(
                self.queryset, league
            )

    def filter_position(self) -> None:
        """Filter queryset by player position"""
        if position := self.query_params.get("position"):
            self.queryset = self.profile_service.filter_player_position(
                self.queryset, position
            )

    def filter_youth(self) -> None:
        """Filter queryset by youth players"""
        if self.query_params.get("youth"):
            self.queryset = self.profile_service.filter_youth_players(self.queryset)

    def filter_age(self) -> None:
        """Filter queryset by age"""
        if min_age := self.query_params.get("min_age"):
            self.queryset = self.profile_service.filter_min_age(self.queryset, min_age)

        if max_age := self.query_params.get("max_age"):
            self.queryset = self.profile_service.filter_max_age(self.queryset, max_age)
