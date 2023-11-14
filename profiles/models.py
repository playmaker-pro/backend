import logging
import typing
import uuid
from collections import Counter
from datetime import datetime

from address.models import AddressField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.core import validators
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

import utils as utilites
from adapters import strategy
from adapters.base_adapter import API_METHOD, ScrapperAPI
from adapters.player_adapter import (
    PlayerGamesAdapter,
    PlayerScoreAdapter,
    PlayerSeasonStatsAdapter,
)
from external_links.models import ExternalLinks
from external_links.utils import create_or_update_profile_external_links
from mapper.models import Mapper
from profiles.errors import VerificationCompletionFieldsWrongSetup
from profiles.mixins import TeamObjectsDisplayMixin
from profiles.mixins import utils as profile_utils
from roles import definitions
from voivodeships.models import Voivodeships

User = get_user_model()


logger = logging.getLogger(__name__)


GLOBAL_TRAINING_READY_CHOCIES = (
    (1, "1-2 treningi"),
    (2, "3-4 treningi"),
    (3, "5-6 treningi"),
)

FORMATION_CHOICES = (
    ("5-3-2", "5-3-2"),
    ("5-4-1", "5-4-1"),
    ("4-4-2", "4-4-2"),
    ("4-5-1", "4-5-1"),
    ("4-3-3", "4-3-3"),
    ("4-2-3-1", "4-2-3-1"),
    ("4-1-4-1", "4-1-4-1"),
    ("4-3-2-1", "4-3-2-1"),
    ("3-5-2", "3-5-2"),
    ("3-4-3", "3-4-3"),
    ("4-3-1-2", "4-3-1-2"),
    ("4-4-1-1", "4-4-1-1"),
)


