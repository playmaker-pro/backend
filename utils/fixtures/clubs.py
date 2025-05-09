import random

import pytest

from clubs import models

from .utils import fake


@pytest.fixture
def league():
    """Create a league instance."""
    return models.League.objects.create(
        name=fake.company(),
    )


@pytest.fixture
def team(league, club):
    """Create a team instance."""
    return models.Team.objects.create(
        name=fake.company(),
        league=league,
        club=club,
    )


@pytest.fixture
def club():
    """Create a club instance."""
    return models.Club.objects.create(
        name=fake.company(),
    )


@pytest.fixture
def season():
    """Create a season instance."""
    return models.Season.objects.get_or_create(
        name=random.choice(["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
    )[0]


@pytest.fixture
def team_history(team, season):
    """Create a team history instance."""
    return models.TeamHistory.objects.create(
        team=team,
        season=season,
    )
