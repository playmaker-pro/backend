import random

import pytest
from django.utils.text import slugify
from faker import Faker

from profiles import models
from profiles.services import TransferStatusService
from roles import definitions
from utils.factories.profiles_factories import (
    ClubProfileFactory,
    CoachProfileFactory,
    GuestProfileFactory,
    ManagerProfileFactory,
    PlayerProfileFactory,
    ScoutProfileFactory,
)

from .utils import get_random_bool, get_random_date, get_random_int

fake = Faker(locale="pl_PL")


@pytest.fixture
def player_position():
    """Create a player position instance."""
    position_count = models.PlayerPosition.objects.count()
    return models.PlayerPosition.objects.create(name=f"position_{position_count}")


@pytest.fixture
def profile_video(player_profile):
    """Create a profile video instance."""
    return models.ProfileVideo.objects.create(
        profile=player_profile,
        url=fake.url(),
        title=fake.sentence(),
    )


@pytest.fixture
def player_profile_position(player_profile, player_position):
    """Create a player profile position instance."""
    return models.PlayerProfilePosition.objects.get_or_create(
        player_profile=player_profile, player_position=player_position
    )[0]


@pytest.fixture
def verification_stage():
    """Create a verification stage instance."""
    return models.VerificationStage.objects.create(done=get_random_bool())


@pytest.fixture
def player_metrics(player_profile):
    """Create player metrics instance."""
    metrics = player_profile.playermetrics
    metrics.games_summary = {"games": "summary"}
    metrics.season_summary = {"season": "summary"}
    metrics.pm_score = get_random_int(0, 100)
    metrics.season_score = {
        "2022/2023": 67,
        "2023/2024": 45,
    }
    metrics.save()
    return metrics


@pytest.fixture
def player_profile(unique_user, mapper, team, team_history, verification_stage):
    """Create a player profile instance."""
    yield PlayerProfileFactory.create()


@pytest.fixture
def player_profile_with_language(player_profile):
    """Create a player profile with specific languages."""
    language_codes = ["pl", "en"]
    languages = models.Language.objects.filter(code__in=language_codes)
    player_profile.user.userpreferences.spoken_languages.set(languages)
    return player_profile


@pytest.fixture
def player_profile_with_empty_metrics(player_profile):
    """Create a player profile with empty metrics."""
    player_profile.playermetrics.wipe_metrics()
    return player_profile


@pytest.fixture
def player_profile_with_specific_metrics(player_profile, pm_score=75):
    """Create a player profile with specific metrics score."""
    player_metrics = player_profile.playermetrics
    player_metrics.pm_score = pm_score
    player_metrics.save()
    return player_profile


@pytest.fixture
def coach_profile(unique_user, mapper, team, team_history):
    """Create a coach profile instance."""
    yield CoachProfileFactory.create()


@pytest.fixture
def club_profile(unique_user, team, club):
    """Create a club profile instance."""
    yield ClubProfileFactory.create()


@pytest.fixture
def scout_profile():
    """Create a scout profile instance."""
    yield ScoutProfileFactory.create()


@pytest.fixture
def manager_profile(unique_user):
    """Create a manager profile instance."""
    yield ManagerProfileFactory.create()


@pytest.fixture
def guest_profile():
    """Create a guest profile instance."""
    yield GuestProfileFactory.create()


@pytest.fixture
def position():
    """Create a player position instance."""
    positions = ["Napastnik", "Skrzydłowy", "Obrońca prawy", "Bramkarz"]
    position_name = random.choice(positions)
    return models.PlayerPosition.objects.get_or_create(name=position_name)[0]


@pytest.fixture
def licence_type():
    """Create a licence type instance."""
    counter = models.LicenceType.objects.count() + 1
    return models.LicenceType.objects.create(
        name=f"licence_{counter}", order=100 + counter
    )


@pytest.fixture
def coach_licence(licence_type, user):
    """Create a coach licence instance."""
    return models.CoachLicence.objects.create(
        licence=licence_type,
        expiry_date=get_random_date(start_date="-15y", end_date="today"),
        owner=user,
        is_in_progress=get_random_bool(),
        release_year=get_random_int(2000, 2021),
    )


@pytest.fixture
def course(user):
    """Create a course instance."""
    counter = models.Course.objects.count() + 1
    return models.Course.objects.create(
        name=f"course_{counter}", release_year=get_random_int(2000, 2021), owner=user
    )


@pytest.fixture
def language():
    """Create a language instance."""
    languages = ["Polski", "Angielski", "Niemiecki", "Francuski"]
    language_name = random.choice(languages)
    return models.Language.objects.get_or_create(name=language_name)[0]


@pytest.fixture
def team_contributor(player_profile, team):
    """Create a team contributor instance."""
    contributor = models.TeamContributor.objects.create(
        profile_uuid=player_profile.uuid, is_primary=False
    )
    contributor.team_history.add(team)
    return contributor


@pytest.fixture
def transfer_status(player_profile=None):
    """Create a transfer status instance."""
    if not player_profile:
        player_profile = pytest.fixture("player_profile")()

    additional_info_choices = [
        info[0] for info in definitions.TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES
    ]
    training_choices = [
        training[0] for training in definitions.TRANSFER_TRAININGS_CHOICES
    ]
    salary_choices = [salary[0] for salary in definitions.TRANSFER_SALARY_CHOICES]

    data = {
        "status": 1,
        "additional_info": [random.choice(additional_info_choices)],
        "number_of_trainings": random.choice(training_choices),
        "salary": random.choice(salary_choices),
    }

    data = TransferStatusService.prepare_generic_type_content(data, player_profile)

    status = models.ProfileTransferStatus.objects.create(**data)

    return status


@pytest.fixture
def transfer_request(team_contributor, player_profile=None):
    """Create a transfer request instance."""
    if not player_profile:
        player_profile = pytest.fixture("player_profile")()

    # Setup required data
    data = {
        "status": "1",
        "benefits": [1, 2],
        "requesting_team": team_contributor,
        "gender": "M",
        "number_of_trainings": "1",
        "salary": "1",
    }

    # Apply generic content preparation
    data = TransferStatusService.prepare_generic_type_content(data, player_profile)

    # Create the instance
    request = models.ProfileTransferRequest.objects.create(**data)

    # Add positions
    positions = models.PlayerPosition.objects.all()[:2]
    if positions:
        for position in positions:
            request.position.add(position.pk)

    return request


@pytest.fixture
def catalog():
    """Create a catalog instance."""
    counter = models.Catalog.objects.count() + 1
    name = f"Catalog {counter}"
    return models.Catalog.objects.create(
        name=name, slug=slugify(name), description="Sample catalog description"
    )
