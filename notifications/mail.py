import logging

from django.conf import settings
from django.core.mail import mail_managers, send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)


def notify_error_admins(subject="Wystąpił błąd", message=""):
    mail_managers(subject, message)


def build_absolute_url(uri: str) -> str:
    url = f"{settings.BASE_URL}{uri}"
    return url


def add_footer(body):
    body += "Pozdrawiamy, \n" "Zespół PlayMaker.pro"
    return body


absurl = build_absolute_url


def announcement_notify_club_player(announcement, player):
    subject = "Dostałeś odpowiedź na Twoje ogłoszenie"
    body = f"Piłkarz {player.first_name} {player.last_name} jest zainteresowany testami w Twoim klubie.\n"
    body += f"Jeśli jego CV jest dla Ciebie interesujące, skontaktuj się z nim\n\n"
    body += f"Email: {player.email}\n"
    if player.profile.phone:
        body += f"Telefon: {player.profile.phone}:\n"
    body += f"Link do profilu: {absurl(player.profile.get_permalink())}\n\n"
    body = add_footer(body)

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [announcement.creator.email])


def announcement_notify_club_coach(announcement, coach):
    subject = "Dostałeś odpowiedź na Twoje ogłoszenie o pracy"
    body = f"Trener {coach.first_name} {coach.last_name} chce wziąć udział w rekrutacji na stanowisko trenera.\n"
    body += f"Jeśli jesteś zainteresowany, skontaktuj się:\n\n"
    body += f"Email: {coach.email}\n"
    if coach.profile.phone:
        body += f"Telefon: {coach.profile.phone}:\n"
    body += f"Link do profilu: {absurl(coach.profile.get_permalink())}\n\n"
    body = add_footer(body)

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [announcement.creator.email])


def announcement_notify_player(announcement, inviter):
    subject = "Dostałeś odpowiedź na Twoje ogłoszenie"
    if inviter.declared_role == "T":  # if inviter is a Coach
        body = f"Klub {inviter.coachprofile.display_club} chce Cię zaprosić na testy!\n"
        body += f"Jeśli jesteś zainteresowany, skontaktuj się: \n\n"
        body += f"Email trenera: {inviter.coachprofile.user.email}\n"  # or coach's email if coach exists
        if phone := inviter.profile.phone:
            body += f"Telefon trenera: {phone}:\n"
        body += f"Link do profilu trenera: {absurl(inviter.coachprofile.get_permalink())}\n\n"

    else:  # if inviter is a Club
        body = f"Klub {inviter.clubprofile.display_club} chce Cię zaprosić na testy!\n"
        body += f"Jeśli jesteś zainteresowany, skontaktuj się: \n\n"
        body += f"Email: {inviter.clubprofile.user.email}\n"
        body += f"Link do profilu: {absurl(inviter.clubprofile.club_object.get_permalink())}\n\n"

    body = add_footer(body)

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [announcement.creator.email])


def announcement_notify_coach(announcement, club):
    subject = "Dostałeś odpowiedź na Twoje ogłoszenie"
    body = (
        f"Klub {club.clubprofile.display_club} chce Cię zaprosić na rozmowę o pracę!\n"
    )
    body += f"Jeśli jesteś zainteresowany, skontaktuj się: \n\n"
    body += f"Email: {club.clubprofile.user.email}\n"
    if club.clubprofile.phone:
        body += f"Telefon: {club.clubprofile.phone}:\n"
    body += (
        f"Link do profilu: {absurl(club.clubprofile.club_object.get_permalink())}\n\n"
    )
    body = add_footer(body)

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [announcement.creator.email])


def announcement_notify_requester(announcement_type, announcement, user):
    subject = ""
    body = ""
    if announcement_type == "PlayerForClubAnnouncement":
        subject = "Wysłałeś zaproszenie na testy"
        body = (
            f"Twoje zaproszenie na testy zostało wysłane do "
            f"{announcement.creator.first_name} {announcement.creator.last_name}.\n"
            f"Jeśli zawodnik będzie zainteresowany - skontaktuje się z Tobą telefonicznie lub mailowo.\n\n"
        )
    elif announcement_type == "CoachForClubAnnouncement":
        subject = "Wysłałeś zaproszenie na rozmowę o pracę"
        body = (
            f"Twoje zaproszenie na rozmowę o pracę zostało wysłane do "
            f"{announcement.creator.first_name} {announcement.creator.last_name}.\n"
            f"Jeśli trener będzie zainteresowany - skontaktuje się z Tobą telefonicznie lub mailowo.\n\n"
        )
    elif announcement_type == "ClubForCoachAnnouncement":
        subject = "Wysłałeś aplikację na rozmowę o pracę"
        body = (
            f"Twoja aplikacja na rozmowę o pracę została wysłana do {announcement.club.display_club}.\n"
            f"Jeśli klub będzie zainteresowany Twoją kandydaturą - skontaktuje się z Tobą "
            f"telefonicznie lub mailowo.\n\n"
        )
    elif announcement_type == "ClubForPlayerAnnouncement":
        subject = "Wysłałeś zgłoszenie na testy"
        body = (
            f"Twoje zgłoszenie na testy zostało wysłane do {announcement.creator.profile.display_club}. \n"
            f"Reszta pozostaje w rękach trenera, prezesa lub dyrektora sportowego. "
            f"To oni decydują czy otrzymasz zaproszenie na testy.\n\n"
        )

    body = add_footer(body)

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])


