import datetime
import functools
import logging
import re
from urllib.parse import parse_qs, urlparse

import pandas as pd
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import profiles
from profiles import models
from roles import definitions
from stats import adapters
from typing import Optional

# from . import models
# from profiles import forms  # todo teog importu tu nie moze być bo sie robi rekurencja
from users.models import User

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


def calculate_player_metrics():
    from utils import get_current_season

    qs = User.objects.filter(
        declared_role=definitions.PLAYER_SHORT, state=User.STATE_ACCOUNT_VERIFIED
    )
    for user in qs:
        if user.profile.has_data_id:
            season_name = get_current_season()
            _id = int(
                user.profile.mapper.get_entity(
                    related_type="player", database_source="s38"
                ).mapper_id
            )
            games_summary = adapters.PlayerLastGamesAdapter(_id).get(
                season=season_name, limit=3
            )  # should be profile.playermetrics.refresh_games_summary() and putted to celery.
            fantasy_summary = adapters.PlayerFantasyDataAdapter(_id).get(
                season=season_name
            )
            season_summary = adapters.PlayerStatsSeasonAdapter(_id).get(
                season=season_name
            )
            user.profile.playermetrics.update_summaries(
                games_summary, season_summary, fantasy_summary
            )


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


def make_jj_manago():
    from clubs.models import Club

    cs = Club.objects.filter(autocreated=True)
    sysuser = User.get_system_user()
    for i in cs:
        i.manager = sysuser
        i.save()


def create_from_data():
    """Create and attach League,Season,Seniority,Team,Club - based on data_Plater.meta
    operation should be run once
    """

    def seniority_translate(name):
        if name == "seniorskie":
            return "seniorzy"
        elif name == "młodzieżowe":
            return "juniorzy"

    players = User.objects.filter(declared_role=definitions.PLAYER_SHORT)
    print(f"Number of players to update {players.count()}")
    ids = 0
    from league_filter_map import LEAGUE_MAP
    from teams_map import TEAM_MAP

    from clubs.models import Club, Gender, League, Seniority, Team, Voivodeship
    from stats.adapters import PlayerAdapter
    from stats.utilites import LEAGUES_CODES_MAP
    from utils import get_current_season

    print("getting sys user")

    sysuser = User.get_system_user()
    print("loop")
    for player in players:
        try:
            profile = player.profile

        except:
            print("do not have related object", player)
            continue
        if profile.has_data_id:
            # print('get from s38')
            adpt = PlayerAdapter(
                int(
                    profile.mapper.get_entity(
                        related_type="player", database_source="s38"
                    ).mapper_id
                )
            )
            # print('adapt')
            if adpt.player.meta is None:
                print("This player dont have META yet... {adpt.player} ")
                continue
            meta_new = adpt.player.meta.get(get_current_season(), None)
            if meta_new is None:
                print(f"--------------------- {adpt.player}")
                print("\t\tWarning.......... no meta for platyer")
                profile.trigger_refresh_data_player_stats()
                adpt.player.refresh_from_db()
                meta_new = adpt.player.meta.get(get_current_season(), None)
                if meta_new is None:
                    print(
                        f"\t\tno meta for 2020/2021 {adpt.player}  -- taking older season."
                    )
                    meta_new = adpt.player.meta.get("2019/2020", None)
                    if meta_new is None:
                        print(
                            f"\t\tno meta  for 2019/2020 {adpt.player}  -- taking older season."
                        )
                        meta_new = adpt.player.meta.get("2018/2019", None)

                        if meta_new is None:
                            print(
                                f"!!!!!! PlayerProfile {profile} still do not have yet meta for 2018/2019 /{adpt.player} meta: {adpt.player.meta}"
                            )
                            continue

                            # print(f'\t\tPlayer do not have yet meta  for 2018/2019 {adpt.player}  -- taking older season.')
                            # meta_new = adpt.player.meta.get('2017/2018', None)
                            # if meta_new is None:
                else:
                    print(f"FIXED")
            else:
                profile.meta = meta_new
                profile.save()

            lc = meta_new["league_code"]
            tn = meta_new["team"]
            # print(meta_new)
            # print('--------------------------------------------')
            # print('meta=', meta_new)
            # print('ll=', LEAGUE_MAP)
            for m in LEAGUE_MAP:
                if (
                    meta_new["zpn"].lower() + "e" in m["województwo"]
                    and str(lc) == m["league_code"]
                ):
                    x = m
                    # print('xxx=', x)
                    break

            # print('--------------------------------------------')
            # print(TEAM_MAP[tn])
            if TEAM_MAP.get(tn) is None:
                print(
                    f"!!!!!!! Not mapped TEAM {tn} for player Player do not have yet meta {adpt.player}"
                )
                continue
            if TEAM_MAP[tn]["name"]:
                team = TEAM_MAP[tn]["name"]
                club = TEAM_MAP[tn]["club"] or TEAM_MAP[tn]["name"]
            else:
                team = tn
                club = tn
            vivo = meta_new["zpn"].lower() + "e"
            vivo = conver_vivo_for_api(vivo)
            league_name = LEAGUES_CODES_MAP[int(lc)]
            gen = x["plec"]
            sen = seniority_translate(x["seniority"])
            # print('------')
            # print('league=', league_name)
            # print('seniority=', sen)
            # print('vivo=', vivo)
            # print('gen=', gen)
            # print('lc=', lc)
            # print('team=', team)
            # print('club=', club)
            try:
                leagueo, _ = League.objects.update_or_create(
                    name=league_name.title(), defaults={"code": str(lc)}
                )
            except Exception as e:
                print(e)
                print("lc=", str(lc), meta_new)

            if vivo is not None:
                vivoo, _ = Voivodeship.objects.update_or_create(name=vivo.lower())
            else:
                vivoo = None

            cqs = Club.objects.filter(name__icontains=club)
            # print(f'club is present: cqs {cqs.count()}')
            if cqs.count() > 0:
                clubo = cqs.first()
                createdc = False
            elif cqs.count() == 0:
                clubo, createdc = Club.objects.update_or_create(
                    name=club, defaults={"manager": sysuser, "voivodeship": vivoo}
                )

            if createdc:
                # print('Club created..')
                clubo.autocreated = True
                clubo.save()
            # teams

            seno, _ = Seniority.objects.update_or_create(name=sen)
            geno, _ = Gender.objects.update_or_create(name=gen)

            tqs = Team.objects.filter(name__icontains=Team)
            if tqs.count() > 0:
                teamo = tqs.first()
                createdt = False
            elif tqs.count() == 0:
                teamo, createdt = Team.objects.update_or_create(
                    name=team,
                    league=leagueo,
                    seniority=seno,
                    club=clubo,
                    defaults={"gender": geno},
                )
            if createdt:
                # print('Team created..')
                teamo.visible = False
                teamo.autocreated = True
                teamo.save()
            profile.team_object = teamo
            profile.save()

            ids += 1

    print(ids)


