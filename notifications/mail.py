from django.core.mail import mail_managers, send_mail
from django.conf import settings
from django.urls import reverse


def request_new(instance, extra_body=''):
    ''' inquiry request instance'''

    if instance.sender.is_player:
        from_who = 'piłkarza'
    elif instance.sender.is_coach:
        from_who = 'trenera'
    elif instance.sender.is_club:
        from_who = 'klubu'
    else:
        from_who = ''

    if (instance.sender.is_coach or instance.sender.is_club) and instance.recipient.is_player:
        subject = f"Otrzymałeś zaproszenie od {from_who}"
        body = 'Witaj,\n'
        body += 'Gratulujemy! Otrzymałeś zaproszenie na testy!\n\n'
        body += 'Odwiedź swój profil na PlayMaker.pro lub kliknij w poniższy link \n\n'
        body += f'https://playmaker.pro{reverse("profiles:my_requests")}\n\n'
        body += 'Nie zwlekaj i zobacz, kto chce się z Tobą skontaktować!\n\n'
        body += 'Do zobaczenia na PlayMaker.pro!\n'
        body += 'Zespół PlayMaker.pro'
    elif instance.sender.is_player and (instance.recipient.is_club or instance.recipient.is_coach):
        subject = f"Otrzymałeś zapytanie o testy od {from_who}"
        body = 'Witaj,\n'
        body += 'Zawodnik wysłał zapytanie o testy w Twoim klubie! \n\n'
        body += 'Odwiedź swój klubowy profil na PlayMaker.pro lub kliknij w poniższy link \n\n'
        body += f'https://playmaker.pro{reverse("profiles:my_requests")}\n\n'
        body += 'Nie zwlekaj i sprawdź profil zawodnika, który może okazać się potencjalnym wzmocnieniem Twojej kadry!\n\n'
        body += 'Pozdrawiamy\n'
        body += 'Zespół PlayMaker.pro'

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [instance.recipient.email])


def resetpassword(instance, extra_body=''):

    subject = 'Twój profil został zweryfikowany'
    message = ''
    message += 'Cześć, z tej strony Zespół PlayMaker.pro!\n\n'
    message += ''
    message += 'Przejdź do platformy i bądź znaleziony w świecie piłki nożnej:\n\n'
    message += f'https://playmaker.pro{instance.profile.get_permalink()}\n\n'
    message += ''
    message += ''
    message += 'Do zobaczenia na PlayMaker.pro!\n'
    message += 'Zespół PlayMaker.pro\n'

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email], fail_silently=True)


def verification_notification(instance, extra_body=''):

    subject = 'Twój profil został zweryfikowany'
    message = ''
    message += 'Cześć, z tej strony Zespół PlayMaker.pro!\n\n'
    message += ''
    message += 'Przejdź do platformy i bądź znaleziony w świecie piłki nożnej:\n\n'
    message += f'https://playmaker.pro{instance.profile.get_permalink()}\n\n'
    message += ''
    message += ''
    message += 'Do zobaczenia na PlayMaker.pro!\n'
    message += 'Zespół PlayMaker.pro\n'

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email], fail_silently=True)


def mail_role_change_request(instance, extra_body=''):
    ''' Instance -> profile.models.RoleChangeRequest
    '''

    if extra_body is None:
        extra_body = ''

    subject = f'[Zmiana roli] Prośba o zmianę roli dla użytkownika {instance.user}'
    message = f'Użytkownik wysłał prośbe o zmianę swojej roli w profilu. \n ' \
        f'Obecna: {instance.current} --> {instance.get_new_display()} \n\n' \
        f'Link do admina: {settings.BASE_URL}{instance.get_admin_url()}. \n\n' \
        f'{extra_body}'
    mail_managers(subject, message)


def build_absolute_url(uri: str) -> str:
    url = f'{settings.BASE_URL}{uri}'
    return url


def mail_user_waiting_for_verification(instance, extra_body=None):
    ''' Instance -> users.models.User
    '''

    if extra_body is None:
        extra_body = ''

    if instance.declared_role is not None:
        role = instance.get_declared_role_display()
    else:
        role = instance.declared_role
  # f'Link do profilu: {build_absolute_url(instance.profile.get_permalink())} \n\n' \
    subject = f'[Oczekuje na weryfikacje] Użytkownik {instance.username} cheka na weryfikacje tożsamości'
    message = f'Użytkownik {instance.username} ({role}) zmienił swoje dane. \n\n ' \
        f'Link do admina: {build_absolute_url(instance.get_admin_url())}. \n' \
        f'{extra_body}'
    mail_managers(subject, message)


def mail_admins_about_new_user(instance, extra_body=None):
    '''
    Is na new user instance
    Instance -> users.models.User
    '''

    if extra_body is None:
        extra_body = ''

    # f'Link do profilu: {build_absolute_url(instance.profile.get_permalink())} \n\n' \
    subject = f'[Nowa rejestracja] Użytkownik {instance.username} właśnie się zarejestrował'

    message = f'Użytkownik {instance.username} {instance.first_name} ({instance.declared_role}) własnie się zarejestrował. \n\n ' \
        f'Link do admina: {build_absolute_url(instance.get_admin_url())}. \n' \
        f'{extra_body}'
    mail_managers(subject, message)
