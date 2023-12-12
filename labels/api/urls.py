from django.urls import path
from rest_framework import routers

from labels.api import views

router = routers.SimpleRouter(trailing_slash=False)

urlpatterns = [
    path(
        r"",
        views.LabelsAPI.as_view(
            {
                "get": "get_labels_definition",
            }
        ),
        name="labels_definition_list",
    ),]
