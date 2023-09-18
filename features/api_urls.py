from django.urls import path

from features.api_views import FeatureElementAPI

app_name = "features"


urlpatterns = [
    path(
        r"",
        FeatureElementAPI.as_view(
            {
                "post": "create_feature_subscription_entity",
            }
        ),
        name="create_feature_subscription_entity",
    ),
]
