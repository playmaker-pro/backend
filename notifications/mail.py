from django.core.mail import mail_managers


def mail_role_change_request(instance):
    ''' Instance -> profile.models.RoleChangeRequest
    '''
    subject = f'Prośba o zmianę roli dla użytkownika {instance.user}'
    message = f'Użytkownik wysłał prośbe o zmianę swojej roli w profilu. \n ' \
        f'Obecna: {instance.current} --> {instance.get_new_display()} \n\n' \
        f'Link do admina: {instance.get_admin_url()}.'
    mail_managers(subject, message)


def mail_user_waiting_for_verification(instance):
    ''' Instance -> users.models.User
    '''
    subject = f'Użytkownik {instance.username} cheka na werifikacje tożsamości'
    message = f'Użytkownik potwierdził swój adress email. \n ' \
        'Link do admina: {instance.get_admin_url()}.'
    mail_managers(subject, message)
