import random

from factory import Factory, post_generation

from profiles.models import PlayerPosition
from roles import definitions
from transfers import models
from utils.factories.profiles_factories import TeamContributorFactory

# from . import PlayerProfileFactory

factory = Factory()


class TransferStatusFactory(factory.django.DjangoModelFactory):
    """Transfer status factory"""

    class Meta:
        model = models.ProfileTransferStatus

    status = 1
    additional_info = factory.List([
        factory.Iterator([
            info[0] for info in definitions.TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES
        ])
    ])
    number_of_trainings = factory.Iterator([
        training[0] for training in definitions.TRANSFER_TRAININGS_CHOICES
    ])
    salary = factory.Iterator([
        salary[0] for salary in definitions.TRANSFER_SALARY_CHOICES
    ])

    class Params:
        profile = None
        leagues = factory.List([])

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


class TransferRequestFactory(factory.django.DjangoModelFactory):
    """Transfer status factory"""

    class Meta:
        model = models.ProfileTransferRequest

    status = "1"
    benefits = [1, 2]
    requesting_team = factory.SubFactory(TeamContributorFactory)
    gender = "M"
    number_of_trainings = "1"
    salary = "1"

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

    @post_generation
    def position(self, create, extracted, **kwargs):  # noqa
        if not create:
            return
        if not self.position.all().exists():  # noqa
            positions = PlayerPosition.objects.all()
            random_positions = random.sample(list(positions), 2)
            for random_position in random_positions:
                self.position.add(random_position.pk)  # noqa
