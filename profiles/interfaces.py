from datetime import datetime
from typing import TYPE_CHECKING, Protocol, Union

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from roles.definitions import ProfileDataScore

if TYPE_CHECKING:
    from profiles.models import BaseProfile


User = get_user_model()


class FulfillScoreProtocol(Protocol):
    """Protocol for data scoring."""

    @staticmethod
    def data_fulfill_level(obj: "BaseProfile") -> ProfileDataScore:
        raise NotImplementedError


class ProfileVisitHistoryProtocol(Protocol):
    """Protocol for profile visit history. Implements required methods."""

    def increment(self, requestor: Union["BaseProfile", AnonymousUser]) -> None:
        """Increment the visit count for the given profile."""

    @property
    def total_visits(self) -> int:
        """Return the total number of visits."""

    @staticmethod
    def total_visits_from_range(date: datetime, user: User) -> int:
        """Return the total number of visits from a given date."""