class ProfileVideo(models.Model):
    """Model to keep track on user videos"""

    class PlayerLabels(models.TextChoices):
        """Labels specific for PlayerProfile"""

        SHORT = "player_short", "Skrót meczu"
        FULL = "player_full", "Cały mecz"
        GOAL = "player_goal", "Bramka"

    class CoachLabels(models.TextChoices):
        """Labels specific for CoachProfile"""

        SHORT = "coach_short", "Skrót meczu"
        FULL = "coach_full", "Cały mecz"
        ANALYSIS = "coach_analysis", "Analiza"

    class ClubLabels(models.TextChoices):
        """Labels specific for ClubProfile"""

        SHORT = "club_short", "Skrót meczu"
        FULL = "club_full", "Cały mecz"
        ANALYSIS = "club_analysis", "Analiza"

    class ScoutLabels(models.TextChoices):
        """Labels specific for ScoutProfile"""

        PLAYER = "scout_player_analysis", "Piłkarz"
        TACTICS = "scout_tactics", "Taktyka"
        FRAGMENT = "scout_fragment", "Stałe fragmenty"

    LABELS = (
        *PlayerLabels.choices,
        *CoachLabels.choices,
        *ScoutLabels.choices,
        *ClubLabels.choices,
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_video")
    url = models.URLField(
        _("Youtube url"),
    )
    title = models.CharField(_("Tytuł nagrania"), max_length=235, blank=True, null=True)
    description = models.TextField(_("Opis"), null=True, blank=True)
    label = models.CharField(choices=LABELS, null=True, blank=True, max_length=30)
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = "Profile Video"
        verbose_name_plural = "Profile Videos"

    @property
    def get_youtube_thumbnail_url(self) -> typing.Union[str, None]:
        """Crop YouTube video id from url, then return thumbnail url"""
        from urllib.parse import parse_qsl, urlparse

        thumbnail_url: str = "https://i.ytimg.com/vi/{}/hqdefault.jpg"
        url = str(self.url)
        parser = urlparse(url)

        if parser.netloc.endswith("youtu.be") or parser.netloc.endswith("youtube.com"):
            query_params = dict(parse_qsl(parser.query))
            if video_id := query_params.get(  # noqa: E999
                "v", parser.path.split("/")[-1]
            ):
                return thumbnail_url.format(video_id)


class Course(models.Model):
    name = models.CharField(max_length=100)
    release_year = models.IntegerField(blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses"
    )

    def __str__(self) -> str:
        return f"{self.owner} - {self.name} ({self.release_year})"


class RoleChangeRequest(models.Model):
    """Keeps track on requested changes made by users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="changerolerequestor",
        help_text="User who requested change",
    )

    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        help_text="Admin who verified.",
    )

    approved = models.BooleanField(
        default=False, help_text="Defines if admin approved change"
    )

    request_date = models.DateTimeField(auto_now_add=True)

    accepted_date = models.DateTimeField(auto_now=True)

    new = models.CharField(max_length=100, choices=definitions.ACCOUNT_ROLES)

    class Meta:
        unique_together = ("user", "request_date")

    def approve(self):
        self.approved = True
        self.save()

    @property
    def current(self):
        return self.user.get_declared_role_display()

    @property
    def current_pretty(self):
        return self.user.get_declared_role_display()

    @property
    def new_pretty(self):
        return self.get_new_display()

    def __str__(self):
        return (
            f"{self.user}'s request to change profile from {self.current} to {self.new}"
        )

    def save(self, *args, **kwargs):
        if self.approved:
            self.accepted_date = datetime.now()
        super().save(*args, **kwargs)

    def get_admin_url(self):
        return reverse(
            f"admin:{self._meta.app_label}_{self._meta.model_name}_change",
            args=(self.id,),
        )


class ProfileVisitHistory(models.Model):
    counter = models.PositiveIntegerField(default=0)
    counter_coach = models.PositiveIntegerField(default=0)
    counter_scout = models.PositiveIntegerField(default=0)

    def increment(self, commit=True):
        self.counter += 1
        if commit:
            self.save()

    def increment_coach(self, commit=True):
        self.counter_coach += 1
        if commit:
            self.save()

    def increment_scout(self, commit=True):
        self.counter_scout += 1
        if commit:
            self.save()


class EventLogMixin:
    EVENT_LOG_HISTORY = 35

    def make_default_event_log(self):
        self.event_log = list()

    def add_event_log_message(self, msg: str, type: str = "nor", commit: bool = True):
        """Adds event log into list
        if more than event_log_history it will be removed
        types = ['nor', 'err', 'deb']
        """
        if type == "err":
            suffix = "ERROR:"
        elif type == "dev":
            suffix = "DEBUG:"
        else:
            suffix = ""
        if self.event_log is None or isinstance(self.event_log, dict):
            self.make_default_event_log()

        if len(self.event_log) > self.EVENT_LOG_HISTORY:
            try:
                self.event_log.pop()
            except Exception as e:
                logger.error(
                    f"Cannot remove eventlog message form user profile. reason={e}"
                )
        date = timezone.now()
        msg = {"date": f"{date}", "message": f"{suffix}{msg}"}
        self.event_log.insert(0, msg)
        if commit:
            self.save()


class BaseProfile(models.Model, EventLogMixin):
    """Base profile model to held most common profile elements"""

    _video_labels = models.TextChoices  # override in subclasses

    PROFILE_TYPE = None
    AUTO_VERIFY = False  # flag to perform auto verification of User based on profile. If true - User.state will be switched to Verified  # noqa: E501
    VERIFICATION_FIELDS = (
        []
    )  # this is definition of profile fields which will be threaded as must-have params.  # noqa: E501
    COMPLETE_FIELDS = (
        []
    )  # this is definition of profile fields which will be threaded as mandatory for full profile.  # noqa: E501
    OPTIONAL_FIELDS = (
        []
    )  # this is definition of profile fields which will be threaded optional

    data_mapper_changed = None
    verification = models.OneToOneField(
        "ProfileVerificationStatus", on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )
    history = models.OneToOneField(
        ProfileVisitHistory, on_delete=models.CASCADE, null=True, blank=True
    )
    data_mapper_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of object placed in data_ database. It should alwayes reflect scheme which represents.",  # noqa: E501
    )
    slug = models.CharField(max_length=255, blank=True, editable=False)
    bio = models.CharField(
        _("Krótki opis o sobie"), max_length=455, blank=True, null=True
    )
    event_log = models.JSONField(null=True, blank=True)
    verification_stage = models.OneToOneField(
        "VerificationStage", on_delete=models.SET_NULL, null=True, blank=True
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    labels = GenericRelation("labels.Label")

    def get_absolute_url(self):
        return self.get_permalink()

    def get_permalink(self):
        return reverse("profiles:show", kwargs={"slug": self.slug})

    def generate_uuid(self, force: bool = False) -> None:
        """
        Set/overwrite new uuid for object
        May cause data incoherence, make sure you want to use it
        """
        if force:
            self.uuid = uuid.uuid4()
            super().save()

    def get_team(self):
        if self.PROFILE_TYPE in [
            definitions.PROFILE_TYPE_COACH,
            definitions.PROFILE_TYPE_PLAYER,
        ]:
            if self.team_object is not None:
                return self.team_object
            else:
                return None
        # @todo: here player profile need to be added.
        else:
            return None

    def get_league_object(self):
        """Gets league object based on self.team_object if present"""
        team = self.get_team()
        if team and team.league:
            return team.league
        return None

    def get_club_object(self):
        if self.PROFILE_TYPE in [
            definitions.PROFILE_TYPE_CLUB,
            definitions.PROFILE_TYPE_COACH,
            definitions.PROFILE_TYPE_PLAYER,
        ]:
            if self.PROFILE_TYPE == definitions.PROFILE_TYPE_CLUB:
                return self.club_object
            elif (
                self.PROFILE_TYPE == definitions.PROFILE_TYPE_COACH
                or definitions.PROFILE_TYPE_PLAYER
            ):
                if self.team_object is None:
                    return None
                else:
                    return self.team_object.club
        # @todo: here player profile need to be added.
        else:
            return None

    @property
    def has_attachemnt(self):
        return False

    @property
    def is_active(self):
        return (
            definitions.PROFILE_TYPE_SHORT_MAP.get(self.PROFILE_TYPE)
            == self.user.declared_role
        )

    @property
    def is_complete(self):
        for field_name in self.COMPLETE_FIELDS + self.VERIFICATION_FIELDS:
            if getattr(self, field_name) is None:
                return False
        return True

    @property
    def has_data_id(self) -> typing.Optional[bool]:
        """By default we retrun False if not implemented"""
        if self.PROFILE_TYPE in [
            definitions.PROFILE_TYPE_COACH,
            definitions.PROFILE_TYPE_PLAYER,
        ]:
            if self.mapper is not None:
                mapper_entity = self.mapper.get_entity(
                    related_type__in=["player", "coach"], database_source="s38"
                )
                if mapper_entity is not None:
                    return mapper_entity.mapper_id is not None
            return False

    @property
    def is_not_complete(self):
        return not self.is_complete

    @property
    def percentage_completion(self):
        total = len(self.COMPLETE_FIELDS + self.VERIFICATION_FIELDS)
        if total == 0:
            return int(100)
        field_values = [
            getattr(self, field_name)
            for field_name in self.COMPLETE_FIELDS + self.VERIFICATION_FIELDS
        ]
        part = total - Counter(field_values).get(None, 0)
        completion_percentage = 100 * float(part) / float(total)
        return int(completion_percentage)

    @property
    def percentage_left_verified(self):
        total = len(self.COMPLETE_FIELDS + self.VERIFICATION_FIELDS)
        total_fields_to_verify = len(self.VERIFICATION_FIELDS)
        if total_fields_to_verify == 0:
            return int(0)
        field_values = [
            getattr(self, field_name) for field_name in self.VERIFICATION_FIELDS
        ]
        to_verify_count = len(list(filter(None, field_values)))

        left_fields_counter = total_fields_to_verify - to_verify_count
        try:
            left_verify_percentage = 100 * float(left_fields_counter) / float(total)
        except ZeroDivisionError:
            raise VerificationCompletionFieldsWrongSetup(
                "Wrongly setuped COMPLETE_FIELDS and VERIFICATION_FIELDS"
            )
        # print('a', field_values, to_verify_count, left_verify_percentage)
        return int(left_verify_percentage)

    def _get_verification_object_verification_fields(self, obj=None):
        object_exists = False
        try:
            obj = obj or type(self).objects.get(pk=self.pk) if self.pk else None
            if obj:
                fields_values = self._get_verification_field_values(obj)
                object_exists = True
            else:
                fields_values = None
        except type(self).DoesNotExist:
            # it means first creation of object.
            fields_values = None
        return fields_values, object_exists

    def _save_make_profile_history(self):
        if self.history is None:
            self.history = ProfileVisitHistory.objects.create()

    def ensure_verification_stage_exist(self, commit: bool = True) -> None:
        """Create VerificationStage for profile if it doesn't exist"""
        if not self.verification_stage:
            self.verification_stage = VerificationStage.objects.create()
            if commit:
                self.save()

    @classmethod
    def get_profile_video_labels(cls) -> list:
        """Returns list of video labels for profile"""
        return cls._video_labels.choices

    def save(self, *args, **kwargs):
        # silent_param = kwargs.get('silent', False)
        # if silent_param is not None:
        #     kwargs.pop('silent')
        # if self.event_log is None:
        #     self.make_default_event_log()

        if self._state.adding:
            self.user.declared_role = definitions.PROFILE_TYPE_SHORT_MAP[
                self.PROFILE_TYPE
            ]
            self.user.save(update_fields=["declared_role"])

        self.ensure_verification_stage_exist(commit=False)
        self._save_make_profile_history()
        try:
            obj_before_save = obj = (
                type(self).objects.get(pk=self.pk) if self.pk else None
            )
        except type(self).DoesNotExist:
            obj_before_save = None

        slug_str = "%s %s %s" % (
            self.PROFILE_TYPE,
            self.user.first_name,
            self.user.last_name,
        )
        profile_utils.unique_slugify(self, slug_str)

        ver_old, object_exists = self._get_verification_object_verification_fields(
            obj=obj_before_save
        )
        if obj_before_save is not None:
            before_datamapper = obj.data_mapper_id
        else:
            before_datamapper = None

        # If there is no verification object set we need to create initial for that
        if self.verification is None and self.user.is_need_verfication_role:
            self.verification = ProfileVerificationStatus.create_initial(self.user)

        # Queen of the show
        super().save(*args, **kwargs)

        if self.data_mapper_id != before_datamapper:
            self.data_mapper_changed = True
        else:
            self.data_mapper_changed = False

        # we are updating existing model (not first occurence)
        # rkesik: due to new registration flow that is not needed.
        # ver_new = self._get_verification_field_values(self)
        # if not object_exists:
        #     ver_old = ver_new

        # rkesik: due to new registration flow that is not needed.
        # Cases when one of verification fields is None
        # if self._is_verification_fields_filled():
        #     if not self.user.is_waiting_for_verification and not self.user.is_verified:  # noqa: E501
        #         reason_text = 'Parametry weryfikacyjne są uzupełnione,
        #         a użytkownik nie miał wcześniej statusu "zwerfikowany"
        #         ani że "czeka na weryfikacje"'
        #         reason = f'[verification-params-ready]: \n {reason_text} \n\n
        #         params:{self.VERIFICATION_FIELDS})
        #         \n Old:{ver_old} -> New:{ver_new} \n'
        #         self.user.waiting_for_verification(extra={'reason': reason})
        #         self.user.save()
        #     else:
        #         if self._verification_fileds_has_changed_and_was_filled(ver_old, ver_new):  # noqa: E501
        #             reason_text = 'Parametry weryfikacyjne zostały zmienione
        #             i są wszyskie pola uzupełnione.'
        #             reason = f'[verification-params-changed] \n {reason_text}
        #             \n\n params:{self.VERIFICATION_FIELDS})
        #             \n Old:{ver_old} -> New:{ver_new} \n'
        #             self.user.unverify(extra={'reason': reason})
        #             self.user.save()
        # else:
        #     if not self.user.is_missing_verification_data:
        #         self.user.missing_verification_data()  # -> change state to missing ver data  # noqa: E501
        #         self.user.save()

    # rkesik: due to new registration flow that is not needed.
    # def _is_verification_fields_filled(self):
    #     return all(self._get_verification_field_values(self))

    # def _verification_fileds_has_changed_and_was_filled(self, old, new):
    #     return old != new and all(old) and all(new)

    def get_verification_data_from_profile(self, owner: User = None) -> dict:
        """Based on user porfile get default verification-status data."""
        owner = owner or self.user
        team = None
        has_team = None
        team_not_found = None
        club = None
        text = None

        if owner.is_coach or owner.is_player:
            team = owner.profile.get_team_object_or_none()
            if team is None:
                has_team = False
                text = owner.declared_club if owner.declared_club else None
            else:
                has_team = True
            team_not_found = False

        elif owner.is_club:
            team_not_found = False
            club = owner.profile.get_club_object_or_none()
            if club is None:
                has_team = False
                text = owner.declared_club if owner.declared_club else None
            else:
                has_team = True
            text = None
        else:
            return None

        return {
            "status": owner.state,
            "set_by": User.get_system_user(),
            "owner": owner,
            "text": text,
            "has_team": has_team,
            "team_not_found": team_not_found,
            "club": club,
            "team": team,
        }

    def _get_verification_field_values(self, obj):
        return [getattr(obj, field) for field in self.VERIFICATION_FIELDS]

    def __str__(self):
        return f"{self.user}'s {self.PROFILE_TYPE} profile"

    class Meta:
        abstract = True
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"


class TrainerContact(models.Model):
    # @todo to be connected
    first_name = models.CharField(_("Imię"), max_length=255)
    last_name = models.CharField(_("Nazwisko"), max_length=255)
    season = models.CharField(_("Sezon"), max_length=255, null=True, blank=True)
    email = models.CharField(_("adres e-mail"), max_length=255, null=True, blank=True)
    phone = models.CharField(_("Telefon"), max_length=15, blank=True, null=True)


class PlayerPosition(models.Model):
    name = models.CharField(max_length=255)
    score_position = models.CharField(max_length=255, blank=True, null=True)
    shortcut = models.CharField(max_length=4, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.shortcut}"


class PlayerProfile(BaseProfile, TeamObjectsDisplayMixin):
    """Player specific profile"""

    _video_labels = ProfileVideo.PlayerLabels
    PROFILE_TYPE = definitions.PROFILE_TYPE_PLAYER
    VERIFICATION_FIELDS = [
        "country",
        "birth_date",
    ]
    # @(rkesik): since PM-87 we always verify player
    #    'team_club_league_voivodeship_ver',
    # ]
    #     'team_object'
    # ]

    COMPLETE_FIELDS = [
        "height",
        "weight",
        "formation",
        "prefered_leg",
        "transfer_status",
        "card",
        "soccer_goal",
        "phone",
        "address",
        "practice_distance",
        "about",
        "training_ready",
        "league",
        # 'club',  # @todo this is kicked-off waiting for club mapping implementation
        "team",
        "position_raw",
        "voivodeship_obj",
    ]

    OPTIONAL_FIELDS = [
        "position_raw_alt",
        "formation_alt",
        "facebook_url",
        "laczynaspilka_url",
        "min90_url",
        "transfermarket_url",
        "agent_status",
        "agent_name",
        "agent_phone",
        "agent_foreign",
    ]

    POSITION_CHOICES = [
        (1, "Bramkarz"),
        (2, "Obrońca Lewy"),
        (3, "Obrońca Prawy"),
        (4, "Obrońca Środkowy"),
        (5, "Pomocnik defensywny (6)"),
        (6, "Pomocnik środkowy (8)"),
        (7, "Pomocnik ofensywny (10)"),
        (8, "Skrzydłowy"),
        (9, "Napastnik"),
    ]

    FANTASY_GOAL_KEEPER = "bramkarz"
    FANTASY_DEFENDER = "obronca"
    FANTASY_HELPER = "pomocnik"
    FANTASY_ATTAKER = "napastnik"

    FANTASY_MAPPING = {
        1: FANTASY_GOAL_KEEPER,
        2: FANTASY_DEFENDER,
        3: FANTASY_DEFENDER,
        4: FANTASY_DEFENDER,
        5: FANTASY_HELPER,
        6: FANTASY_HELPER,
        7: FANTASY_HELPER,
        8: FANTASY_HELPER,
        9: FANTASY_ATTAKER,
    }

    LEG_CHOICES = (
        (1, "Lewa"),
        (2, "Prawa"),
    )

    TRANSFER_STATUS_CHOICES = (
        (1, "Szukam klubu"),
        (2, "Rozważę wszelkie oferty"),
        (3, "Nie szukam klubu"),
    )

    CARD_CHOICES = (
        (1, "Mam kartę na ręku"),
        (2, "Nie wiem czy mam kartę na ręku"),
        (3, "Nie mam karty na ręku"),
    )

    GOAL_CHOICES = (
        (1, "Poziom profesjonalny"),
        (2, "Poziom półprofesjonalny"),
        (3, "Poziom regionalny"),
    )

    AGENT_STATUS_CHOICES = (
        (1, "Mam agenta"),
        (2, "Szukam agenta"),
        (3, "Nie szukam agenta"),
    )

    TRAINING_READY_CHOCIES = GLOBAL_TRAINING_READY_CHOCIES

    @property
    def has_attachemnt(self):
        if self.team_object is not None:
            return True
        return False

    @property
    def is_goalkeeper(self):
        if self.position_raw is not None:
            return self.position_raw == 1
        return None

    @property
    def age(self) -> typing.Optional[int]:
        return self.user.userpreferences.age

    @property
    def has_videos(self):
        return ProfileVideo.objects.filter(player=self).count() > 0

    @property
    def attached(self):
        """proxy method to pass if profile has id"""
        return self.has_data_id()

    @property
    def get_team_object(self):
        """to support alternative seletion of team"""
        if self.team_object_alt is not None:
            return self.team_object_alt
        return self.team_object

    meta = models.JSONField(null=True, blank=True)
    meta_updated = models.DateTimeField(null=True, blank=True)
    team_club_league_voivodeship_ver = models.CharField(
        _("team_club_league_voivodeship_ver"),
        max_length=355,
        help_text=_("Drużyna, klub, rozgrywki, województwo."),
        blank=True,
        null=True,
    )
    team_object = models.ForeignKey(
        "clubs.Team",
        on_delete=models.SET_NULL,
        related_name="players",
        null=True,
        blank=True,
    )
    team_history_object = models.ForeignKey(
        "clubs.TeamHistory",
        on_delete=models.SET_NULL,
        related_name="players",
        null=True,
        blank=True,
    )
    team_object_alt = models.ForeignKey(
        "clubs.Team",
        on_delete=models.SET_NULL,
        related_name="players_alt",
        null=True,
        blank=True,
    )
    club = models.CharField(
        _("Klub"),
        max_length=68,
        db_index=True,
        help_text=_("Klub w którym obecnie reprezentuejsz"),
        blank=True,
        null=True,
    )

    team = models.CharField(
        _("Drużyna"),
        db_index=True,
        max_length=68,
        help_text=_("Drużyna w której obecnie grasz"),
        blank=True,
        null=True,
    )

    league = models.CharField(
        _("Rozgrywki"),
        max_length=68,
        db_index=True,
        help_text=_("Poziom rozgrywkowy"),
        blank=True,
        null=True,
    )

    # DEPRECATED: Migrated to UserPreferences PM20-148
    birth_date = models.DateField(_("Data urodzenia"), blank=True, null=True)
    height = models.PositiveIntegerField(
        _("Wzrost"),
        help_text=_("Wysokość (cm) [130-210cm]"),
        blank=True,
        null=True,
        validators=[
            validators.MinValueValidator(130),
            validators.MaxValueValidator(210),
        ],
    )
    weight = models.PositiveIntegerField(
        _("Waga"),
        help_text=_("Waga(kg) [40-140kg]"),
        blank=True,
        null=True,
        validators=[
            validators.MinValueValidator(40),
            validators.MaxValueValidator(140),
        ],
    )
    position_raw = models.IntegerField(
        _("Pozycja"),
        db_index=True,
        choices=profile_utils.make_choices(POSITION_CHOICES),
        blank=True,
        null=True,
    )
    position_raw_alt = models.IntegerField(
        _("Pozycja alternatywna"),
        choices=profile_utils.make_choices(POSITION_CHOICES),
        blank=True,
        null=True,
    )
    position_fantasy = models.CharField(
        _("Pozycja Fantasy"), max_length=35, blank=True, null=True
    )
    formation = models.CharField(
        _("Formacja"),
        choices=profile_utils.make_choices(FORMATION_CHOICES),
        max_length=15,
        null=True,
        blank=True,
    )
    formation_alt = models.CharField(
        _("Alternatywna formacja"),
        choices=profile_utils.make_choices(FORMATION_CHOICES),
        max_length=15,
        null=True,
        blank=True,
    )
    prefered_leg = models.IntegerField(
        _("Noga"),
        choices=profile_utils.make_choices(LEG_CHOICES),
        null=True,
        blank=True,
    )
    transfer_status = models.IntegerField(
        _("Status transferowy"),
        choices=profile_utils.make_choices(TRANSFER_STATUS_CHOICES),
        null=True,
        blank=True,
    )
    card = models.IntegerField(
        _("Karta na ręku"),
        choices=profile_utils.make_choices(CARD_CHOICES),
        null=True,
        blank=True,
    )
    soccer_goal = models.IntegerField(
        _("Piłkarski cel"),
        choices=profile_utils.make_choices(GOAL_CHOICES),
        null=True,
        blank=True,
    )
    phone = models.CharField(_("Telefon"), max_length=15, blank=True, null=True)
    facebook_url = models.URLField(_("Facebook"), max_length=500, blank=True, null=True)

    mapper = models.OneToOneField(
        Mapper, on_delete=models.SET_NULL, blank=True, null=True
    )
    external_links = models.OneToOneField(
        ExternalLinks, on_delete=models.SET_NULL, blank=True, null=True
    )
    # laczynaspilka_url, min90_url, transfermarket_url data will be migrated
    # into PlayerMapper and then those fields will be deleted
    laczynaspilka_url = models.URLField(_("LNP"), max_length=500, blank=True, null=True)
    min90_url = models.URLField(
        _("90min portal"), max_length=500, blank=True, null=True
    )
    transfermarket_url = models.URLField(_("TrasferMarket"), blank=True, null=True)

    # TODO Based on task PM-363. After migration on production, field can be deleted
    voivodeship = models.CharField(
        _("Województwo zamieszkania"),
        help_text="Wybierz województwo. Stare pole przygotowane do migracji.",
        max_length=68,
        blank=True,
        null=True,
        choices=settings.VOIVODESHIP_CHOICES,
    )
    voivodeship_obj = models.ForeignKey(
        Voivodeships,
        verbose_name=_("Województwo zamieszkania"),
        help_text="Wybierz województwo.",
        max_length=20,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    voivodeship_raw = models.CharField(
        # TODO:(l.remkowicz):followup needed to check if that can be safely removed from database scheme follow-up: PM-365  # noqa: E501
        _("Wojewódźtwo (raw)"),
        help_text=_("Wojewódźtwo w którym grasz. Nie uzywane pole"),
        max_length=68,
        blank=True,
        null=True,
        choices=settings.VOIVODESHIP_CHOICES,
    )
    address = AddressField(
        help_text=_("Miasto z którego dojeżdżam na trening"), blank=True, null=True
    )
    # address = models.CharField(max_length=100, help_text=_('Miasto z którego dojeżdżam na trening'), blank=True, null=True)  # noqa: E501
    practice_distance = models.PositiveIntegerField(
        _("Odległość na trening"),
        blank=True,
        null=True,
        help_text=_("Maksymalna odległośc na trening"),
        validators=[
            validators.MinValueValidator(10),
            validators.MaxValueValidator(500),
        ],
    )
    about = models.TextField(_("O sobie"), null=True, blank=True)
    training_ready = models.IntegerField(
        _("Gotowość do treningu"),
        choices=profile_utils.make_choices(TRAINING_READY_CHOCIES),
        null=True,
        blank=True,
    )
    country = CountryField(
        _("Country"),
        default="PL",
        null=True,
        blank_label=_("Wybierz kraj"),
    )
    agent_status = models.IntegerField(
        _("Czy posiadasz agenta"),
        choices=profile_utils.make_choices(AGENT_STATUS_CHOICES),
        blank=True,
        null=True,
    )
    agent_name = models.CharField(
        _("Nazwa agenta"), max_length=45, blank=True, null=True
    )
    agent_phone = models.CharField(
        _("Telefon do agenta"), max_length=15, blank=True, null=True
    )
    agent_foreign = models.BooleanField(
        _("Otwarty na propozycje zagraniczne"), blank=True, null=True
    )
    updated = models.BooleanField(default=False)

    def display_position_fantasy(self):
        if self.position_fantasy is not None:
            if self.position_fantasy.lower() == "obronca":
                return "obrońca"
            return self.position_fantasy
        else:
            return None

    def has_meta_entry_for(self, season: str):
        """checks if meta info exists for given season"""

        if self.meta is None:
            return None
        return self.meta.get(season, None) is not None

    def calculate_fantasy_object(self, *args, **kwargs):
        season = utilites.get_current_season()
        if not self.has_meta_entry_for(season):
            msg = (
                f'Cannot calculate fantasy data object do not have "meta" '
                f'or "meta" data do not have data for season={season}'
            )
            self.add_event_log_message(msg)
            return

        from fantasy.models import CalculateFantasyStats

        f = CalculateFantasyStats()
        f.calculate_fantasy_for_player(self, season, is_senior=True)
        f.calculate_fantasy_for_player(self, season, is_senior=False)

    # DEPRECATED: PM-1015
    # def calculate_data_from_data_models(self, adpt=None, *args, **kwargs):
    #     """Interaction with s38: league, vivo, team <- s38"""
    #     if self.attached:
    #         adpt = adpt or PlayerAdapter(
    #             int(
    #                 self.mapper.get_entity(
    #                     related_type="player", database_source="s38"
    #                 ).mapper_id
    #             )
    #         )
    #         if adpt.has_player:
    #             self.league = adpt.get_current_league()
    #             self.voivodeship = adpt.get_current_voivodeship()
    #             # self.club = adpt.get_current_club()  # not yet implemented. Maybe after 1.12  # noqa: E501
    #             self.team = adpt.get_current_team()

    # DEPRECATED: PM-1015
    # def update_data_player_object(self, adpt=None):
    #     """Interaction with s38: updates --> s38 wix_id and fantasy position"""
    #     if self.attached:
    #         adpt = adpt or PlayerAdapter(
    #             self.mapper.get_entity(
    #                 related_type="player", database_source="s38"
    #             ).mapper_id
    #         )
    #         adpt.update_wix_id_and_position(
    #             email=self.user.email, position=self.position_fantasy
    #         )

    # DEPRECATED: PM-1015
    # def fetch_data_player_meta(self, adpt=None, save=True, *args, **kwargs):
    #     """Interaction with s38: updates meta from <--- s38"""
    #     if self.attached:
    #         adpt = adpt or PlayerAdapter(
    #             int(
    #                 self.mapper.get_entity(
    #                     related_type="player", database_source="s38"
    #                 ).mapper_id
    #             )
    #         )
    #         self.meta = adpt.player.meta
    #         self.meta_updated = timezone.now()
    #         if save:
    #             self.save()

    # DEPRECATED: PM-1015
    # def trigger_refresh_data_player_stats(self, adpt=None, *args, **kwargs):
    #     """Trigger update of player stats --> s38"""
    #     if self.attached:
    #         adpt = adpt or PlayerAdapter(
    #             int(
    #                 self.mapper.get_entity(
    #                     related_type="player", database_source="s38"
    #                 ).mapper_id
    #             )
    #         )
    #         adpt.calculate_stats(season_name=utilites.get_current_season())

    def get_team_object_based_on_meta(self, season_name, retries: int = 3):
        """set TeamObject based on meta data"""
        if retries <= 0 or self.meta is None:
            return None
        season_data = self.meta.get(season_name, None)
        if season_data is not None:
            team_name = season_data["team"]
            league_code = season_data["league_code"]
            if not team_name:
                return None
            from clubs.services import TeamAdapter

            team_object = TeamAdapter().match_name_or_mapping_with_code(
                team_name, str(league_code)
            )
            return team_object
        else:
            r = retries - 1
            self.get_team_object_based_on_meta(
                utilites.calculate_prev_season(season_name), retries=r
            )

    def set_team_object_based_on_meta(self, save=True):
        if self.meta is not None and self.attached:
            team_object = self.get_team_object_based_on_meta(
                utilites.get_current_season()
            )
            logger.info(f"Found team_object `{team_object}` for playerprofile {self}")
            if team_object is not None:
                logger.debug(f"Setting new team_object for {self}")
                self.team_object = team_object
                if save:
                    logger.debug(f"Saving new team_object for {self}")
                    self.save()
                    return
        logger.info("Object not found or meta is empty.")

    def refresh_metrics(self, *args, **kwargs):
        self.add_event_log_message(
            kwargs.get("event_log_msg", "Refresh metrics started.")
        )
        self.playermetrics.refresh_metrics(*args, **kwargs)

    def refresh_scoring(self, *args, **kwargs) -> None:
        """Call metrics method to refresh scoring for player"""
        self.add_event_log_message(
            kwargs.get("event_log_msg", "Refresh scoring started.")
        )
        self.playermetrics.refresh_scoring(*args, **kwargs)

    def create_mapper_obj(self):
        self.mapper = Mapper.objects.create()

    def create_external_links_obj(self) -> None:
        """
        Create a new ExternalLinks object
        and associate it with this PlayerProfile instance.
        """
        self.external_links = ExternalLinks.objects.create()

    def save(self, *args, **kwargs):
        """'Nie jest wyświetlana na profilu.
        Pole wykorzystywane wyłącznie do gry Fantasy.
        Użytkownik nie ingeruje w nie, bo ustawiony jest trigger przy wyborze pozycji z A18.
        'Bramkarz' -> 'bramkarz';
        'Obrońca%' ->  'obronca';
        '%pomocnik' -> pomocnik;
        'Skrzydłowy' -> 'pomocnik';
        'Napastnik' -> 'napastnik'

           POSITION_CHOICES = [
        (1, 'Bramkarz'),
        (2, 'Obrońca Lewy'),
        (3, 'Obrońca Prawy'),
        (4, 'Obrońca Środkowy'),
        (5, 'Pomocnik defensywny (6)'),
        (6, 'Pomocnik środkowy (8)'),
        (7, 'Pomocnik ofensywny (10)'),
        (8, 'Skrzydłowy'),
        (9, 'Napastnik'),
        ]
        """  # noqa: E501
        if self.position_raw is not None:
            self.position_fantasy = self.FANTASY_MAPPING.get(self.position_raw, None)

        if not self.mapper:
            self.create_mapper_obj()

        if not self.external_links:
            self.create_external_links_obj()

        # adpt = None
        # Each time actions
        # if self.attached:
        #     old = self.playermetrics.how_old_days
        #     # logger.error(
        #     f'xxxxx {any([old(season=True) >= 1,
        #     old(fantasy=True) >= 1,
        #     old(games=True) >= 1])}
        #     {old(season=True) >= 1}
        #     {old(fantasy=True) >= 1}
        #     {old(games=True) >= 1}'
        #     )
        #     if any([old(season=True) >= 1, old(fantasy=True) >= 1, old(games=True) >= 1]):  # noqa: E501
        #         logger.debug(f'Stats old enough {self}')
        #         self.playermetrics.refresh_metrics()  # download: metrics data

        # print(f'---------- Datamapper: {self.data_mapper_changed}')
        super().save(*args, **kwargs)
        # print(f'---------- Datamapper: {self.data_mapper_changed}')

        # DEPRECATED: PM-1015
        # Onetime actions:
        # if (
        #     self.data_mapper_changed and self.attached
        # ):  # if datamapper changed after save and it is not None
        #     logger.info(f"Calculating metrics for player {self}")
        #     adpt = PlayerAdapter(
        #         int(
        #             self.mapper.get_entity(
        #                 related_type="player", database_source="s38"
        #             ).mapper_id
        #         )
        #     )  # commonly use adpt
        #     if utilites.is_allowed_interact_with_s38():  # are we on PROD and not Debug  # noqa: E501
        #         self.update_data_player_object(adpt)  # send data to s38
        #         self.trigger_refresh_data_player_stats(adpt)  # send trigger to s38
        #     self.calculate_data_from_data_models(
        #         adpt
        #     )  # update league, vivo, team from Players meta
        #     self.fetch_data_player_meta(adpt)  # update update meta
        # create_or_update_player_external_links(self)

    class Meta:
        verbose_name = "Player Profile"
        verbose_name_plural = "Player Profiles"


class PlayerMetrics(models.Model):
    # @todo tu powinna isc metoda    u.profile.playermetrics.refresh()
    player = models.OneToOneField(
        PlayerProfile,
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    games_summary = models.JSONField(null=True, blank=True)
    games_summary_updated = models.DateTimeField(null=True, blank=True)
    games = models.JSONField(null=True, blank=True)
    games_updated = models.DateTimeField(null=True, blank=True)

    fantasy_summary = models.JSONField(null=True, blank=True)
    fantasy_summary_updated = models.DateTimeField(null=True, blank=True)
    fantasy = models.JSONField(null=True, blank=True)
    fantasy_updated = models.DateTimeField(null=True, blank=True)

    season_summary = models.JSONField(null=True, blank=True)
    season_summary_updated = models.DateTimeField(null=True, blank=True)
    season = models.JSONField(null=True, blank=True)
    season_updated = models.DateTimeField(null=True, blank=True)

    pm_score = models.IntegerField(
        null=True, blank=True, verbose_name="PlayMaker Score"
    )
    pm_score_updated = models.DateTimeField(
        null=True, blank=True, verbose_name="PlayMaker Score date updated"
    )

    season_score = models.JSONField(null=True, blank=True, verbose_name="Season Score")
    season_score_updated = models.DateTimeField(
        null=True, blank=True, verbose_name="Season Score date updated"
    )

    def _update_cached_field(self, attr: str, data, commit=True):
        if not data:
            return
        setattr(self, attr, data)
        setattr(self, f"{attr}_updated", timezone.now())
        if commit:
            self.save()

    def refresh_metrics(
        self, method: typing.Type[API_METHOD] = ScrapperAPI, *args, **kwargs
    ) -> None:
        """
        get metrics from api and save into model
        fantasy is currently unavailable
        """
        start = datetime.now()
        stats = self.get_season_data(method)
        stats_summary = self.get_season_summary_data(method)
        self.update_season(stats)
        print(f"\t> PlayerStatsSeasonAdapter: {datetime.now() - start}")

        start = datetime.now()
        games = self.get_games_data(method)
        games_summary = games[:3]
        self.update_games(games)
        print(f"\t> PlayerLastGamesAdapter: {datetime.now() - start}")

        self.update_summaries(games_summary, stats_summary, None)
        self.save()

    def refresh_scoring(self, method: typing.Type[API_METHOD] = ScrapperAPI) -> None:
        """Refresh scoring section"""
        data = self.get_score(method)
        pm_score, season_score = data.get("pm_score"), data.get("season_score")

        self.update_pm_score(pm_score, commit=False)
        self.update_season_score(season_score, commit=False)
        # add here new updaters related to scoring
        self.save()

    def get_and_update_pm_score(
        self, method: typing.Type[API_METHOD] = ScrapperAPI
    ) -> None:
        """Get and update PlaymakerScore only"""
        data = self.get_score(method)
        self.update_pm_score(data.get("pm_score"))

    def get_and_update_season_score(
        self, method: typing.Type[API_METHOD] = ScrapperAPI
    ) -> None:
        """Get and update Season only"""
        data = self.get_score(method)
        self.update_season_score(data.get("season_score"))

    def get_games_data(
        self, method: typing.Type[API_METHOD] = ScrapperAPI
    ) -> typing.List:
        player_obj = getattr(self, "player")
        games_adapter = PlayerGamesAdapter(
            player=player_obj, strategy=strategy.AlwaysUpdate, api_method=method
        )
        games_adapter.get_latest_seasons_player_games()
        serializer = games_adapter.serialize()
        return serializer.data

    def get_games_summary_data(
        self, method: typing.Type[API_METHOD] = ScrapperAPI
    ) -> typing.List:
        player_obj = getattr(self, "player")
        games_adapter = PlayerGamesAdapter(
            player=player_obj, strategy=strategy.AlwaysUpdate, api_method=method
        )
        games_adapter.get_player_games()
        serializer = games_adapter.serialize(limit=3)
        return serializer.data

    def get_season_data(
        self, method: typing.Type[API_METHOD] = ScrapperAPI
    ) -> typing.Dict:
        player_obj = getattr(self, "player")
        stats_adapter = PlayerSeasonStatsAdapter(
            player=player_obj, strategy=strategy.AlwaysUpdate, api_method=method
        )
        stats_adapter.get_latest_seasons_stats(primary_league=False)
        serializer = stats_adapter.serialize()
        return serializer.data

    def get_season_summary_data(
        self, method: typing.Type[API_METHOD] = ScrapperAPI
    ) -> typing.Dict:
        player_obj = getattr(self, "player")
        stats_adapter = PlayerSeasonStatsAdapter(
            player=player_obj, strategy=strategy.AlwaysUpdate, api_method=method
        )
        stats_adapter.get_season_stats()
        serializer = stats_adapter.serialize()
        return serializer.data_summary

    def get_score(self, method: typing.Type[API_METHOD] = ScrapperAPI) -> dict:
        """get scoring for player"""
        player_obj = getattr(self, "player")
        score_adapter = PlayerScoreAdapter(
            player=player_obj, strategy=strategy.AlwaysUpdate, api_method=method
        )
        score_adapter.get_scoring()

        serializer = score_adapter.serialize()
        return serializer.data

    def update_summaries(self, games, season, fantasy):
        self.update_games_summary(games, commit=False)
        # self.update_fantasy_summary(fantasy, commit=False)
        self.update_season_summary(season, commit=False)

    def update_pm_score(self, *args, **kwargs) -> None:
        """Update PlayMaker Score"""
        self._update_cached_field("pm_score", *args, **kwargs)

    def update_season_score(self, *args, **kwargs) -> None:
        """Update Season Score"""
        self._update_cached_field("season_score", *args, **kwargs)

    def update_games(self, *args, **kwargs):
        self._update_cached_field("games", *args, **kwargs)

    def update_games_summary(self, *args, **kwargs):
        self._update_cached_field("games_summary", *args, **kwargs)

    def update_fantasy(self, *args, **kwargs):
        self._update_cached_field("fantasy", *args, **kwargs)

    def update_fantasy_summary(self, *args, **kwargs):
        self._update_cached_field("fantasy_summary", *args, **kwargs)

    def update_season(self, *args, **kwargs):
        self._update_cached_field("season", *args, **kwargs)

    def update_season_summary(self, *args, **kwargs):
        self._update_cached_field("season_summary", *args, **kwargs)

    def how_old_days(
        self,
        games=False,
        season=False,
        fantasy=False,
        games_summary=False,
        season_summary=False,
        fantasy_summary=False,
    ):
        if games:
            date = self.games_updated
        elif games_summary:
            date = self.games_summary_updated
        elif season:
            date = self.season_updated
        elif season_summary:
            date = self.season_summary_updated
        elif fantasy:
            date = self.fantasy_updated
        elif fantasy_summary:
            date = self.fantasy_summary_updated
        else:
            date = self.updated_at

        if date is None:
            return 999
        now = timezone.now()
        diff = now - date
        return diff.days

    def wipe_metrics(self) -> None:
        """Wipe all metrics data"""
        self.games_summary = None
        self.games_summary_updated = None
        self.games = None
        self.games_updated = None

        self.fantasy_summary = None
        self.fantasy_summary_updated = None
        self.fantasy = None
        self.fantasy_updated = None

        self.season_summary = None
        self.season_summary_updated = None
        self.season = None
        self.season_updated = None

        self.pm_score = None
        self.pm_score_updated = None

        self.season_score = None
        self.season_score_updated = None

        self.save()

    def save(self, data_refreshed: bool = None, *args, **kwargs):
        if data_refreshed is not None and data_refreshed is True:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Metryka gracza")
        verbose_name_plural = _("Metryki graczy")

    def __str__(self):
        def none_or_date(param):
            _f = "%b/%d/%Hh"
            return (
                getattr(self, param).strftime(_f)
                if getattr(self, param)
                else getattr(self, param)
            )

        params = {
            "g": none_or_date("games_updated"),
            "gs": none_or_date("games_summary_updated"),
            "c": none_or_date("season_updated"),
            "cs": none_or_date("season_summary_updated"),
            "f": none_or_date("fantasy_updated"),
            "fs": none_or_date("fantasy_summary_updated"),
        }
        return " ".join([f"{name}:{metric}" for name, metric in params.items()])


class ClubProfile(BaseProfile):
    _video_labels = ProfileVideo.ClubLabels
    PROFILE_TYPE = definitions.PROFILE_TYPE_CLUB

    CLUB_ROLE = definitions.CLUB_ROLES

    VERIFICATION_FIELDS = [
        # 'team_club_league_voivodeship_ver',
        "club_role",
    ]

    def get_club_object_or_none(self):
        if self.club_object:
            return self.club_object

    @property
    @profile_utils.supress_exception
    def display_club(self):
        return self.club_object.display_club

    @property
    @profile_utils.supress_exception
    def display_voivodeship(self):
        return self.club_object.display_voivodeship

    @property
    def has_attachemnt(self):
        if self.club_object is not None:
            return True
        return False

    @property
    def is_clubless(self):
        if self.club_object:
            return True
        return False

    club_object = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        related_name="clubowners",
        db_index=True,
        null=True,
        blank=True,
    )
    team_object = models.ForeignKey(
        "clubs.Team",
        on_delete=models.SET_NULL,
        related_name="club_profiles",
        null=True,
        blank=True,
    )
    team_history_object = models.ForeignKey(
        "clubs.TeamHistory",
        on_delete=models.SET_NULL,
        related_name="club_profiles_history",
        null=True,
        blank=True,
    )
    phone = models.CharField(_("Telefon"), max_length=15, blank=True, null=True)
    team_club_league_voivodeship_ver = models.CharField(
        _("team_club_league_voivodeship_ver"),
        max_length=355,
        help_text=_("Drużyna, klub, rozgrywki, wojewódźtwo."),
        blank=True,
        null=True,
    )
    club_role = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        choices=CLUB_ROLE,
        help_text=_("Defines if admin approved change"),
    )
    custom_club_role = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Custom club role specified by the user."),
    )
    external_links = models.OneToOneField(
        ExternalLinks, on_delete=models.SET_NULL, blank=True, null=True
    )

    class Meta:
        verbose_name = "Club Profile"
        verbose_name_plural = "Club Profiles"


