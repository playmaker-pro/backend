import logging

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from profiles import models
from profiles.api.errors import InvalidProfileRole, ProfileDoesNotExist
from profiles.errors import ProfileVisitHistoryDoesNotExistException
from profiles.services import ProfileService, ProfileVisitHistoryService

User = get_user_model()

profile_service = ProfileService()
visit_history_service = ProfileVisitHistoryService()

logger = logging.getLogger(__name__)


class ProfileRetrieveMixin:
    def retrieve_profile_and_respond(
        self, request, profile_object: models.PROFILE_MODELS
    ) -> Response:
        """Shared logic for retrieving a profile and responding with serialized data."""
        # Profile visit counter logic
        if profile_object.user != request.user:
            requestor_profile = self.handle_requestor_profile(request)
            self.manage_visit_history(profile_object, requestor_profile)

        # Serializer logic
        serializer_class = self.get_serializer_class(
            model_name=profile_object.__class__.__name__
        )
        if not serializer_class:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = serializer_class(
            profile_object, context={"request": request, "label_context": "profile"}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def handle_requestor_profile(self, request: Request) -> User:
        """Handle requestor profile logic."""
        requestor_profile = request.user
        if request.user.is_authenticated:
            try:
                requestor_profile = profile_service.get_profile_by_role_and_user(
                    user=request.user, role=request.user.role
                )
                if not requestor_profile:
                    raise ProfileDoesNotExist(details="Requestor has no profile")
            except ValueError:
                raise InvalidProfileRole(details="Requestor has invalid role")
        return requestor_profile

    def manage_visit_history(self, profile_object, requestor) -> None:
        """Manage the visit history for a profile."""
        try:
            history = visit_history_service.get_user_profile_visit_history(
                user=profile_object.user, created_at=timezone.now()
            )
            visit_history_service.increment(instance=history, requestor=requestor)
        except ProfileVisitHistoryDoesNotExistException:
            logger.error("Profile visit history does not exist. Creating one..")
            history = visit_history_service.create(user=profile_object.user)
            visit_history_service.increment(instance=history, requestor=requestor)

        try:
            requestor_profile = requestor.profile
        except:
            return

        models.ProfileVisitation.upsert(
            visitor=requestor_profile, visited=profile_object
        )