def request_accepted(instance, extra_body=""):
    """inquiry request instance"""

    greetings = "Gratulujemy!"

    # setting object name
    if instance.recipient.is_player or instance.recipient.is_coach:
        name = f"{instance.recipient.first_name} {instance.recipient.last_name}"
    elif instance.recipient.is_club:
        name = f"{instance.recipient.profile.display_club}"
    else:
        name = ""

    # setting profile link
    profile_link = ""
    if instance.recipient.is_player or instance.recipient.is_coach:
        profile_link = absurl(instance.recipient.profile.get_permalink())
    else:
        profile_link = absurl(instance.recipient.profile.club_object.get_permalink())

    # setting phone
    phone = instance.recipient.profile.phone or "brak"
    message = ""

    # [player -> klub]
    if instance.sender.is_club and instance.recipient.is_player:
        subject = "Piłkarz zaakceptował Twoje zaproszenie na testy"
        message = f"Piłkarz {name} zaakceptował Twoje zaproszenie na testy. Poniżej prezentujemy jego dane kontaktowe:"

    # [trener -> klub]
    if instance.sender.is_club and instance.recipient.is_coach:
        subject = "Trener zaakceptował Twoje zaproszenie na testy"
        message = f"Trener {name}  zaakceptował Twoje zaproszenie. Poniżej prezentujemy jego dane kontaktowe:"

    # [klub -> trener]
    if instance.sender.is_coach and instance.recipient.is_club:
        subject = "Klub zaakceptował Twoje zapytanie"
        message = f"Klub {name} zaakceptował Twoje zapytanie. Poniżej prezentujemy jego dane kontaktowe:"

    # [piłkarz -> trener]
    if instance.sender.is_coach and instance.recipient.is_player:
        subject = "Piłkarz zaakceptował Twoje zaproszenie na testy"
        message = f"Piłkarz {name} zaakceptował Twoje zaproszenie na testy. Poniżej prezentujemy jego dane kontaktowe:"

    # [klub -> piłkarz]
    if instance.sender.is_player and instance.recipient.is_club:
        subject = "Klub zaakceptował Twoje zaproszenie na testy"
        message = f"Klub {name} zaakceptował Twoje zapytanie o testy. Poniżej prezentujemy jego dane kontaktowe:"

    # [trener-> piłkarz]
    if instance.sender.is_player and instance.recipient.is_coach:
        subject = "Trener zaakceptował Twoje zaproszenie na testy"
        message = f"Trener {name} zaakceptował Twoje zapytanie o testy. Poniżej prezentujemy jego dane kontaktowe:"

    body = f"{greetings}\n\n"
    body += f"{message}\n\n"
    body += f"\t{name}\n"
    body += "\t----------\n"
    body += f"\tProfil: {profile_link}\n"
    body += f"\tTelefon: {phone}\n"
    body += f"\tEmail: {instance.recipient.email}\n\n"
    body += "Pozdrawiamy, \n"
    body += "Zespół PlayMaker.pro"

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [instance.sender.email])


def weekly_account_report(instance, extra_body=""):
    """Instance users.User

    generates weekly raport
    """
    # text = textwrap.dedent(f'''
    subject = "Cotygodniowy raport"
    body = f"""
Witaj, z tej strony Zespół PlayMaker.pro!

Wiele działo się na Twoim profilu w zeszłym tygodniu

Otrzymane zapytania: {instance.sender_request_recipient.count()}
Wysłane zapytania: {instance.inquiry_request_recipient.count()}

Aktualnie pozostało Ci {instance.userinquiry.left} zaproszeń. Jeśli chcesz zwiększyć swoje limity, kliknij w poniższy

Zwieksz limity: {absurl('/' + settings.CUSTOM_URL_ENDPOINTS['limits'])}

Odwiedź swój profil: {absurl(instance.profile.get_permalink())}

Pozdrawiamy!
Zespół PlayMaker.pro
    """
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [instance.email])


