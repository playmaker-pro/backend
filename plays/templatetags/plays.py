
from django import template
from django.urls import reverse
from django.utils.translation import gettext as _


register = template.Library()


@register.filter(name="get_league_url")
def get_league_url(league, season: str = None):
    url = reverse(
        "plays:summary",
        kwargs={"slug": league.slug}
    )
    if season:
        return f"{url}?season={season}"
    return url
