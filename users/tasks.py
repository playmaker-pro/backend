from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from inquiries.services import InquireService
from mailing.models import Mailing
from profiles.errors import ProfileVisitHistoryDoesNotExistException
from profiles.services import ProfileVisitHistoryService
from users.models import Ref, User, UserPreferences
from users.mongo_login_service import mongo_login_service
from users.services import UserService

logger = get_task_logger(__name__)


def _get_user(user_id: int) -> User:
    return User.objects.get(pk=user_id)


@shared_task
def prepare_new_user(*args, **kwargs) -> None:
    """
    Create required/related objects for new user.
    """
    user = _get_user(kwargs.get("user_id"))
    UserPreferences.objects.get_or_create(user=user)
    Ref.objects.get_or_create(user=user)
    InquireService.create_basic_inquiry_plan(user)
    Mailing.objects.get_or_create(user=user)


@shared_task
def send_email_to_confirm_new_user(*args, **kwargs) -> None:
    """
    Send an email to new user to confirm his account.
    """
    user = _get_user(kwargs.get("user_id"))
    UserService.send_email_to_confirm_new_email_address(user)


@shared_task
def update_user_last_activity(*args, **kwargs):
    """
    Update user's last activity date.
    """
    user = _get_user(kwargs.get("user_id"))
    user.update_activity()


@shared_task
def update_visit_history_for_actual_date(*args, **kwargs):
    """
    Update user visit history for actual date.
    """
    user = _get_user(kwargs.get("user_id"))
    visit_history_service = ProfileVisitHistoryService()

    if not user.is_staff and not user.is_superuser:
        try:
            user_visit_history = visit_history_service.get_user_profile_visit_history(
                user=user, created_at=timezone.now()
            )
            user_visit_history.user_logged_in = True
            user_visit_history.save()
        except ProfileVisitHistoryDoesNotExistException:
            visit_history_service.create(user=user, user_logged_in=True)


@shared_task
def track_user_login_task(user_id: int) -> None:
    """Celery task to track user login activity using MongoDB."""
    try:
        success = mongo_login_service.track_user_login(user_id)

        if not success:
            logger.warning(f"MongoDB login tracking returned False for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to track login for user {user_id}: {str(e)}")
