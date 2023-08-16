import logging

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
        Process the request, updating user activity if they are authenticated.
        """
        response = self.get_response(request)
        # check if user is authenticated and update activity
        if request.user.is_authenticated:
            try:
                request.user.new_user_activity()
            except Exception as e:
                # Log the error
                logger.error(f"Error updating user activity: {e}")
        return response
