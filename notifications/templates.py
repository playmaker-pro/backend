from enum import Enum


class NotificationTemplate(Enum):
    CHECK_TRIAL = {
        "title": "Skorzystaj z wersji próbnej Premium",
        "description": "Wypróbuj 3 dni premium za darmo!",
        "href": "/premium",
    }

    GO_PREMIUM = {
        "title": "Przejdź na Premium",
        "description": "Sprawdź wszystkie możliwości i zyskaj przewagę!",
        "href": "/premium",
    }

    VERIFY_PROFILE = {
        "title": "Zweryfikuj swój profil",
        "description": "Dodaj linki do profili piłkarskich i zweryfikuj swój profil.",
        "href": "/ustawienia",
    }

    PROFILE_HIDDEN = {
        "title": "Profil tymczasowo ukryty",
        "description": "Popraw informacje w profilu (imię, nazwisko, zdjęcie), aby przywrócić widoczność.",
        "href": "/profil",
    }

    BUY_PREMIUM = {
        "title": "Twoje konto Premium wygasło!",
        "description": "Nie czekaj – wróć do PREMIUM i korzystaj ze wszystkich funkcji!",
        "href": "/premium",
    }

    PM_RANK = {
        "title": "Ranking PM",
        "description": "Sprawdź, kto ma najwyższy PM Score w tym miesiacu",
        "href": "/premium",
    }

    VISITS_SUMMARY = {
        "title": "Już {visited_by_count} osób wyświetliło Twój profil!",
        "description": "Kliknij tutaj, aby zobaczyc kto to.",
        "href": "/wyswietlenia",
    }

    WELCOME = {
        "title": "Witaj w PlayMaker!",
        "description": "Dziękujemy za dołączenie do społeczności, Twoja podróż zaczyna się tutaj! Sprawdź, co daje Ci PlayMaker!",
        "href": "/TODO",
    }

    NEW_FOLLOWER = {
        "title": "Ktoś Cię obserwuje",
        "description": "Zobacz kto zaobserwował Twój profil.",
        "href": "/obserowani",
    }

    INQUIRY_ACCEPTED = {
        "title": "{profile} zaakceptował twoje zaproszenie.",
        "description": "Kliknij, aby sprawdzic odpowiedz.",
        "href": "/kontakty?tab=kontakty",
    }

    INQUIRY_REJECTED = {
        "title": "{profile} odrzucił twoje zaproszenie.",
        "description": "Kliknij, aby sprawdzic odpowiedz.",
        "href": "/kontakty?tab=zapytania",
    }

    INQUIRY_READ = {
        "title": "{profile} odczytał twoje zaproszenie.",
        "description": "Kliknij, aby sprawdzic odpowiedz.",
        "href": "/kontakty",
    }

    PROFILE_VISITED = {
        "title": "Wyświetlono twój profil",
        "description": "Kliknij tutaj, aby zobaczyc kto to.",
        "href": "/wyswietlenia",
    }

    SET_TRANSFER_REQUESTS = {
        "title": "Ustaw zapotrzebowanie transferowe!",
        "description": "Kliknij tutaj, aby ustawic swoje zapotrzebowanie.",
        "href": "/profil",
    }

    SET_STATUS = {
        "title": "Ustaw status transferowy",
        "description": "Kliknij tutaj, aby ustawic swój status.",
        "href": "/profil",
    }

    INVITE_FRIENDS = {
        "title": "Zaproś znajomych",
        "description": "Zapraszaj i wygrywaj nagrody!",
        "href": "/moje-konto/zapros",
    }

    ADD_LINKS = {
        "title": "Dodaj linki",
        "description": "Kliknij tutaj, aby przejść do profilu.",
        "href": "/profil",
    }

    ADD_VIDEO = {
        "title": "Dodaj video",
        "description": "Kliknij tutaj, aby przejść do profilu.",
        "href": "/profil",
    }

    ASSIGN_CLUB = {
        "title": "Dodaj aktualną drużynę",
        "description": "Kliknij tutaj, aby przejść do profilu.",
        "href": "/profil",
    }

    NEW_INQUIRY = {
        "title": "Otrzymałeś/aś nowe zapytanie",
        "description": "{profil} wysłał Ci zapytanie o kontakt.",
        "href": "/kontakty?tab=zapytania",
    }
