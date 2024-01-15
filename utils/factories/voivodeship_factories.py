import factory.fuzzy

from voivodeships.models import Voivodeships


class VoivodeshipsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Voivodeships

    name = factory.Faker("name")
    code = factory.fuzzy.FuzzyInteger(1, 10)
