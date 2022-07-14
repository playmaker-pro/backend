from notifications import (
    mail,
)  # import mail_role_change_request, mail_admins_about_new_user


def notify_duplicated_default_annoucement_plan(user):
    subject = f"Błąd podczas nadawania planu (2x default)"
    message = f'Są 2 plany do ogłoszeń z ustawieniem jako "default"!\n\nNapraw problem i przypisz plan (AnnouncementUserQuota) użytkownikom którzy ostanio się rejestrowali.\n\n {user.email} \n\n'
    mail.notify_error_admins(subject, message)
