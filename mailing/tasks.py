from celery import shared_task
from django.core.mail import mail_admins


@shared_task
def notify_admins(subject, message):
    mail_admins(subject, message)
