

from django.core.mail.backends.smtp import EmailBackend

EmailBackend()

from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend

ConsoleEmailBackend()