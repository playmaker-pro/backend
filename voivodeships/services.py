import json
import logging
from typing import Optional, Tuple, Union

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet

from clubs.models import Club, Team
from marketplace.models import (
    ClubForCoachAnnouncement,
    ClubForPlayerAnnouncement,
    CoachForClubAnnouncement,
    PlayerForClubAnnouncement,
)
from profiles.models import CoachProfile, PlayerProfile, ScoutProfile
from voivodeships.exceptions import VoivodeshipDoesNotExist
from voivodeships.models import Voivodeships

ModelsToMap = Union[
    PlayerProfile,
    CoachProfile,
    ScoutProfile,
    ClubForPlayerAnnouncement,
    PlayerForClubAnnouncement,
    CoachForClubAnnouncement,
    ClubForCoachAnnouncement,
    Club,
]

logger = logging.getLogger(__name__)


class VoivodeshipService:
    def __init__(self):
        self.voivodeships_model = Voivodeships

    @property
    def voivodeship_choices(self):
        return self.voivodeships_model.voivodeships_choices()

    @staticmethod
    def display_voivodeship(obj) -> Union[str, None]:
        """displaying name of voivodeship"""

        if isinstance(obj, Team):
            obj = obj.club

        if obj and obj.voivodeship_obj:
            return obj.voivodeship_obj

    @staticmethod
    def get_voivodeship(obj) -> Optional[Voivodeships]:
        """Returning Voivodeship object"""

        if not obj.voivodeship_obj:
            return None
        return obj.voivodeship_obj

    @property
    def get_voivodeships(self) -> QuerySet:
        return self.voivodeships_model.objects.all()

    def get_voivo_by_id(self, voivo_id: int) -> Optional[Voivodeships]:
        """Returning Voivodeship object by id. Raise exception if doesn't exist"""
        try:
            voivo = self.voivodeships_model.objects.get(id=voivo_id)
            return voivo
        except ObjectDoesNotExist:
            logger.exception(f"Voivo with id {voivo_id} does not exist")
            raise VoivodeshipDoesNotExist

    def get_voivodeship_by_name(self, name) -> QuerySet:
        qry = self.voivodeships_model.objects.filter(name=name)

        if qry.exists():
            return qry

        return self.voivodeships_model.objects.filter(name=self._map_name(name))

    @staticmethod
    def _map_name(name):
        data = {
            "POMORSKI": "Pomorskie",
            "pomorskie": "Pomorskie",
            "ŚLĄSKI": "Śląskie",
            "śląskie": "Śląskie",
            "DOLNOŚLĄSKI": "Dolnośląskie",
            "dolnośląskie": "Dolnośląskie",
            "OPOLSKI": "Opolskie",
            "opolskie": "Opolskie",
            "małopolskie": "Małopolskie",
            "MAŁOPOLSKI": "Małopolskie",
            "ŚWIĘTOKRZYSKI": "Świętokrzyskie",
            "świętokrzyskie": "Świętokrzyskie",
            "MAZOWIECKI": "Mazowieckie",
            "mazowieckie": "Mazowieckie",
            "WARMIŃSKOMAZURSKI": "Warmińsko-Mazurskie",
            "Warmińsko-Mazurskie": "Warmińsko-Mazurskie",
            "warmińskomazurskie": "Warmińsko-Mazurskie",
            "zachodniopomorskie": "Zachodniopomorskie",
            "ZACHODNIOPOMORSKI": "Zachodniopomorskie",
            "PODKARPACKI": "Podkarpackie",
            "podkarpackie": "Podkarpackie",
            "PODLASKI": "Podlaskie",
            "podlaskie": "Podlaskie",
            "WIELKOPOLSKI": "Wielkopolskie",
            "wielkopolskie": "Wielkopolskie",
            "LUBUSKI": "Lubuskie",
            "lubuskie": "Lubuskie",
            "LUBELSKI": "Lubelskie",
            "lubelskie": "Lubelskie",
            "ŁÓDZKI": "Łódzkie",
            "łódzkie": "Łódzkie",
            "Kujawsko-pomorskie": "Kujawsko-Pomorskie",
            "KUJAWSKOPOMORSKI": "Kujawsko-Pomorskie",
            "kujawskopomorskie": "Kujawsko-Pomorskie",
        }
        try:
            result = data[name]
        except KeyError:
            result = ""

        return result

    def save_to_db(self, file_path: Union[str, None] = None) -> None:
        """Fill voivodeships model with data written in voivodeships.json file"""

        if not file_path:
            file_path = "constants/voivodeships.json"

        with open(file_path, "r", encoding="utf8") as f:
            data = json.loads(f.read())

            for voivodeship in data:
                assert isinstance(voivodeship, dict), "element is not a dict"

                voivodeship_name = voivodeship.get("name").capitalize()
                voivodeship_code = voivodeship.get("code")

                try:
                    assert isinstance(
                        voivodeship_name, str
                    ), f"{voivodeship_name} is not a string"

                    obj, created = self.voivodeships_model.objects.get_or_create(
                        name=voivodeship_name
                    )

                    if created:
                        print(f"voivodeship {voivodeship_name} has been added")
                    else:
                        print(
                            f"voivodeship {voivodeship_name} already exists in database"
                        )

                    obj.code = voivodeship_code
                    obj.save()

                except Exception as e:
                    print(f"{voivodeship_name}", e)

    def map_old_field_to_new(self) -> None:
        model_name: Tuple[Tuple[str, str], ...] = (
            ("PlayerProfile", "profiles"),
            ("CoachProfile", "profiles"),
            ("ScoutProfile", "profiles"),
            ("ClubForPlayerAnnouncement", "marketplace"),
            ("PlayerForClubAnnouncement", "marketplace"),
            ("CoachForClubAnnouncement", "marketplace"),
            ("ClubForCoachAnnouncement", "marketplace"),
            ("Club", "clubs"),
        )

        for name in model_name:
            model: ModelsToMap = apps.get_model(name[1], name[0])

            for profile in model.objects.all():
                try:
                    if name[1] == "profiles":
                        voivodeship: QuerySet = self.get_voivodeship_by_name(
                            profile.voivodeship
                        )
                    elif name[1] == "marketplace" and profile.voivodeship:
                        voivodeship: QuerySet = self.get_voivodeship_by_name(
                            profile.voivodeship.name
                        )
                    elif name[1] == "clubs" and profile.voivodeship:
                        voivodeship: QuerySet = self.get_voivodeship_by_name(
                            profile.voivodeship.name
                        )
                    else:
                        continue

                    if voivodeship.exists():
                        voivodeship_model: Voivodeships = apps.get_model(
                            "voivodeships", "Voivodeships"
                        )
                        voivodeship_obj: Voivodeships = voivodeship_model.objects.get(
                            id=voivodeship.first().id
                        )

                        profile.voivodeship_obj = voivodeship_obj
                        profile.save()
                        logger.info(
                            f"[LOGER VOIVODESHIPS] "
                            f'Model {name[0]} with id {profile.id if name[1] != "profiles" else profile.user_id} '  # noqa: 501
                            f"updated"
                        )
                        print(
                            f'Model {name[0]} with id {profile.id if name[1] != "profiles" else profile.user_id} '  # noqa: 501
                            f"updated"
                        )
                except (ObjectDoesNotExist, AttributeError):
                    print(f"Something went wrong with {profile}")
