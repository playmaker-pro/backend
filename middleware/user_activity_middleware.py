import logging

from django.utils import timezone

from profiles.errors import ProfileVisitHistoryDoesNotExistException
from profiles.services import ProfileVisitHistoryService

logger = logging.getLogger("user_activity")


class UserActivityMiddleware:
    """
    Middleware to track the activity of authenticated users.

    Whenever an authenticated user makes a request, their activity is updated
    using the `new_user_activity` method on the user instance.
    """

    def __init__(self, get_response):
        """
        Initialize the middleware.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the request, updating user activity if they are authenticated,
        and profile visit history for actual date for none staff users.
        """
        response = self.get_response(request)
        # check if user is authenticated and update activity
        if request.user.is_authenticated:
            try:
                (user := request.user).new_user_activity()

                # Update user visit history for actual date.
                visit_history_service = ProfileVisitHistoryService()
                if not user.is_staff and not user.is_superuser:
                    try:
                        user_visit_history = (
                            visit_history_service.get_user_profile_visit_history(
                                user=user, created_at=timezone.now()
                            )
                        )
                        user_visit_history.user_logged_in = True
                        user_visit_history.save()
                    except ProfileVisitHistoryDoesNotExistException:
                        visit_history_service.create(user=user, user_logged_in=True)
            except Exception as e:
                logger.error(f"Error updating user activity: {e}")
        return response
