from django.core.mail import mail_managers
from django.conf import settings


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


def mail_user_waiting_for_verification(instance, extra_body=None):
    ''' Instance -> users.models.User
    '''

    if extra_body is None:
        extra_body = ''

    subject = f'[Oczekuje na werifikacje] Użytkownik {instance.username} cheka na werifikacje tożsamości'
    message = f'Użytkownik {instance.username} zmienił swoje dane. \n ' \
        f'Link do admina: {settings.BASE_URL}{instance.get_admin_url()}. \n' \
        f'{extra_body}'
    mail_managers(subject, message)
