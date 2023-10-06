from .api_request_factory import *
from .base import CustomObjectFactory
from .cities_factories import *
from .clubs_factories import *
from .mapper_factories import *
from .profiles_factories import *
from .user_factories import *

NAME_TO_FACTORY_MAPPER = {
    "User": UserFactory,
    "PlayerProfile": PlayerProfileFactory,
    "CoachProfile": CoachProfileFactory,
    "ClubProfile": ClubProfileFactory,
    "ScoutProfile": ScoutProfileFactory,
    "GuestProfile": GuestProfileFactory,
    "Club": ClubFactory,
    "Team": TeamFactory,
    "League": LeagueFactory,
    "Season": SeasonFactory,
    "TeamHistory": TeamHistoryFactory,
    "LeagueHistory": LeagueHistoryFactory,
}
