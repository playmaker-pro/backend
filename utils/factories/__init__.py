from .api_request_factory import *
from .cities_factories import *
from .clubs_factories import *
from .external_links_factories import *
from .inquiry_factories import *
from .labels_factories import *
from .mapper_factories import *
from .payment_factories import *
from .premium_factories import *
from .profiles_factories import *
from .user_factories import *
from .transfers_factories import *


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
