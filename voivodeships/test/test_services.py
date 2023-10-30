import json
import tempfile

from django.test import TestCase

from utils import testutils as utils
from utils.factories import PlayerProfileFactory
from voivodeships.models import Voivodeships
from voivodeships.services import VoivodeshipService


class TestVoivodeshipService(TestCase):
    def setUp(self) -> None:
        utils.create_system_user()
        self.voivodeship_data = {"name": "Warmińsko-Mazurskie"}

        self.voivodeship, _ = Voivodeships.objects.get_or_create(
            **self.voivodeship_data
        )
        self.manager = VoivodeshipService()
        self.user_data = {
            "user__password": "super_secret_password",
            "user__email": "test_user@test.com",
        }

        self.user = PlayerProfileFactory.create(**self.user_data).user

        self.user.profile.voivodeship_obj = self.voivodeship
        self.user.profile.save()

    def test_choices(self) -> None:
        """test voivodeship_choices method"""

        choices = self.manager.voivodeship_choices

        self.assertIsInstance(choices, tuple)
        for element in choices:
            self.assertIsInstance(element, tuple)

        self.assertEqual(choices[0][0], self.voivodeship_data["name"])
        self.assertEqual(choices[0][1], self.voivodeship_data["name"])
        self.assertEqual(len(choices), 1)

    def test_display_voivodeship(self) -> None:
        """test voivodeship_display method"""

        voivodeship = self.manager.display_voivodeship(self.user.profile)

        self.assertIsInstance(voivodeship, Voivodeships)
        self.assertEqual(voivodeship.name, self.voivodeship.name)

    def test_get_voivodeship_by_name(self) -> None:
        """test get_voivodeship_by_name method"""

        voivodeship = self.manager.get_voivodeship_by_name(
            self.voivodeship_data["name"]
        )

        self.assertEqual(len(voivodeship), 1)
        self.assertIsInstance(voivodeship[0], Voivodeships)
        self.assertEqual(voivodeship[0].name, self.voivodeship.name)

    def test_get_voivodeship_by_different_name(self) -> None:
        """test get_voivodeship_by_name method when giving different string"""

        second_vivo, _ = Voivodeships.objects.get_or_create(name="Kujawsko-pomorskie")
        voivodeship = self.manager.get_voivodeship_by_name("Warmińsko-Mazurskie")

        self.assertEqual(len(voivodeship), 1)
        self.assertIsInstance(voivodeship[0], Voivodeships)
        self.assertEqual(voivodeship[0].name, self.voivodeship_data["name"])

        voivodeship = self.manager.get_voivodeship_by_name("Kujawsko-pomorskie")

        self.assertIsInstance(voivodeship[0], Voivodeships)
        self.assertEqual(voivodeship[0].name, second_vivo.name)

    def test_get_voivodeship_by_invalid_name(self) -> None:
        """test get_voivodeship_by_name method when giving invalid vivodeship name"""

        voivodeship = self.manager.get_voivodeship_by_name("invalid_name")
        self.assertEqual(len(voivodeship), 0)

    def test_get_voivodeship(self) -> None:
        """test get_voivodeship method. Returning queryset with all voivodeships"""

        Voivodeships.objects.get_or_create(name="Kujawsko-pomorskie")
        Voivodeships.objects.get_or_create(name="Małopolskie")
        Voivodeships.objects.get_or_create(name="Mazowieckie")
        qry = self.manager.get_voivodeships

        self.assertEqual(len(qry), 4)
        self.assertIsInstance(qry[0], Voivodeships)

    def test_save_to_db(self) -> None:
        """test get_voivodeship method. Returning queryset with all voivodeships"""

        tmp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)

        json_data = [{"name": "Dolnośląskie"}, {"name": "Kujawsko-pomorskie"}]

        with open(tmp_file.name, "w") as f:
            f.write(json.dumps(json_data))

        self.manager.save_to_db(tmp_file.name)
        all_vivos = Voivodeships.objects.all()

        self.assertEqual(len(all_vivos), 3)

        first_voivodeship = Voivodeships.objects.filter(name=json_data[0]["name"])

        self.assertTrue(first_voivodeship.exists())
