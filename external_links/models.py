from django.db import models


class ExternalLinks(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    target_name = models.CharField(max_length=100, null=True, blank=True)

    @property
    def owner(self):
        if not self.target_name:
            for name in [
                "playerprofile",
                "clubprofile",
                "coachprofile",
                "guestprofile",
                "managerprofile",
                "scoutprofile",
                "refereeprofile",
                "club",
                "leaguehistory",
                "team",
            ]:
                if hasattr(self, name):
                    self.target_name = name
                    self.save()
            else:
                return None

        return getattr(self, self.target_name)

    def __str__(self):
        return f"{self.owner} links"


class LinkSource(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class ExternalLinksEntity(models.Model):
    RELATED_MODELS = (
        ("player", "player profile"),
        ("coach", "coach profile"),
        ("scout", "scout profile"),
        ("manager", "manager profile"),
        ("referee", "referee profile"),
        ("club", "club"),
        ("team", "team"),
        ("league", "league history highest parent"),
    )

    CREATOR_TYPE = (
        ("admin", "admin"),
        ("user", "user"),
    )

    DATA_TYPE = (
        ("statistics", "statistics"),
        ("social", "social"),
    )

    target = models.ForeignKey(
        ExternalLinks,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="links",
    )
    source = models.ForeignKey(
        LinkSource, on_delete=models.SET_NULL, null=True, blank=True
    )
    url = models.URLField(max_length=500, null=True, blank=True)
    related_type = models.CharField(max_length=100, choices=RELATED_MODELS)
    creator_type = models.CharField(max_length=100, choices=CREATOR_TYPE)
    link_type = models.CharField(max_length=100, choices=DATA_TYPE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        if not self.description:
            self.update_description(f"{self.target.owner} - Type: {self.source}")

        return self.description

    def update_description(self, text: str):
        self.description = text
        self.save()

    class Meta:
        unique_together = ("target", "source")
