import logging

from django.db import models as dj_models
from django.utils import timezone

from events import errors, models


logger = logging.getLogger(__name__)


class NotificationServices:
    def read_event(self, event_id: int, request_user_id: int) -> None:
        try:
            event = models.NotificationEvent.objects.get(id=event_id)
        except models.NotificationEvent.DoesNotExist:
            logger.error(f"Message with given id={event_id} does not exists")

        if event.user.id is not request_user_id:
            raise errors.OperationOnEventNotAllowed()

        if event.seen is False:
            event.seen_date = timezone.now()
            event.seen = True
            event.save()
        else:
            raise errors.EventAlreadySeen(f"event={event_id} already marked as seen")

    def get_user_unseen_events(
        self, user_id: int, request_user_id: int
    ) -> dj_models.QuerySet:
        if request_user_id != user_id:
            raise errors.OperationOnEventNotAllowed()

        return models.NotificationEvent.objects.filter(
            user__id=user_id,
            seen=False,
        )
