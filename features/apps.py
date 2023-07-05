from django.apps import AppConfig


class FeaturesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features"

    def ready(self) -> None:
        """Load custom signals."""
        from django.db import models
        from features.models import FeatureElement

        models.signals.pre_save.connect(
            FeatureElement.on_pre_save, sender=FeatureElement
        )
