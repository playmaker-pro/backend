from django.conf import settings
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class EmailCheckerThrottle(UserRateThrottle, AnonRateThrottle):
    """
    Custom throttle for email verification.
    We want to limit the number of requests to this endpoint due to security reasons.
    """

    rate = f"{settings.THROTTLE_EMAIL_CHECK_LIMITATION}/minute"
