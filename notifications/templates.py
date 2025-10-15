"""
Module for defining notification templates.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from django.utils import translation
from django.utils.translation import gettext_lazy as _


@dataclass
class NotificationBody:
    title: str
    description: str
    href: str
    template_name: Optional[str] = None
    icon: Optional[str] = None
    picture: Optional[str] = None
    picture_profile_role: Optional[str] = None

    kwargs: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Post-initialization - store unformatted templates for proper translation.
        For backward compatibility, we still need formatted versions for legacy notifications.
        """
        # Store unformatted templates in Polish for proper translation later
        with translation.override("pl"):
            self.formatted_title = str(self.title)  # Store template, not formatted text
            self.formatted_description = str(
                self.description
            )  # Store template, not formatted text

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the notification body to a dictionary.
        Store unformatted templates in the database for proper translation.
        """
        result = {
            "title": self.formatted_title,  # Store unformatted template
            "description": self.formatted_description,  # Store unformatted template
            "href": self.href,
            "template_name": self.template_name,
            "template_params": self.kwargs,  # Store parameters separately
            "icon": self.icon,
            "picture": self.picture,
            "picture_profile_role": self.picture_profile_role,
        }
        return result


class NotificationTemplate(Enum):
    CONFIRM_EMAIL = {
        "title": _("Potwierdź swój adres email"),
        "description": _(
            "Twój adres email nie został przez Ciebie potwierdzony."
            "Upewnij się, czy adres jest poprawny i potwierdź go."
        ),
        "href": "/ustawienia",
        "icon": "playmaker",
    }
    CHECK_TRIAL = {
        "title": _("Skorzystaj z wersji próbnej Premium"),
        "description": _("Wypróbuj 3 dni premium za darmo!"),
        "href": "/premium",
        "icon": "premium",
    }
    GO_PREMIUM = {
        "title": _("Przejdź na Premium"),
        "description": _("Sprawdź wszystkie możliwości i zyskaj przewagę!"),
        "href": "/premium",
        "icon": "premium",
    }
    VERIFY_PROFILE = {
        "title": _("Zweryfikuj swój profil"),
        "description": _(
            "Dodaj linki do profili piłkarskich i zweryfikuj swój profil."
        ),
        "href": "/ustawienia",
        "icon": "links",
    }
    PROFILE_HIDDEN = {
        "title": _("Profil tymczasowo ukryty"),
        "description": _(
            "Popraw informacje w profilu (imię, nazwisko, zdjęcie), aby przywrócić widoczność."
        ),
        "href": "?modal=profile-hidden",
        "icon": "hidden",
    }
    PREMIUM_EXPIRED = {
        "title": _("Twoje konto Premium wygasło!"),
        "description": _(
            "Nie czekaj – wróć do PREMIUM i korzystaj ze wszystkich funkcji!"
        ),
        "href": "/premium",
        "icon": "premium",
    }
    PM_RANK = {
        "title": _("Ranking PM"),
        "description": _("Sprawdź, kto ma najwyższy PM Score w tym miesiacu"),
        "href": "/premium",
        "icon": "pm-rank",
    }
    VISITS_SUMMARY = {
        "title": _("Już {visited_by_count} osób wyświetliło Twój profil!"),
        "description": _("Kliknij tutaj, aby zobaczyc kto to."),
        "href": "/wyswietlenia",
        "icon": "eye",
    }
    WELCOME = {
        "title": _("Witaj w PlayMaker!"),
        "description": _(
            "Dziękujemy za dołączenie do społeczności, Twoja podróż zaczyna się tutaj! Sprawdź, co daje Ci PlayMaker!"
        ),
        "href": "?modal=welcome",
        "icon": "playmaker",
    }
    NEW_FOLLOWER = {
        "title": _("Ktoś Cię obserwuje"),
        "description": _("Zobacz kto zaobserwował Twój profil."),
        "href": "/obserwowani?tab=obserwatorzy",
        "icon": "star",
    }
    INQUIRY_ACCEPTED = {
        "title": _("{profile} zaakceptował twoje zaproszenie."),
        "description": _("Kliknij, aby sprawdzic odpowiedz."),
        "href": "/kontakty?tab=kontakty",
        "icon": "inquiry-accepted",
    }
    INQUIRY_REJECTED = {
        "title": _("{profile} odrzucił twoje zaproszenie."),
        "description": _("Kliknij, aby sprawdzic odpowiedz."),
        "href": "/kontakty?tab=zapytania&subtab=wyslane",
        "icon": "inquiry-rejected",
    }
    INQUIRY_READ = {
        "title": _("{profile} odczytał twoje zaproszenie."),
        "description": _("Kliknij, aby sprawdzic odpowiedz."),
        "href": "/kontakty?tab=zapytania&subtab=wyslane",
        "icon": "inquiry",
    }
    PROFILE_VISITED = {
        "title": _("Wyświetlono twój profil"),
        "description": _("Kliknij tutaj, aby zobaczyc kto to."),
        "href": "/wyswietlenia",
        "icon": "eye",
    }
    SET_TRANSFER_REQUESTS = {
        "title": _("Ustaw zapotrzebowanie transferowe!"),
        "description": _("Kliknij tutaj, aby ustawic swoje zapotrzebowanie."),
        "href": "/profil",
        "icon": "transfer",
    }
    SET_STATUS = {
        "title": _("Ustaw status transferowy"),
        "description": _("Kliknij tutaj, aby ustawic swój status."),
        "href": "/profil",
        "icon": "transfer",
    }
    INVITE_FRIENDS = {
        "title": _("Zaproś znajomych"),
        "description": _("Zapraszaj i wygrywaj nagrody!"),
        "href": "/moje-konto/zapros",
        "icon": "send",
    }
    ADD_LINKS = {
        "title": _("Dodaj linki"),
        "description": _("Kliknij tutaj, aby przejść do profilu."),
        "href": "/profil#sekcja-linki",
        "icon": "links",
    }
    ADD_VIDEO = {
        "title": _("Dodaj video"),
        "description": _("Kliknij tutaj, aby przejść do profilu."),
        "href": "/profil#sekcja-video-z-gry",
        "icon": "video",
    }
    ASSIGN_CLUB = {
        "title": _("Dodaj aktualną drużynę"),
        "description": _("Kliknij tutaj, aby przejść do profilu."),
        "href": "/profil#sekcja-kariera",
        "icon": "club",
    }
    NEW_INQUIRY = {
        "title": _("Otrzymałeś/aś nowe zapytanie"),
        "description": _("{profile} wysłał Ci zapytanie o kontakt."),
        "href": "/kontakty?tab=zapytania",
        "icon": "inquiry",
    }
    PROFILE_VERIFIED = {
        "title": _("Twój profil został zweryfikowany!"),
        "description": _(
            "Potwierdziliśmy Twoją tożsamość. Korzystaj z PLAYMAKER.pro bez ograniczeń!"
        ),
        "href": "/profil",
        "icon": "success",
    }

    TEST = {
        "title": _("Test"),
        "description": _("Test"),
        "href": "/",
        "icon": "test",
    }