def match_player_videos(csv_file: str) -> None:
    """
    Matches player videos with data from csv_file.
    Expects the csv_file to have the following columns:
            player - the user id,
            url - the URL of the video,
            title - the title of the video,
            description - the description of the video.
    """
    player_profiles = profiles.models.PlayerProfile.objects.all()
    df = pd.read_csv(csv_file)

    for index, row in df.iterrows():
        player_profile = player_profiles.get(user=row["player"])

        vids = profiles.models.PlayerVideo.objects.filter(
            player=player_profile, url=row["url"]
        )

        if not vids:
            profiles.models.PlayerVideo.objects.create(
                player=player_profile,
                url=row["url"],
                title=row["title"] if not pd.isna(row["title"]) else "",
                description=row["description"]
                if not pd.isna(row["description"])
                else "",
            )
            print(f"{player_profile.user} video with url {row['url']} created")
        else:
            print(f"{player_profile.user} video with url {row['url']} already exists")


def get_metrics_update_date(metrics: "models.PlayerMetrics") -> str:
    """
    Returns the date when player metrics were last updated.
    If the metrics were updated after 15 February 2023, returns the date portion of the
    newest update_date argument. Otherwise, returns 1 August 2022.
    Parameters:
    metrics (dict): A dictionary containing the different metrics update dates.
    Returns:
    datetime.date: The date when player metrics were last updated.
    """
    # Check which update_date is the newest
    dates = list(
        filter(
            lambda date: date is not None,
            [
                metrics.games_updated,
                metrics.games_summary_updated,
                metrics.season_updated,
                metrics.season_summary_updated,
            ],
        )
    )

    if dates:
        newest_update_date = max(dates)
        threshold_date = datetime.datetime(
            2023, 2, 15, tzinfo=newest_update_date.tzinfo
        )
        # Check if the metrics were updated after the threshold date
        if newest_update_date and newest_update_date > threshold_date:
            return newest_update_date.date().strftime("%d-%m-%Y")
        else:
            # If the metrics were not updated after the threshold date, return an older date
            return datetime.date(2022, 8, 1).strftime("%d-%m-%Y")


def calculate_age(birth_date: Optional[datetime.date]) -> Optional[int]:
    """
    Calculate the age based on the given birth date.
    """
    if birth_date:
        now = timezone.now()
        return (
            now.year
            - birth_date.year
            - ((now.month, now.day) < (birth_date.month, birth_date.day))
        )
    else:
        return None
