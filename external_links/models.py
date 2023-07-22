from django.db import models


class ExternalLinks(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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
        ExternalLinks, on_delete=models.SET_NULL, null=True, blank=True
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

    def __str__(self):
        return self.source.name

    class Meta:
        unique_together = ("target", "source")
