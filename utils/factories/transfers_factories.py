import random

import factory

from profiles.models import PlayerPosition
from roles import definitions
from transfers import models
from utils.factories.base import CustomObjectFactory
from utils.factories.profiles_factories import TeamContributorFactory


class TransferStatusFactory(CustomObjectFactory):
    """Transfer status factory"""

    class Meta:
        model = models.ProfileTransferStatus

    status = 1
    additional_info = factory.List(
        [
            factory.Iterator(
                [
                    info[0]
                    for info in definitions.TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES
                ]
            )
        ]
    )
    number_of_trainings = factory.Iterator(
        [training[0] for training in definitions.TRANSFER_TRAININGS_CHOICES]
    )
    salary = factory.Iterator(
        [salary[0] for salary in definitions.TRANSFER_SALARY_CHOICES]
    )
    meta = factory.SubFactory("utils.factories.profiles_factories.ProfileMetaFactory")

    class Params:
        profile = None
        league = factory.List([])

    # @classmethod
    # def create(cls, **kwargs) -> models.PROFILE_TYPE:
    #     """Override for GenericForeignKey and ManyToMany fields handling."""
    #     leagues = kwargs.pop(
    #         "leagues", None
    #     )  # Extract leagues before instance creation
    #     profile = kwargs.pop("profile", None)

    #     if not profile:
    #         profile = PlayerProfileFactory.create()

    #     kwargs = TransferStatusService.prepare_generic_type_content(kwargs, profile)
    #     transfer_status_instance = super().create(**kwargs)  # Create the instance

    #     # Set the leagues using the set method, if leagues are provided
    #     if leagues is not None:
    #         transfer_status_instance.league.set(leagues)

    #     return transfer_status_instance


class TransferRequestFactory(CustomObjectFactory):
    """Transfer status factory"""

    class Meta:
        model = models.ProfileTransferRequest

    status = "1"
    benefits = [1, 2]
    requesting_team = factory.SubFactory(TeamContributorFactory)
    gender = "M"
    number_of_trainings = "1"
    salary = "1"
    meta = factory.SubFactory("utils.factories.profiles_factories.ProfileMetaFactory")

    class Params:
        profile = None

    # @classmethod
    # def create(cls, **kwargs) -> models.PROFILE_TYPE:
    #     """Override for GenericForeignKey purposes."""
    #     if not kwargs.get("profile"):
    #         profile = PlayerProfileFactory.create()
    #     else:
    #         profile = kwargs.pop("profile")
    #     kwargs = TransferStatusService.prepare_generic_type_content(kwargs, profile)
    #     return super().create(**kwargs)

    @factory.post_generation
    def position(self, create, extracted, **kwargs):  # noqa
        if not create:
            return
        if not self.position.all().exists():  # noqa
            positions = PlayerPosition.objects.all()
            random_positions = random.sample(list(positions), 2)
            for random_position in random_positions:
                self.position.add(random_position.pk)  # noqa
