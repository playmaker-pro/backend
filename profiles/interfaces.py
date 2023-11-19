from typing import TYPE_CHECKING, Protocol

from roles.definitions import ProfileDataScore

if TYPE_CHECKING:
    from profiles.models import BaseProfile


class FulfillScoreProtocol(Protocol):
    """Protocol for data scoring."""

    @staticmethod
    def data_fulfill_level(obj: "BaseProfile") -> ProfileDataScore:
        raise NotImplementedError
