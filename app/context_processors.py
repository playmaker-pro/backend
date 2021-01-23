from django.conf import settings


def app_info(request):
    return {'app_version': settings.VERSION, 'app_debug': settings.DEBUG}
