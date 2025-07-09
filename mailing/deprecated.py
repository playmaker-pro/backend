from django.conf import settings
from django.core.mail import mail_managers


def build_absolute_url(uri: str) -> str:
    url = f"{settings.BASE_URL}{uri}"
    return url


def mail_admins_about_new_user(instance, extra_body=None):
    """
    Is na new user instance
    Instance -> users.models.User
    """

    if extra_body is None:
        extra_body = ""

    # f'Link do profilu: {build_absolute_url(instance.profile.get_permalink())} \n\n' \
    subject = f"[Nowa rejestracja] Użytkownik  właśnie się zarejestrował"

    message = (
        f"Użytkownik {instance.first_name} ({instance.declared_role}) własnie się zarejestrował. \n\n "
        f"Link do admina: {build_absolute_url(instance.get_admin_url())}. \n"
        f"{extra_body}"
    )
    mail_managers(subject, message)


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
