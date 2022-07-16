import json
from typing import Union

from django.db.models import QuerySet
from voivodeships.models import Voivodeships

from clubs.models import Team


class VoivodeshipService:

    def __init__(self):
        self.voivodeships_model = Voivodeships

    @property
    def voivodeship_choices(self):
        return self.voivodeships_model.voivodeships_choices()

    @staticmethod
    def display_voivodeship(obj) -> Union[str, None]:
        """ displaying name of voivodeship """

        if isinstance(obj, Team):
            obj = obj.club

        if not obj.voivodeship_obj:
            return None
        return obj.voivodeship_obj

    @staticmethod
    def get_voivodeship(obj) -> Voivodeships:
        """ Returning Voivodeship object """

        if not obj.voivodeship_obj:
            return None
        return obj.voivodeship_obj

    @property
    def get_voivodeships(self) -> QuerySet:
        return self.voivodeships_model.objects.all()

    def get_voivodeship_by_name(self, name) -> QuerySet:
        qry = self.voivodeships_model.objects.filter(name=name)

        if qry.exists():
            return qry

        return self.voivodeships_model.objects.filter(name=self._map_name(name))

    def _map_name(self, name):
        data = {
            "pomorskie": 'Pomorskie',
            "śląskie": 'Śląskie',
            "dolnośląskie": 'Dolnośląskie',
            "opolskie": 'Opolskie',
            "małopolskie": 'Małopolskie',
            "świętokrzyskie": 'Świętokrzyskie',
            "mazowieckie": 'Mazowieckie',
            "warmińskomazurskie": 'Warmińsko-Mazurskie',
            "zachodniopomorskie": 'Zachodniopomorskie',
            "podkarpackie": 'Podkarpackie',
            "podlaskie": 'Podlaskie',
            "wielkopolskie": 'Wielkopolskie',
            "lubuskie": 'Lubuskie',
            "lubelskie": 'Lubelskie',
            "łódzkie": 'Łódzkie',
            "kujawskopomorskie": 'Kujawsko-pomorskie'
        }
        try:
            result = data[name]
        except:
            result = ''

        return result

    def save_to_db(self, file_path: Union[str, None] = None) -> None:
        """ Fill voivodeships model with data written in voivodeships.json file """

        if not file_path:
            file_path = 'constants/voivodeships.json'

        with open(file_path, 'r', encoding="utf8") as f:
            data = json.loads(f.read())

            for voivodeship in data:

                assert isinstance(voivodeship, dict), "element is not a dict"
                voivodeship = voivodeship['name']

                try:

                    assert isinstance(voivodeship, str), f"{voivodeship} is not a string"
                    obj, created = self.voivodeships_model.objects.get_or_create(
                        name=voivodeship
                    )

                    if created:
                        print(f'voivodeship {voivodeship} has been added')
                    else:
                        print(f'voivodeship {voivodeship} already exists in database')

                except Exception as e:
                    print(f'{voivodeship}', e)
