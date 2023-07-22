from django.conf import settings

from utils import get_current_season


def app_info(request):
    return {
        "app_version": settings.VERSION,
        "app_debug": settings.DEBUG,
        "app_debug_panel": settings.DEBUG_PANEL,
        "current_season": get_current_season(),
        "seo": settings.SEO_DATA,
    }