def request_declined(instance, extra_body=""):
    """inquiry request instance"""

    body = ""

    # [player -> klub / coach]
    if (
        instance.sender.is_club or instance.sender.is_coach
    ) and instance.recipient.is_player:
        subject = "Piłkarz odrzucił Twoje zaproszenie"
        body += f"Piłkarz {instance.recipient.first_name} {instance.recipient.last_name} odrzucił Twoje zaproszenie na testy.\n\n"
        body += f"Jeśli nadal masz problem ze skompletowaniem kadry, sprawdź usługi skautingowe PlayMaker.pro. Więcej informacji znajdziesz w poniższym linku:\n\n"
        body += "https://playmaker.pro/scouting/\n\n"

    # [trener -> klub]
    if instance.sender.is_player and instance.recipient.is_coach:
        subject = "Trener odrzucił Twoje zapytanie"
        body += f"Trener {instance.recipient.first_name} {instance.recipient.last_name} odrzucił Twoje zapytanie o testy.\n\n"
        body += f"Jeśli nadal masz problem ze znalezieniem klubu, sprawdź nasze wsparcie transferowe PlayMaker.pro. Więcej informacji znajdziesz w poniższym linku:\n\n"
        body += "https://playmaker.pro/transfer/\n\n"

    if instance.sender.is_club and instance.recipient.is_coach:
        subject = "Trener odrzucił Twoje zapytanie"
        body += f"Trener {instance.recipient.first_name} {instance.recipient.last_name} odrzucił Twoje zapytanie o testy.\n\n"
        body += f"Jeśli nadal masz problem ze znalezieniem trenera do swojego klubu sprawdź naszą bazę trenerów pod poniższym linkiem lub napisz do nas na email na biuro@playmaker.pro\n\n"
        body += "https://playmaker.pro/tables/coaches/\n\n"

    # [klub -> trener]
    if (
        instance.sender.is_player or instance.sender.is_coach
    ) and instance.recipient.is_club:
        subject = "Klub odrzucił Twoje zapytanie"
        suffix = ""
        if instance.sender.is_player:
            suffix = " o testy"
        body += f"Klub {instance.recipient.profile.display_club} odrzucił Twoje zapytanie{suffix}.\n\n"
        body += f"Jeśli nadal masz problemem ze znalezieniem klubu, zaktualizuj swoje CV i uzyskaj wsparcie transferowe od PlayMaker.pro! Więcej informacji znajdziesz w poniższym linku: \n\n"
        body += "https://playmaker.pro/transfer/\n\n"

    body += "Pozdrawiamy, \n"
    body += "Zespół PlayMaker.pro"

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [instance.sender.email])


def request_new(instance, extra_body=""):
    """inquiry request instance"""

    if instance.sender.is_player:
        from_who = "piłkarza"
    elif instance.sender.is_coach:
        from_who = "trenera"
    elif instance.sender.is_club:
        from_who = "klubu"
    else:
        from_who = ""

    subject = "Otrzymane zaproszenie"
    body = "Gratulujemy! Otrzymałeś zaproszenie od innego użytkownika\n\n"

    logger.info(f"New request instance:{instance}")

    if (
        instance.sender.is_coach or instance.sender.is_club
    ) and instance.recipient.is_player:
        subject = f"Otrzymałeś zaproszenie od {from_who}"
        body = "Witaj,\n"
        body += "Gratulujemy! Otrzymałeś zaproszenie na testy!\n\n"
        body += "Odwiedź swój profil na PlayMaker.pro lub kliknij w poniższy link \n\n"
        body += f"https://playmaker.pro/????????????\n\n"  # TODO(rkeisk): @dep-2
        body += "Nie zwlekaj i zobacz, kto chce się z Tobą skontaktować!\n\n"
        body += "Do zobaczenia na PlayMaker.pro!\n"
        body += "Zespół PlayMaker.pro"

    elif instance.sender.is_player and (
        instance.recipient.is_club or instance.recipient.is_coach
    ):
        subject = f"Otrzymałeś zapytanie o testy od {from_who}"
        body = "Witaj,\n"
        body += "Zawodnik wysłał zapytanie o testy w Twoim klubie! \n\n"
        body += "Odwiedź swój klubowy profil na PlayMaker.pro lub kliknij w poniższy link \n\n"
        body += f'https://playmaker.pro{reverse("profiles:my_requests")}\n\n'
        body += "Nie zwlekaj i sprawdź profil zawodnika, który może okazać się potencjalnym wzmocnieniem Twojej kadry!\n\n"
        body += "Pozdrawiamy\n"
        body += "Zespół PlayMaker.pro"

    elif instance.sender.is_club and instance.recipient.is_coach:
        subject = f"Otrzymałeś zapytanie od klubu"
        body = "Witaj,\n"
        body += "Otrzymałeś zapytanie od klubu!  \n\n"
        body += "Odwiedź swój trenerski profil na www.playmaker.pro lub kliknij w poniższy link \n\n"
        body += f'{absurl(reverse("profiles:my_requests"))}\n\n'
        body += "Nie zwlekaj i przejrzyj profil klubu, który jest zainteresowany Twoim trenerskim profilem! \n\n"
        body += "Pozdrawiamy\n"
        body += "Zespół PlayMaker.pro"

    elif instance.sender.is_coach and instance.recipient.is_club:
        subject = f"Otrzymałeś zapytanie od trenera"
        body = "Witaj,\n"
        body += "Otrzymałeś zapytanie od trenera!  \n\n"
        body += "Odwiedź swój klubowy profil na www.playmaker.pro lub kliknij w poniższy link \n\n"
        body += f'{absurl(reverse("profiles:my_requests"))}\n\n'
        body += "Nie zwlekaj i przejrzyj profil Trenera, który może poprawić wyniki Twojej drużyny! \n\n"
        body += "Pozdrawiamy\n"
        body += "Zespół PlayMaker.pro"

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [instance.recipient.email])


