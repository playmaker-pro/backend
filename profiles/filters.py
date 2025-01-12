import random
import typing
from datetime import timedelta
from functools import cached_property

from django.db.models import BooleanField, Case, F, QuerySet, Value, When
from django.utils import timezone

from api import errors as api_errors
from api import utils as api_utils
from api.errors import InvalidAPIRequestParam
from api.filters import APIFilter
from labels.utils import (
    apply_label_filters,
    get_profile_specific_ids,
    get_user_related_ids,
    validate_labels,
)
from profiles import models, services
from profiles.api.errors import IncorrectProfileRole


class ProfileListAPIFilter(APIFilter):
    service = services.ProfileFilterService()

    # define other filter params requiring validation below.
    # New values will be added to self.query_params
    PARAMS_PARSERS = {
        "youth": api_utils.convert_bool,
        "min_age": api_utils.convert_int,
        "max_age": api_utils.convert_int,
        "position": api_utils.convert_list_with_string_to_int,
        "league": api_utils.convert_int_list,
        "latitude": api_utils.convert_float,
        "longitude": api_utils.convert_float,
        "radius": api_utils.convert_int,
        "country": api_utils.convert_str_list,
        "language": api_utils.convert_str_list,
        "gender": api_utils.convert_str_list,
        "shuffle": api_utils.convert_bool,
        "not_me": api_utils.convert_bool,
        "licence": api_utils.convert_str_list,
        "labels": api_utils.convert_str_list,
        "transfer_status": api_utils.convert_str_list,
        "additional_info": api_utils.convert_str_list,
        "number_of_trainings": api_utils.convert_str,
        "benefits": api_utils.convert_str_list,
        "salary": api_utils.convert_str,
        "transfer_status_league": api_utils.convert_int_list,
        "min_pm_score": api_utils.convert_int,
        "max_pm_score": api_utils.convert_int,
        "observed": api_utils.convert_bool,
        "sort": api_utils.convert_str,
        "last_activity": api_utils.convert_str,
    }

    @cached_property
    def model(self) -> models.PROFILE_MODELS:
        """Get Profile class based on role defined within params"""
        role: str = self.request.query_params.get("role")
        try:
            return self.service.profile_service.get_model_by_role(role)
        except ValueError:
            raise IncorrectProfileRole

    def filter_last_activity(self) -> None:
        """Filter queryset by last activity"""
        if last_activity := self.query_params.get("last_activity"):
            now = timezone.now()
            last_activity_timestamp_mapper = {
                "last_week": now - timedelta(weeks=1),
                "last_month": now - timedelta(weeks=4),
                "last_two_months": now - timedelta(weeks=8),
                "last_six_months": now - timedelta(weeks=24),
                "last_year": now - timedelta(weeks=52),
                "more_than_year_ago": now - timedelta(weeks=52),
            }

            try:
                last_activity_timestamp = last_activity_timestamp_mapper[last_activity]
            except KeyError:
                return
            if last_activity == "more_than_year_ago":
                self.queryset = self.queryset.filter(
                    user__last_activity__lt=last_activity_timestamp
                )
            else:
                self.queryset = self.queryset.filter(
                    user__last_activity__gte=last_activity_timestamp
                )

    def sort_promoted_first(self, qs: QuerySet) -> QuerySet:
        """Set default sorting for queryset - promoted profiles first, then by last activity"""
        now = timezone.now()

        return qs.annotate(
            is_profile_promoted=Case(
                When(
                    premium_products__promotion__valid_until__gt=now, then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField(),
            )
        ).order_by("-is_profile_promoted", "-user__last_activity")

    def get_queryset(self) -> typing.Union[QuerySet, typing.List]:
        """Get queryset based on role, apply filters, and handle shuffle parameter."""
        self.queryset = self.model.objects.to_list_by_api()
        self.filter_queryset(self.queryset)

        if self.query_params.get("shuffle", False):
            # Random shuffle -> get random sample of 10 -> return list of random choices
            shuffled_queryset = self.queryset.order_by("?")
            queryset_length = shuffled_queryset.count()

            if queryset_length >= 10:
                selected_items = random.sample(list(shuffled_queryset), 10)
                return self.queryset.filter(pk__in=[item.pk for item in selected_items])
            else:
                # Handle cases where the queryset has fewer than 10 elements
                return shuffled_queryset

        self.sort_queryset()

        return self.queryset

    def sort_queryset(self) -> None:
        """Sort queryset based on sort parameter"""
        if sort_param := self.query_params.get("sort"):
            if self.request.query_params.get("role") == "P":
                if sort_param == "-pm_score":
                    self.queryset = self.queryset.order_by(
                        F("playermetrics__pm_score").desc(nulls_last=True)
                    )
                elif sort_param == "pm_score":
                    self.queryset = self.queryset.order_by(
                        F("playermetrics__pm_score").asc(nulls_last=True)
                    )
        else:
            self.queryset = self.sort_promoted_first(self.queryset)

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
        self.filter_gender()
        self.filter_players_by_transfer_status()
        self.filter_by_salary()
        self.filter_by_benefits()
        self.filter_by_transfer_status_league()
        self.filter_by_additional_info()
        self.filter_by_number_of_trainings()
        self.filter_by_pm_score()

        self.queryset = self.queryset.order_by("-user__date_joined")

        # position has its own sorting, so it should be the last filter
        self.filter_position()

    def coach_filters(self) -> QuerySet:
        """Filters related with GuestProfile"""
        ...

    def common_filters(self) -> None:
        """Common filters for each type of profile"""
        if not (
            self.query_params.get("youth", False) and self.model is models.PlayerProfile
        ):
            self.filter_age()

        self.not_me_filter()
        self.filter_localization()
        self.filter_country()
        self.filter_language()
        self.filter_licence()
        self.filter_by_labels()
        self.filter_league()
        self.filter_last_activity()
        self.observed()

    def define_query_params(self) -> None:
        """Validate query_params and save as self.query_params"""
        params: dict = {}

        for key, parser in self.PARAMS_PARSERS.items():
            value = (
                self.request.query_params.getlist(key)
                if parser in api_utils.LIST_PARSERS
                else self.request.query_params.get(key)
            )
            if key_in_params := value:  # noqa: E999
                try:
                    params[key] = parser(key, key_in_params)
                except ValueError as e:
                    raise InvalidAPIRequestParam(e)
        self.query_params = params

    def filter_language(self) -> None:
        """Filter queryset by language"""
        if language := self.query_params.get("language"):
            try:
                self.queryset = self.service.filter_language(self.queryset, language)
            except ValueError as e:
                raise api_errors.InvalidLanguageCode(e)

    def not_me_filter(self) -> None:
        """Exclude current user from queryset if not_me param is sent"""
        if self.query_params.get("not_me") and self.request.user.is_authenticated:
            self.queryset = self.queryset.exclude(user=self.request.user)

    def filter_country(self) -> None:
        """Filter queryset by language"""
        if country := self.query_params.get("country"):
            try:
                self.queryset = self.service.filter_country(self.queryset, country)
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
            self.queryset = self.service.filter_localization(
                self.queryset, latitude, longitude, radius
            )

    def filter_league(self) -> None:
        """Filter queryset by player league"""
        if league := self.query_params.get("league"):
            self.queryset = self.service.filter_league(self.queryset, league)

    def filter_gender(self) -> None:
        """Filter queryset by player gender"""
        if gender := self.query_params.get("gender"):
            self.queryset = self.service.filter_player_gender(self.queryset, gender)

    def filter_position(self) -> None:
        """Filter queryset by player position"""
        if position := self.query_params.get("position"):
            self.queryset = self.service.filter_qs_by_player_position_id(
                self.queryset, position
            )

    def filter_youth(self) -> None:
        """Filter queryset by youth players"""
        if self.query_params.get("youth"):
            self.queryset = self.service.filter_youth_players(self.queryset)

    def filter_age(self) -> None:
        """Filter queryset by age"""
        if min_age := self.query_params.get("min_age"):
            self.queryset = self.service.filter_min_age(self.queryset, min_age)

        if max_age := self.query_params.get("max_age"):
            self.queryset = self.service.filter_max_age(self.queryset, max_age)

    def filter_licence(self) -> None:
        """Filter queryset by licence"""
        licence_names: typing.List[str] = self.query_params.get("licence", [])
        if licence_names:
            try:
                services.ProfileFilterService.validate_licence_keys(licence_names)
            except ValueError:
                available_names = models.LicenceType.get_available_licence_names()
                raise api_errors.ChoiceFieldValueErrorHTTPException(
                    field="licence", choices=available_names, model="LicenceType"
                )
            self.queryset = self.queryset.filter(
                user__licences__licence__name__in=licence_names
            ).distinct()

    def filter_by_labels(self) -> None:
        """
        Filters the queryset based on label criteria.

        The method relies on utility functions to validate label names, get specific
        IDs for profile and user-related labels, and apply these filters to the
        queryset.
        """
        if label_names := self.query_params.get("labels"):
            valid_label_names = validate_labels(label_names)
            profile_specific_ids = get_profile_specific_ids(
                self.model, valid_label_names
            )
            user_related_ids = get_user_related_ids(valid_label_names)

            self.queryset = apply_label_filters(
                self.queryset, profile_specific_ids, user_related_ids, self.model
            )

    def filter_players_by_transfer_status(self) -> None:
        """Filter queryset by players transfer status."""
        transfer_statuses = self.query_params.get("transfer_status")
        if transfer_statuses:
            self.queryset = self.service.filter_transfer_status(
                self.queryset, transfer_statuses
            )

    def filter_by_transfer_status_league(self) -> None:
        """
        Filter the queryset by leagues associated with the profile's transfer status.
        """
        if league_ids := self.query_params.get("transfer_status_league"):
            self.queryset = self.service.filter_by_transfer_status_league(
                self.queryset, league_ids
            )

    def filter_by_additional_info(self) -> None:
        """
        Filter the queryset by additional information related to the profile's transfer status.
        """
        if info := self.query_params.get("additional_info"):
            self.queryset = self.service.filter_by_additional_info(self.queryset, info)

    def filter_by_number_of_trainings(self) -> None:
        """
        Filter the queryset by the number of trainings per week as specified in the profile's transfer status.
        """
        if trainings := self.query_params.get("number_of_trainings"):
            self.queryset = self.service.filter_by_number_of_trainings(
                self.queryset, trainings
            )

    def filter_by_benefits(self) -> None:
        """
        Filter the queryset by benefits associated with the profile's transfer status.
        """
        if benefits := self.query_params.get("benefits"):
            self.queryset = self.service.filter_by_benefits(self.queryset, benefits)

    def filter_by_salary(self) -> None:
        """
        Filter the queryset by salary range as indicated in the profile's transfer status.
        """
        if salary := self.query_params.get("salary"):
            self.queryset = self.service.filter_by_salary(self.queryset, salary)

    def filter_by_pm_score(self) -> None:
        """Filter queryset based on the range of PlayMaker Score"""
        min_score = self.query_params.get("min_pm_score")
        max_score = self.query_params.get("max_pm_score")

        if min_score is not None:
            self.queryset = self.service.filter_min_pm_score(self.queryset, min_score)

        if max_score is not None:
            self.queryset = self.service.filter_max_pm_score(self.queryset, max_score)

    def observed(self) -> None:
        """Include only profiles that are observed by the user"""
        if self.query_params.get("observed") and self.request.user.is_authenticated:
            followed_profile_ids = self.service.get_followed_profile_ids(
                self.request.user, self.model
            )
            self.queryset = self.queryset.filter(user__id__in=followed_profile_ids)
