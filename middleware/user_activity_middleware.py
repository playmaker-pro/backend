import logging
from users.tasks import update_user_last_activity, update_visit_history_for_actual_date
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
                user = request.user
                update_user_last_activity.delay(user_id=user.pk)
                update_visit_history_for_actual_date.delay(user_id=user.pk)
            except Exception as e:
                logger.error(f"Error updating user activity: {e}")
        return response
