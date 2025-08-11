import datetime
import functools
import logging
import re
import typing
from urllib.parse import parse_qs, urlparse

from dateutil.relativedelta import relativedelta
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode

# from stats import adapters DEPRECATED: PM-1015

logger = logging.getLogger(__name__)


def extract_video_id(url):
    # Examples:
    # - http://youtu.be/SA2iWivDJiE
    # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    # - http://www.youtube.com/embed/SA2iWivDJiE
    # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    # https://m.youtube.com/watch?v=WdnTytj75bc'
    query = urlparse(url)
    if query.hostname == "youtu.be":
        return query.path[1:]
    if query.hostname in {"www.youtube.com", "youtube.com", "m.youtube.com"}:
        if query.path == "/watch":
            return parse_qs(query.query)["v"][0]
        if query.path[:7] == "/embed/":
            return query.path.split("/")[2]
        if query.path[:3] == "/v/":
            return query.path.split("/")[2]
    # fail?
    return None


def supress_exception(func):
    """A function wrapper for catching all exceptions and logging them"""

    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            # TODO(rkesik): mute that error cause if making a lot of noice in logs.
            # logger.error(f'Following exception was supressed: {func} {ex}')
            return None

    return inner


def conver_vivo_for_api(zpn):
    if zpn is None:
        return None
    if "/" in zpn:
        return None
    else:
        return zpn


def calculate_age_from_date(date):
    if date:
        now = timezone.now()
        return now.year - date.year - ((now.month, now.day) < (date.month, date.day))
    return None


def get_datetime_from_age(age):
    if age is not None:
        now = timezone.now()
        return timezone.datetime(now.year - age, 1, 1)
    return None


def get_datetime_from_year(year):
    if not year:
        return None
    return timezone.datetime(year, 1, 1)


# DEPRECATED: PM-1015
# def calculate_player_metrics():
#     from utils import get_current_season
#
#     qs = User.objects.filter(
#         declared_role=definitions.PLAYER_SHORT, state=User.STATE_ACCOUNT_VERIFIED
#     )
#     for user in qs:
#         if user.profile.has_data_id:
#             season_name = get_current_season()
#             _id = int(
#                 user.profile.mapper.get_entity(
#                     related_type="player", database_source="s38"
#                 ).mapper_id
#             )
#             games_summary = adapters.PlayerLastGamesAdapter(_id).get(
#                 season=season_name, limit=3
#             )  # should be profile.playermetrics.refresh_games_summary() and putted to celery.
#             fantasy_summary = adapters.PlayerFantasyDataAdapter(_id).get(
#                 season=season_name
#             )
#             season_summary = adapters.PlayerStatsSeasonAdapter(_id).get(
#                 season=season_name
#             )
#             user.profile.playermetrics.update_summaries(
#                 games_summary, season_summary, fantasy_summary
#             )


# @(rkesik): that can be moved to /app/utils.py
def unique_slugify(
    instance, value, slug_field_name="slug", queryset=None, slug_separator="-"
):
    """
    Calculates and stores a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    ``queryset`` usually doesn't need to be explicitly provided - it'll default
    to using the ``.all()`` queryset from the model's default manager.
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug, limiting its length if necessary.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    # Create the queryset if one wasn't explicitly provided and exclude the
    # current instance from the queryset.
    if queryset is None:
        queryset = instance.__class__._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    # Find a unique slug. If one matches, at '-2' to the end and try again
    # (then '-3', etc).
    next = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = "%s%s" % (slug_separator, next)
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[: slug_len - len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = "%s%s" % (slug, end)
        next += 1

    setattr(instance, slug_field.attname, slug)


def _slug_strip(value, separator="-"):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    separator = separator or ""
    if separator == "-" or not separator:
        re_sep = "-"
    else:
        re_sep = "(?:-|%s)" % re.escape(separator)
    # Remove multiple instances and if an alternate separator is provided,
    # replace the default '-' separator.
    if separator != re_sep:
        value = re.sub("%s+" % re_sep, separator, value)
    # Remove separator from the beginning and end of the slug.
    if separator:
        if separator != "-":
            re_sep = re.escape(separator)
        value = re.sub(r"^%s+|%s+$" % (re_sep, re_sep), "", value)
    return value


def make_choices(choices):
    """
    Returns tuples of localized choices based on the dict choices parameter.
    Uses lazy translation for choices names.
    """
    return tuple([(k, _(v)) for k, v in choices])


PARAMETERS_MAPPING = {
    "game__host_team_name": "host_name",
    "host_team_name": "host_name",
    "game__guest_team_name": "guest_name",
    "guest_team_name": "guest_name",
    "minutes_played": "minutes",
    "host_score": "host_score",
    "guest_score": "guest_score",
    "game__host_score": "host_score",
    "game__guest_score": "guest_score",
    "team_goals": "team_goals",
    "goals": "goals",
    "yellow_cards": "yellow_cards",
    "red_cards": "red_cards",
    "date": "date",
    "league_name": "league_name",
}


def list_item_adapter(items: list) -> list:
    outcome = []
    for item in items:
        outcome.append(
            dict((PARAMETERS_MAPPING[key], value) for (key, value) in item.items())
        )
    return outcome


def item_adapter(item: dict) -> dict:
    return dict((PARAMETERS_MAPPING[key], value) for (key, value) in item.items())


def get_past_date(days: int = 0, months: int = 0, years: int = 0) -> datetime.datetime:
    """Get past date based on days/months/years from current date"""
    return datetime.datetime.now() - relativedelta(
        days=days, months=months, years=years
    )


def map_service_exception(exception) -> typing.Optional[typing.Type[Exception]]:
    """
    Maps a service layer exception to its corresponding API exception.

    This function attempts to find a matching API exception for a given
    service exception. If a match is found, the API exception is returned,
    otherwise, None is returned.
    """
    # avoid recursive import
    from clubs import errors as club_errors
    from profiles import errors as profile_errors
    from profiles.api import errors as profile_api_errors

    exception_mapping: typing.Dict[typing.Type[Exception], typing.Type[Exception]] = {
        club_errors.LeagueNotFoundServiceException: club_errors.LeagueDoesNotExist,
        club_errors.LeagueHistoryNotFoundServiceException: club_errors.LeagueHistoryDoesNotExist,
        club_errors.TeamNotFoundServiceException: club_errors.TeamDoesNotExist,
        profile_errors.TeamContributorAlreadyExistServiceException: profile_api_errors.TeamContributorExist,
        profile_errors.TeamContributorNotFoundServiceException: profile_api_errors.TeamContributorDoesNotExist,
        club_errors.TeamHistoryNotFoundServiceException: club_errors.TeamHistoryDoesNotExist,
        club_errors.SeasonDoesNotExistServiceException: club_errors.SeasonDoesNotExist,
        club_errors.SeasonDateRangeTooWideServiceException: club_errors.SeasonDateRangeTooWide,
    }

    return exception_mapping.get(type(exception), None)


def preprocess_search_term(term: str) -> str:
    """
    Preprocess the given search term by converting non-ASCII characters
    to their closest ASCII equivalents, removing spaces, and converting to lowercase.
    """
    # Convert non-ASCII characters to their closest ASCII equivalents
    term = unidecode(term)
    # Remove spaces
    term = term.replace(" ", "")
    # Convert to lowercase
    term = term.lower()
    return term


# Mapping of English profile types to their Polish equivalents
profile_type_english_to_polish = {
    "player": "pilkarz",
    "coach": "trener",
    "club": "dzialacz-klubowy",
    "scout": "skaut",
    "guest": "kibic",
    "manager": "menadzer",
}