class LicenceType(models.Model):
    name = models.CharField(
        _("Licencja"), max_length=25, unique=True, help_text=_("Type of the licence")
    )
    key = models.CharField(
        _("Key"),
        max_length=10,
        null=True,
        blank=True,
        help_text=_("Key of the licence"),
    )
    order = models.PositiveIntegerField(
        unique=True,
        help_text=_("Order in which the licence will be listed."),
    )

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ["order"]


class CoachProfile(BaseProfile, TeamObjectsDisplayMixin):
    _video_labels = ProfileVideo.CoachLabels
    PROFILE_TYPE = definitions.PROFILE_TYPE_COACH
    DATA_KEY_GAMES = "games"
    DATA_KET_CARRIER = "carrier"

    COMPLETE_FIELDS = [
        "phone",
    ]

    CLUB_ROLE = (
        (1, "Trener"),
        (2, "Prezes"),
        (3, "Kierownik"),
        (4, "Członek zarządu"),
        (5, "Sztab szkoleniowy"),
        (6, "Inne"),
    )

    VERIFICATION_FIELDS = [
        "country",
        "birth_date",
        "licence",
    ]  # 'team_club_league_voivodeship_ver']

    OPTIONAL_FIELDS = ["licence"]

    GOAL_CHOICES = (
        (1, "Profesjonalna kariera"),
        (2, "Kariera regionalna"),
        (3, "Trenerka jako hobby"),
    )

    LICENCE_CHOICES = (
        (1, "UEFA PRO"),
        (2, "UEFA A"),
        (3, "UEFA EY A"),
        (4, "UEFA B"),
        (5, "UEFA C"),
        (6, "GRASS C"),
        (7, "GRASS D"),
        (8, "UEFA Futsal B"),
        (9, "PZPN A"),
        (10, "PZPN B"),
        (11, "W trakcie kursu"),
    )

    COACH_ROLE_CHOICES = (
        ("IC", "Pierwszy trener"),
        ("IIC", "Drugi trener"),
        ("GKC", "Trener bramkarzy"),
        ("FIC", "Trener motoryki"),
        ("MEC", "Trener mentalny"),
        ("ANC", "Analityk"),
        ("OTC", "Inne"),
    )

    DATA_KEYS = ("metrics",)

    # Deprecated PM20-79
    licence = models.IntegerField(
        _("Licencja"),
        choices=LICENCE_CHOICES,
        blank=True,
        null=True,
    )

    team_club_league_voivodeship_ver = models.CharField(
        _("Województwo"),
        max_length=355,
        help_text=_("Drużyna, klub, rozgrywki, wojewódźtwo."),
        blank=True,
        null=True,
    )

    team_object = models.ForeignKey(
        "clubs.Team",
        on_delete=models.SET_NULL,
        related_name="coaches",
        null=True,
        blank=True,
    )
    team_history_object = models.ForeignKey(
        "clubs.TeamHistory",
        on_delete=models.SET_NULL,
        related_name="players_history",
        null=True,
        blank=True,
    )
    # DEPRECATED: Migrated to UserPreferences PM20-148
    birth_date = models.DateField(_("Data urodzenia"), blank=True, null=True)
    soccer_goal = models.IntegerField(
        _("Piłkarski cel"),
        choices=profile_utils.make_choices(GOAL_CHOICES),
        null=True,
        blank=True,
    )
    phone = models.CharField(_("Telefon"), max_length=15, blank=True, null=True)
    facebook_url = models.URLField(_("Facebook"), max_length=500, blank=True, null=True)
    mapper = models.OneToOneField(
        Mapper, on_delete=models.SET_NULL, blank=True, null=True
    )
    external_links = models.OneToOneField(
        ExternalLinks, on_delete=models.SET_NULL, blank=True, null=True
    )
    country = CountryField(
        _("Country"),
        blank=True,
        default="PL",
        null=True,
        blank_label=_("Wybierz kraj"),
    )

    practice_distance = models.PositiveIntegerField(
        _("Maksymalna odległość na trening"),
        blank=True,
        null=True,
        help_text=_("Maksymalna odległośc na trening"),
        validators=[
            validators.MinValueValidator(10),
            validators.MaxValueValidator(500),
        ],
    )

    about = models.TextField(_("O sobie"), null=True, blank=True)

    address = AddressField(
        help_text=_("Miasto z którego dojeżdżam na trening"), blank=True, null=True
    )

    # TODO Based on task PM-363. After migration on production, field can be deleted
    voivodeship = models.CharField(
        _("Województwo zamieszkania."),
        help_text="Wybierz województwo. Stare pole przygotowane do migracji",
        max_length=68,
        blank=True,
        null=True,
        choices=settings.VOIVODESHIP_CHOICES,
    )
    voivodeship_obj = models.ForeignKey(
        Voivodeships,
        verbose_name=_("Województwo zamieszkania"),
        help_text="Wybierz województwo.",
        max_length=20,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    club_role = models.IntegerField(
        choices=CLUB_ROLE,
        default=1,  # trener
        null=True,
        blank=True,
        help_text="Defines if admin approved change",
    )
    coach_role = models.CharField(
        _("Rola trenera"),
        max_length=3,
        choices=COACH_ROLE_CHOICES,
        blank=True,
        null=True,
        help_text=_("This field represents the role of the coach."),
    )
    custom_coach_role = models.CharField(
        _("Custom Coach Role"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Custom club role specified by the user."),
    )

    formation = models.CharField(
        _("Formacja"),
        max_length=7,
        choices=FORMATION_CHOICES,
        blank=True,
        null=True,
        help_text=_("This field represents the preferred formation of the coach."),
    )

    data = models.JSONField(null=True, blank=True)

    def get_season_games_data(self, season: str) -> bool:
        if (
            self.data
            and self.data.get(season)
            and isinstance(self.data.get(season), dict)
            and self.data.get(season).get(self.DATA_KEY_GAMES)
        ):
            return self.data.get(season).get(self.DATA_KEY_GAMES)

    def get_data(self) -> list:
        if self.data and isinstance(self.data, dict):
            return self.data

    def get_season_carrier_data(self, season: str) -> bool:
        if (
            self.data
            and self.data.get(season)
            and isinstance(self.data.get(season), dict)
            and self.data.get(season).get(self.DATA_KET_CARRIER)
        ):
            return self.data.get(season).get(self.DATA_KET_CARRIER)

    def get_total_season_carrier_data(self, season: str) -> bool:
        data = self.get_season_carrier_data(season)
        if data:
            return data.get("total")

    def calculate_metrics(
        self, seasons_behind: int = 1, season_name: str = None, requestor: User = None
    ):
        """
        :param seasons_behind: if present it defines how many season we want to calucalte in past.
                               value 1 means that we will calcuate for current season
        :season_name: name of season to update

        Celem jest możliwość pokazania:
        kariera [sezon, team, rozgrywki, wygrane mecze,
        remisy, porażki, śr. pkt na mecz,  bramki strzelone vs. bramki stracone (klubu, który prowadził)]
        mecze [data, rozgrywki, gospodarz, gość, wynik]

        Za wygrany mecz 3 pkt, za remis 1 pkt, za porażkę 0 pkt.

        """  # noqa: E501
        from metrics.coach import CoachCarrierAdapterPercentage, CoachGamesAdapter

        if not self.has_data_id:
            return
        _id = int(
            self.mapper.get_entity(
                related_type="coach", database_source="s38"
            ).mapper_id
        )
        season_name = season_name or utilites.get_current_season()

        def _calculate(season_name):
            # set default value for data attribute
            if self.data is None:
                self.data = {}

            if not self.data.get(season_name):
                self.data[season_name] = {}

            games = CoachGamesAdapter().get(int(_id), season_name=season_name)
            self.data[season_name][self.DATA_KEY_GAMES] = games

            season_stats = CoachCarrierAdapterPercentage().get(
                int(_id), season_name=season_name
            )
            self.data[season_name][self.DATA_KET_CARRIER] = season_stats

        for _ in range(seasons_behind):  # noqa: F402
            print(f"Calculating data for {self} for season {season_name}")
            _calculate(season_name)
            season_name = utilites.calculate_prev_season(season_name)
        msg = "Coach stats updated."
        self.add_event_log_message(msg, commit=False)
        self.save()

    def create_mapper_obj(self):
        self.mapper = Mapper.objects.create()

    def create_external_links_obj(self) -> None:
        """
        Create a new ExternalLinks object and associate it with this CoachProfile instance.
        """  # noqa: E501
        self.external_links = ExternalLinks.objects.create()

    def save(self, *args, **kwargs):
        if not self.mapper:
            self.create_mapper_obj()
        if not self.external_links:
            self.create_external_links_obj()
        super().save(*args, **kwargs)
        # Update or create external links associated with the coach.
        # This ensures that the coach's external links are always up-to-date.
        create_or_update_profile_external_links(self)

    def display_licence(self) -> typing.Optional[str]:
        """
        Returns a string representation of the licences associated with the coach profile.
        """  # noqa: E501
        licences = self.licences.values_list("licence__name", flat=True)
        return ", ".join(licences) if licences else None

    @property
    def has_attachemnt(self):
        if self.team_object is not None:
            return True
        return False

    @property
    def age(self) -> typing.Optional[int]:
        return self.user.userpreferences.age

    class Meta:
        verbose_name = "Coach Profile"
        verbose_name_plural = "Coaches Profiles"


class CoachLicence(models.Model):
    licence = models.ForeignKey(
        LicenceType,
        on_delete=models.CASCADE,
        help_text=_("The type of licence held by the coach"),
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Each user can have licences
        on_delete=models.CASCADE,
        related_name="licences",
        help_text=_("User holding this license"),
    )
    expiry_date = models.DateField(
        blank=True, null=True, help_text=_("The expiry date of the licence (optional)")
    )
    release_year = models.IntegerField(blank=True, null=True)
    is_in_progress = models.BooleanField(default=False)

    class Meta:
        unique_together = ("licence", "owner")

    def __str__(self):
        return f"{self.licence.name}"


class GuestProfile(BaseProfile):
    """In this model we store data about "fan" (kibic) users."""

    PROFILE_TYPE = definitions.PROFILE_TYPE_GUEST
    AUTO_VERIFY = True
    facebook_url = models.URLField(_("Facebook"), max_length=500, blank=True, null=True)
    team_object = models.ForeignKey(
        "clubs.Team",
        on_delete=models.SET_NULL,
        related_name="guest_profiles",
        null=True,
        blank=True,
    )
    team_history_object = models.ForeignKey(
        "clubs.TeamHistory",
        on_delete=models.SET_NULL,
        related_name="guest_history",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Guest Profile"
        verbose_name_plural = "Guests Profiles"


class ManagerProfile(BaseProfile):
    PROFILE_TYPE = definitions.PROFILE_TYPE_MANAGER
    AUTO_VERIFY = True
    facebook_url = models.URLField(_("Facebook"), max_length=500, blank=True, null=True)
    other_url = models.URLField(_("Other"), max_length=500, blank=True, null=True)
    external_links = models.OneToOneField(
        ExternalLinks, on_delete=models.SET_NULL, blank=True, null=True
    )
    agency_phone = models.CharField(
        _("Agency Phone"),
        max_length=15,
        blank=True,
        null=True,
        help_text=_("Contact phone number for the managing agency."),
    )
    agency_email = models.EmailField(
        _("Agency Email"),
        blank=True,
        null=True,
        help_text=_("Contact email address for the managing agency."),
    )
    agency_transfermarkt_url = models.URLField(
        _("Agency Transfermarkt URL"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("URL of the managing agency's profile on Transfermarkt."),
    )
    agency_website_url = models.URLField(
        _("Agency Website URL"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("URL of the managing agency's official website."),
    )
    agency_instagram_url = models.URLField(
        _("Agency Instagram URL"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("URL of the managing agency's Instagram profile."),
    )
    agency_twitter_url = models.URLField(
        _("Agency Twitter URL"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("URL of the managing agency's Twitter profile."),
    )
    agency_facebook_url = models.URLField(
        _("Agency Facebook URL"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("URL of the managing agency's Facebook profile."),
    )
    agency_other_url = models.URLField(
        _("Agency Facebook URL"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("Other agency URL."),
    )
    team_object = models.ForeignKey(
        "clubs.Team",
        on_delete=models.SET_NULL,
        related_name="manager_profiles",
        null=True,
        blank=True,
    )
    team_history_object = models.ForeignKey(
        "clubs.TeamHistory",
        on_delete=models.SET_NULL,
        related_name="managers_history",
        null=True,
        blank=True,
    )

    def create_external_links_obj(self):
        """
        Create a new ExternalLinks object and associate it with this ManagerProfile instance.
        """  # noqa: E501
        self.external_links = ExternalLinks.objects.create()

    def save(self, *args, **kwargs):
        if not self.external_links:
            self.create_external_links_obj()
        super().save(*args, **kwargs)
        # Update or create external links associated with the manager.
        # This ensures that the manager's external links are always up-to-date.
        create_or_update_profile_external_links(self)

    class Meta:
        verbose_name = "Manager Profile"
        verbose_name_plural = "Managers Profiles"


class ScoutProfile(BaseProfile):
    _video_labels = ProfileVideo.ScoutLabels
    PROFILE_TYPE = definitions.PROFILE_TYPE_SCOUT
    AUTO_VERIFY = True
    VERIFICATION_FIELDS = []

    COMPLETE_FIELDS = ["soccer_goal"]

    OPTIONAL_FIELDS = [
        "country",
        "facebook_url",
        "address",
        "practice_distance",
        "club_raw",
        "league_raw",
        "voivodeship_obj",
    ]

    GOAL_CHOICES = (
        (1, "Profesjonalna kariera"),
        (2, "Kariera regionalna"),
        (3, "Skauting jako hobby"),
    )

    soccer_goal = models.IntegerField(
        _("Piłkarski cel"),
        choices=profile_utils.make_choices(GOAL_CHOICES),
        # max_length=60,
        null=True,
        blank=True,
    )
    country = CountryField(
        _("Country"),
        default="PL",
        blank=True,
        null=True,
        blank_label=_("Wybierz kraj"),
    )
    facebook_url = models.URLField(_("Facebook"), max_length=500, blank=True, null=True)

    address = AddressField(max_length=100, help_text=_("Adres"), blank=True, null=True)

    external_links = models.OneToOneField(
        ExternalLinks, on_delete=models.SET_NULL, blank=True, null=True
    )

    practice_distance = models.PositiveIntegerField(
        _("Maksymalna odległość na trening"),
        blank=True,
        null=True,
        help_text=_("Maksymalna odległośc na trening"),
        validators=[
            validators.MinValueValidator(10),
            validators.MaxValueValidator(500),
        ],
    )

    club_raw = models.CharField(
        _("Deklarowany klub"),
        max_length=68,
        help_text=_("Klub w którym obecnie reprezentuejsz"),
        blank=True,
        null=True,
    )

    league_raw = models.CharField(
        _("Deklarowany poziom rozgrywkowy"),
        max_length=68,
        help_text=_("Poziom rozgrywkowy"),
        blank=True,
        null=True,
    )

    voivodeship_obj = models.ForeignKey(
        Voivodeships,
        verbose_name=_("Województwo zamieszkania"),
        help_text="Wybierz województwo.",
        max_length=20,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    voivodeship_raw = models.CharField(
        _("Deklarowane wojewódźtwo"),
        help_text=_("Wojewódźtwo w którym grasz."),
        max_length=68,
        blank=True,
        null=True,
    )  # TODO:(l.remkowicz): followup needed to see if that can be safely removed from database scheme follow-up: PM-365  # noqa: E501
    team_object = models.ForeignKey(
        "clubs.Team",
        on_delete=models.SET_NULL,
        related_name="scouts",
        null=True,
        blank=True,
    )
    team_history_object = models.ForeignKey(
        "clubs.TeamHistory",
        on_delete=models.SET_NULL,
        related_name="scouts_history",
        null=True,
        blank=True,
    )

    def create_external_links_obj(self) -> None:
        """
        Create a new ExternalLinks object and associate it with this ScoutProfile instance.
        """  # noqa: E501
        self.external_links = ExternalLinks.objects.create()

    def save(self, *args, **kwargs):
        if not self.external_links:
            self.create_external_links_obj()
        super().save(*args, **kwargs)
        # Update or create external links associated with the scout.
        # This ensures that the scout's external links are always up-to-date.
        create_or_update_profile_external_links(self)

    class Meta:
        verbose_name = "Scout Profile"
        verbose_name_plural = "Scouts Profiles"


class RefereeProfile(BaseProfile):
    PROFILE_TYPE = definitions.PROFILE_TYPE_REFEREE
    AUTO_VERIFY = True
    external_links = models.OneToOneField(
        ExternalLinks, on_delete=models.SET_NULL, blank=True, null=True
    )

    class Meta:
        verbose_name = "Referee Profile"
        verbose_name_plural = "Referee Profiles"

    def create_external_links_obj(self) -> None:
        """
        Create a new ExternalLinks object and associate it with this RefereeProfile instance.
        """  # noqa: E501
        self.external_links = ExternalLinks.objects.create()

    def save(self, *args, **kwargs):
        """
        Overrides the save method for the RefereeProfile.

        Ensures that an ExternalLinks object is created for the profile if it doesn't exist.
        Also, it updates or creates necessary external links related to the referee.
        """  # noqa: E501
        if not self.external_links:
            self.create_external_links_obj()
        super().save(*args, **kwargs)
        # Update or create external links associated with the referee.
        # This ensures that the referee's external links are always up-to-date.
        create_or_update_profile_external_links(self)


class RefereeLevel(models.Model):
    REFEREE_ROLE_CHOICES = (
        ("Referee", "Sędzia główny"),
        ("AssistantReferee", "Asystent"),
    )

    level = models.ForeignKey(
        "clubs.League",
        on_delete=models.CASCADE,
        help_text="The league in which the referee has officiated.",
    )
    referee_role = models.CharField(
        _("Role"),
        max_length=17,
        choices=REFEREE_ROLE_CHOICES,
        help_text="The role referee plays on this level (Referee or Assistant Referee).",  # noqa: E501
    )
    referee_profile = models.ForeignKey(
        RefereeProfile,
        null=True,
        on_delete=models.CASCADE,
        help_text="The referee profile that this particular level and role combination is associated with.",  # noqa: E501
    )

    class Meta:
        verbose_name = "Referee Level"
        verbose_name_plural = "Referee Levels"
        unique_together = ("level", "referee_role", "referee_profile")

    @property
    def level_name(self):
        """
        Returns the name of the league in which the referee has officiated.
        """
        return self.level.name

    def __str__(self):
        return f"{self.level_name} - {self.role}"


class OtherProfile(BaseProfile):
    PROFILE_TYPE = definitions.PROFILE_TYPE_OTHER
    AUTO_VERIFY = True
    # TODO: Add specific fields if needed in the future

    class Meta:
        verbose_name = "Other Profile"
        verbose_name_plural = "Other Profiles"


class ProfileVerificationStatus(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verifications",
    )
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="set_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    team = models.ForeignKey(
        "clubs.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team",
    )
    team_history = models.ForeignKey(
        "clubs.TeamHistory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_history",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="club",
    )
    has_team = models.BooleanField(null=True, blank=True)
    team_not_found = models.BooleanField(null=True, blank=True)
    text = models.CharField(max_length=355, null=True, blank=True)

    previous = models.OneToOneField(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="next"
    )

    # objects = managers.VerificationObjectManager()

    # @classmethod
    # def create(
    # cls,
    # owner: User = owner,
    # text: str = text,
    # previous=previous,
    # set_by: User = set_by,
    # status: str = status,
    # has_team: bool = has_team,
    # team_not_found: bool = team_not_found,
    # club = None, team = None,
    # ):
    #     return cls.objects.create(
    #         owner=owner,
    #         text=text,
    #         has_team=has_team,
    #         team_not_found=team_not_found,
    #         club=club,
    #         team=team,
    #         status=status,
    #         set_by=set_by,
    #         previous=previous
    #     )

    @classmethod
    def create_initial(cls, owner: User):
        """Creates initial verifcation object for a profile based on current data."""
        defaults = owner.profile.get_verification_data_from_profile()
        defaults["set_by"] = User.get_system_user()
        defaults["previous"] = None
        return cls.objects.create(**defaults)

    def update_with_profile_data(self, requestor: User = None):
        defaults = self.owner.profile.get_verification_data_from_profile()
        self.set_by = requestor or User.get_system_user()
        self.status = defaults.get("status")
        self.text = defaults.get("text")
        self.has_team = defaults.get("has_team")
        self.team_not_found = defaults.get("team_not_found")
        self.club = defaults.get("club")
        self.team = defaults.get("team")
        self.team_history = defaults.get("team_history")
        self.save()


class PlayerProfilePosition(models.Model):
    player_position = models.ForeignKey(PlayerPosition, on_delete=models.CASCADE)
    player_profile = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name="player_positions",
    )
    is_main = models.BooleanField(
        default=False,
        help_text="Indicates whether this is the player's main position.",
    )

    def __str__(self):
        return f"{self.player_profile.user} - {self.player_position}"

    class Meta:
        verbose_name = "Player Profile Position"
        verbose_name_plural = "Player Profile Positions"
        unique_together = ("player_position", "player_profile")

    def clean(self):
        """
        Validate the object before saving.

        This method is called before a `PlayerProfilePosition` object is saved. It ensures that the following
        constraints are met:
        - A player can have only one main position. (This is checked if the position is marked as main.)
        - A player can have a maximum of two non-main positions.
        """  # noqa: E501
        # Call the parent class's clean method
        # to ensure any inherited validation is performed
        super().clean()
        if self.is_main:
            main_positions = self.player_profile.player_positions.filter(is_main=True)
            if self.pk:
                main_positions = main_positions.exclude(pk=self.pk)

            if main_positions.exists():
                raise validators.ValidationError(
                    "A player can have only one main position."
                )

        non_main_positions = self.player_profile.player_positions.filter(is_main=False)
        if self.pk:
            non_main_positions = non_main_positions.exclude(pk=self.pk)

        if not self.is_main and non_main_positions.count() >= 2:
            raise validators.ValidationError(
                "A player can have a maximum of two non-main positions."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Language(models.Model):
    name = models.CharField(max_length=50)
    native_name = models.CharField(max_length=50)
    code = models.CharField(max_length=10)
    priority = models.IntegerField(default=2)

    def __str__(self):
        return f"{self.name} ({self.native_name})"

    class Meta:
        ordering = ["priority", "name"]


class VerificationStage(models.Model):
    step = models.IntegerField(default=0)
    date_updated = models.DateTimeField(auto_now=True)
    done = models.BooleanField(default=False)

    def __str__(self):
        return f"current step: {self.step} | updated: {self.date_updated} | is done?: {self.done}"


class TeamContributor(models.Model):
    ROUND_CHOICES = [
        ("wiosenna", "wiosenna"),
        ("jesienna", "jesienna"),
    ]

    team_history = models.ManyToManyField("clubs.TeamHistory")
    profile_uuid = models.UUIDField(
        db_index=True, help_text="UUID of the related profile."
    )
    round = models.CharField(
        max_length=10,
        choices=ROUND_CHOICES,
        default=None,
        null=True,
        blank=True,
        help_text="Seasonal round for the contribution.",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Determines if this is the actual contribution.",
    )
    start_date = models.DateField(
        null=True, blank=True, help_text="Start date of the contribution."
    )
    end_date = models.DateField(
        null=True, blank=True, help_text="End date of the contribution."
    )
    role = models.CharField(
        max_length=50,
        choices=CoachProfile.COACH_ROLE_CHOICES + definitions.CLUB_ROLES,
        help_text="Role of the contributor in the team.",
        null=True,
        blank=True,
    )
    custom_role = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Custom role of the contributor when 'Other' is selected.",
    )
    is_primary_for_round = models.BooleanField(
        default=False,
        help_text="Determines if this is the primary contributor for the season and round.",
    )

    class Meta:
        ordering = [
            "-team_history__league_history__season__name",
            "-is_primary",
            "round",
        ]
        unique_together = ("profile_uuid", "role", "start_date")

    @staticmethod
    def get_other_roles():
        return ["O", "OTC"]

    def is_other_role(self):
        return self.role in TeamContributor.get_other_roles()


PROFILE_MODELS = (
    PlayerProfile,
    CoachProfile,
    ClubProfile,
    GuestProfile,
    ManagerProfile,
    ScoutProfile,
    RefereeProfile,
)
PROFILE_TYPE = typing.Union[PROFILE_MODELS]

PROFILE_MODEL_MAP = {
    definitions.PLAYER_SHORT: PlayerProfile,
    definitions.COACH_SHORT: CoachProfile,
    definitions.CLUB_SHORT: ClubProfile,
    definitions.SCOUT_SHORT: ScoutProfile,
    definitions.MANAGER_SHORT: ManagerProfile,
    definitions.GUEST_SHORT: GuestProfile,
    definitions.REFEREE_SHORT: RefereeProfile,
}

REVERSED_MODEL_MAP = {
    model: definition for (definition, model) in PROFILE_MODEL_MAP.items()
}