def resetpassword(instance, extra_body=""):
    subject = "Twój profil został zweryfikowany"
    message = ""
    message += "Cześć, z tej strony Zespół PlayMaker.pro!\n\n"
    message += ""
    message += "Przejdź do platformy i bądź znaleziony w świecie piłki nożnej:\n\n"
    message += f"https://playmaker.pro{instance.profile.get_permalink()}\n\n"
    message += ""
    message += ""
    message += "Do zobaczenia na PlayMaker.pro!\n"
    message += "Zespół PlayMaker.pro\n"

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [instance.email],
        fail_silently=True,
    )


def verification_notification(instance, extra_body=""):
    subject = "Twój profil został zweryfikowany"
    message = ""
    message += "Cześć, z tej strony Zespół PlayMaker.pro!\n\n"
    message += ""
    message += "Przejdź do platformy i bądź znaleziony w świecie piłki nożnej:\n\n"
    message += f"https://playmaker.pro{instance.profile.get_permalink()}\n\n"
    message += ""
    message += ""
    message += "Do zobaczenia na PlayMaker.pro!\n"
    message += "Zespół PlayMaker.pro\n"

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [instance.email],
        fail_silently=True,
    )


def mail_role_change_request(instance, extra_body=""):
    """Instance -> profile.models.RoleChangeRequest"""

    if extra_body is None:
        extra_body = ""

    subject = f"[Zmiana roli] Prośba o zmianę roli dla użytkownika {instance.user}"
    message = (
        f"Użytkownik wysłał prośbe o zmianę swojej roli w profilu. \n "
        f"Obecna: {instance.current} --> {instance.get_new_display()} \n\n"
        f"Link do admina: {settings.BASE_URL}{instance.get_admin_url()}. \n\n"
        f"{extra_body}"
    )
    mail_managers(subject, message)


def mail_user_waiting_for_verification(instance, extra_body=None):
    """Instance -> users.models.User"""

    if extra_body is None:
        extra_body = ""

    if instance.declared_role is not None:
        role = instance.get_declared_role_display()
    else:
        role = instance.declared_role
    # f'Link do profilu: {build_absolute_url(instance.profile.get_permalink())} \n\n' \
    subject = f"[Oczekuje na weryfikacje] Użytkownik {instance.username} cheka na weryfikacje tożsamości"
    message = (
        f"Użytkownik {instance.username} ({role}) zmienił swoje dane. \n\n "
        f"Link do admina: {build_absolute_url(instance.get_admin_url())}. \n"
        f"{extra_body}"
    )
    mail_managers(subject, message)


def mail_admins_about_new_user(instance, extra_body=None):
    """
    Is na new user instance
    Instance -> users.models.User
    """

    if extra_body is None:
        extra_body = ""

    # f'Link do profilu: {build_absolute_url(instance.profile.get_permalink())} \n\n' \
    subject = (
        f"[Nowa rejestracja] Użytkownik {instance.username} właśnie się zarejestrował"
    )

    message = (
        f"Użytkownik {instance.username} {instance.first_name} ({instance.declared_role}) własnie się zarejestrował. \n\n "
        f"Link do admina: {build_absolute_url(instance.get_admin_url())}. \n"
        f"{extra_body}"
    )
    mail_managers(subject, message)
