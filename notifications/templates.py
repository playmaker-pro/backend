"""
Module for defining notification templates.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


@dataclass
class NotificationBody:
    title: str
    description: str
    href: str
    template_name: str = None
    icon: Optional[str] = None
    picture: Optional[str] = None
    picture_profile_role: Optional[str] = None

    kwargs: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Post-initialization to set the notification body attrs based on the kwargs.
        """
        self.title = self.title.format(**self.kwargs)
        self.description = self.description.format(**self.kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the notification body to a dictionary.
        """
        return {
            "title": self.title,
            "description": self.description,
            "href": self.href,
            "template_name": self.template_name,
            "icon": self.icon,
            "picture": self.picture,
            "picture_profile_role": self.picture_profile_role,
        }


class NotificationTemplate(Enum):
    CHECK_TRIAL = {
        "title": "Skorzystaj z wersji próbnej Premium",
        "description": "Wypróbuj 3 dni premium za darmo!",
        "href": "/premium",
        "icon": "premium",
    }
    GO_PREMIUM = {
        "title": "Przejdź na Premium",
        "description": "Sprawdź wszystkie możliwości i zyskaj przewagę!",
        "href": "/premium",
        "icon": "premium",
    }
    VERIFY_PROFILE = {
        "title": "Zweryfikuj swój profil",
        "description": "Dodaj linki do profili piłkarskich i zweryfikuj swój profil.",
        "href": "/ustawienia",
        "icon": "links",
    }
    PROFILE_HIDDEN = {
        "title": "Profil tymczasowo ukryty",
        "description": "Popraw informacje w profilu (imię, nazwisko, zdjęcie), aby przywrócić widoczność.",
        "href": "?modal=profile-hidden",
        "icon": "hidden",
    }
    PREMIUM_EXPIRED = {
        "title": "Twoje konto Premium wygasło!",
        "description": "Nie czekaj – wróć do PREMIUM i korzystaj ze wszystkich funkcji!",
        "href": "/premium",
        "icon": "premium",
    }
    PM_RANK = {
        "title": "Ranking PM",
        "description": "Sprawdź, kto ma najwyższy PM Score w tym miesiacu",
        "href": "/premium",
        "icon": "pm-rank",
    }
    VISITS_SUMMARY = {
        "title": "Już {visited_by_count} osób wyświetliło Twój profil!",
        "description": "Kliknij tutaj, aby zobaczyc kto to.",
        "href": "/wyswietlenia",
        "icon": "eye",
    }
    WELCOME = {
        "title": "Witaj w PlayMaker!",
        "description": "Dziękujemy za dołączenie do społeczności, Twoja podróż zaczyna się tutaj! Sprawdź, co daje Ci PlayMaker!",
        "href": "?modal=welcome",
        "icon": "playmaker",
    }
    NEW_FOLLOWER = {
        "title": "Ktoś Cię obserwuje",
        "description": "Zobacz kto zaobserwował Twój profil.",
        "href": "/obserwowani?tab=obserwatorzy",
        "icon": "star",
    }
    INQUIRY_ACCEPTED = {
        "title": "{profile} zaakceptował twoje zaproszenie.",
        "description": "Kliknij, aby sprawdzic odpowiedz.",
        "href": "/kontakty?tab=kontakty",
        "icon": "inquiry-accepted",
    }
    INQUIRY_REJECTED = {
        "title": "{profile} odrzucił twoje zaproszenie.",
        "description": "Kliknij, aby sprawdzic odpowiedz.",
        "href": "/kontakty?tab=zapytania&subtab=wyslane",
        "icon": "inquiry-rejected",
    }
    INQUIRY_READ = {
        "title": "{profile} odczytał twoje zaproszenie.",
        "description": "Kliknij, aby sprawdzic odpowiedz.",
        "href": "/kontakty?tab=zapytania&subtab=wyslane",
        "icon": "inquiry",
    }
    PROFILE_VISITED = {
        "title": "Wyświetlono twój profil",
        "description": "Kliknij tutaj, aby zobaczyc kto to.",
        "href": "/wyswietlenia",
        "icon": "eye",
    }
    SET_TRANSFER_REQUESTS = {
        "title": "Ustaw zapotrzebowanie transferowe!",
        "description": "Kliknij tutaj, aby ustawic swoje zapotrzebowanie.",
        "href": "/profil",
        "icon": "transfer",
    }
    SET_STATUS = {
        "title": "Ustaw status transferowy",
        "description": "Kliknij tutaj, aby ustawic swój status.",
        "href": "/profil",
        "icon": "transfer",
    }
    INVITE_FRIENDS = {
        "title": "Zaproś znajomych",
        "description": "Zapraszaj i wygrywaj nagrody!",
        "href": "/moje-konto/zapros",
        "icon": "send",
    }
    ADD_LINKS = {
        "title": "Dodaj linki",
        "description": "Kliknij tutaj, aby przejść do profilu.",
        "href": "/profil#sekcja-linki",
        "icon": "links",
    }
    ADD_VIDEO = {
        "title": "Dodaj video",
        "description": "Kliknij tutaj, aby przejść do profilu.",
        "href": "/profil#sekcja-video-z-gry",
        "icon": "video",
    }
    ASSIGN_CLUB = {
        "title": "Dodaj aktualną drużynę",
        "description": "Kliknij tutaj, aby przejść do profilu.",
        "href": "/profil#sekcja-kariera",
        "icon": "club",
    }
    NEW_INQUIRY = {
        "title": "Otrzymałeś/aś nowe zapytanie",
        "description": "{profile} wysłał Ci zapytanie o kontakt.",
        "href": "/kontakty?tab=zapytania",
        "icon": "inquiry",
    }
    PROFILE_VERIFIED = {
        "title": "Twój profil został zweryfikowany!",
        "description": "Potwierdziliśmy Twoją tożsamość. Korzystaj z PLAYMAKER.pro bez ograniczeń!",
        "href": "/profil",
        "icon": "success",
    }

    TEST = {
        "title": "Test",
        "description": "Test",
        "href": "/",
        "icon": "test",
    }
