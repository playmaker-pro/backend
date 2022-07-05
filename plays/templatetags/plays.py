from django import template
from django.urls import reverse
from django.utils.translation import gettext as _

from clubs.models import League


register = template.Library()


@register.filter(name="get_league_url")
def get_league_url(league: League, season: str = None):
    url = league.get_permalink()
    if season:
        return f"{url}?season={season}"
    return url
