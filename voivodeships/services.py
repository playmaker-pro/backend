import json
import logging
from typing import Optional, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet

from clubs.models import Club, Team
from profiles.models import CoachProfile, PlayerProfile, ScoutProfile
from voivodeships.exceptions import VoivodeshipDoesNotExist
from voivodeships.models import Voivodeships

ModelsToMap = Union[
    PlayerProfile,
    CoachProfile,
    ScoutProfile,
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
                    assert isinstance(voivodeship_name, str), (
                        f"{voivodeship_name} is not a string"
                    )

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
