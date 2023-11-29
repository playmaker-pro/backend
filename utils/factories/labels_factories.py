import factory
from django.utils import timezone

from labels.models import Label, LabelDefinition
from utils.factories.consts import *


class LabelDefinitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LabelDefinition

    label_name = factory.Sequence(lambda n: f"Label{n}")
    label_description = "Sample description"
    icon = "sample_icon.png"
    conditions = "Sample conditions"


class LabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Label

    label_definition = factory.SubFactory(LabelDefinitionFactory)
    season_name = factory.Iterator(SEASON_NAMES)
    league = factory.Iterator(LEAGUE_NAMES)
    team = factory.Iterator(TEAM_NAMES)
    season_round = factory.Iterator(ROUND_NAMES)
    visible = True

    start_date = factory.LazyFunction(timezone.now)
    end_date = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(days=30)
    )

    visible_on_profile = True
    visible_on_base = True
    visible_on_main_page = True
