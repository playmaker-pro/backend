from django.core.mail import mail_managers, send_mail
from django.conf import settings
from django.urls import reverse
import logging
from notifications.base import PMMailBase

logger = logging.getLogger(__name__)


class ProductMail(PMMailBase):

    @classmethod
    def mail_admins_about_new_product_request(self, instance, extra_body=None):
        '''
        instance -> products.models.UserRequest
        '''

        if extra_body is None:
            extra_body = ''

        subject = f'[Nowe zapytanie produktowe][{instance.product.title}] od użytkownika {instance.user.username}'

        message = f'Użytkownik {instance.user.username} {instance.user.first_name} ({instance.user.declared_role}) własnie wysłał zgłoszenie o product. \n\n ' \
            f'Body: {instance.body_pretty} \n' \
            f'\n\n{extra_body}'
        if instance.product.contact_email:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.contact_email])
        if instance.product.send_email_to_admin:
            mail_managers(subject, message)

    @classmethod
    def mail_user_about_his_request(self, instance, extra_body=None):
        '''
        instance -> products.models.UserRequest
        '''
        # tbdefined
        # body = ''
        # send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [instance.user.email])
