from django.contrib import sitemaps
from django.urls import reverse
from blog.models import BlogPage
from profiles.models import PlayerProfile
from users.models import User
from django.contrib.sitemaps import GenericSitemap


class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "fantasy:fantasy",
            "products:products",
            "marketplace:announcements",
            "soccerbase:players",
            "soccerbase:coaches",
            "soccerbase:teams",
        ]

    def location(self, item):
        return reverse(item)


sitemaps = {
    "sitemaps": {
        "static": StaticViewSitemap,
        "blog": GenericSitemap({"queryset": BlogPage.objects.all()}, priority=0.6),
        "players": GenericSitemap(
            {
                "queryset": PlayerProfile.objects.filter(
                    user__state=User.STATE_ACCOUNT_VERIFIED,
                )
            },
            priority=0.9,
        ),
    }
}
