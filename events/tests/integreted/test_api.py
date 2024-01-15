from time import sleep

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from utils.test.test_utils import UserManager
from utils.factories.user_factories import UserFactory
from events import models as event_models


class EventSeenAPITests(APITestCase):
    def setUp(self) -> None:
        # GIVEN we have a event for a user_id=1 which is unseen (newly created)
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        self.url = "api:events:read_event"
        self.unseen_event = event_models.NotificationEvent.objects.create(
            user=self.user_obj,
            message="Powinieneś jeść więcej śledzi. Wygooglaj sobie.",
            callback="https://google.com",
        )
        self.user_obj2 = (
            UserFactory.create()
        )  # email="rr@rr.com", password="123123qweqwe")
        self.user_obj2.is_activated = True
        self.user_obj2.save()
        self.user_2_event = event_models.NotificationEvent.objects.create(
            user=self.user_obj2,
            message="Powinieneś jeść więcej śledzi. Wygooglaj sobie.",
            callback="https://google.com",
        )
        assert (
            not self.unseen_event.seen
        ), "This is not part of that test scope, but assumption is that database constrains guarantee that event by default is un-seen"
        assert (
            self.unseen_event.seen_date is None
        ), "This is not part of that test scope, but assumption is that database constrains guarantee that event by default is un-seen"

    def _make_mark_read_call(self, event_id: int):
        return self.client.post(
            reverse(self.url, kwargs={"event_id": event_id}),
            **self.headers,
        )

    def test_read_event_get_method_not_allwoed(self) -> None:
        # WHEN: we GET call a api endpoint to mark that specific event as seen
        response = self.client.get(
            reverse(self.url, kwargs={"event_id": self.unseen_event.id}),
            **self.headers,
        )

        # THEN: we should recieve 405 as we allow only POST
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_read_event(self) -> None:
        # WHEN: we POST call a api endpoint to mark that specific event as seen
        response = self._make_mark_read_call(self.unseen_event.id)

        # THEN: we should recieve 200 status with empty response
        #    (side-effect) we should see in database a event with changed flag to seen=True
        #    TODO(rkesik): since we do not have very deep tests we will check that here but that is out-of-the scope of that tests
        assert response.status_code == status.HTTP_200_OK, response.__dict__
        updated_event = event_models.NotificationEvent.objects.get(
            id=self.unseen_event.id
        )
        assert updated_event.seen is True
        assert updated_event.seen_date is not None

    def test_read_event_on_non_existing_object(self) -> None:
        # WHEN: we POST call a api endpoint to mark event as read using random-non-existing id
        response = self._make_mark_read_call(9999900)

        # THEN: we should get an error HTTP 404
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_read_event_on_already_seen_object(self) -> None:
        self.unseen_event.seen = True
        self.unseen_event.save()
        # WHEN: we POST call a api endpoint to mark that specific event as seen
        response = self._make_mark_read_call(self.unseen_event.id)
        # THEN: we should get 409 conflict with empty resource
        assert response.status_code == status.HTTP_409_CONFLICT, response.__dict__

    def test_forbidden_to_read_others_events(self) -> None:
        # WHEN: As User1 we POST call a api endpoint to mark that differnet event id
        response = self._make_mark_read_call(self.user_2_event.id)
        # THEN: we should get 403
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.__dict__


class UserEventsAPITests(APITestCase):
    def setUp(self) -> None:
        # GIVEN we have a events for a user1 and user2 which are unseen
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj1 = self.user.create_superuser()

        self.user_obj2 = (
            UserFactory.create()
        )  # email="rr@rr.com", password="123123qweqwe")
        self.user_obj2.is_activated = True
        self.user_obj2.save()

        self.headers = self.user.get_headers()
        self.url = "api:events:get_user_events"
        sleep(1)
        self.event1 = event_models.NotificationEvent.objects.create(
            user=self.user_obj1,
            message="User 1 event",
            callback="https://google.com",
        )
        sleep(1)
        self.event2 = event_models.NotificationEvent.objects.create(
            user=self.user_obj1,
            message="User 1 event",
            callback="https://google.com",
        )
        self.event3 = event_models.NotificationEvent.objects.create(
            user=self.user_obj2,
            message="User 2 event",
            callback="https://google.com",
        )

    def _make_get_users_call(self, user_id: int):
        url = "api:events:get_user_events"
        return self.client.get(
            reverse(url, kwargs={"user_id": user_id}),
            **self.headers,
        )

    def test_get_list_of_events_for_given_user(self):
        # WHEN: we GET call a api endpoint to get specific user events
        response = self._make_get_users_call(self.user_obj1.id)
        # THEN: we should get an error HTTP 200
        assert response.status_code == status.HTTP_200_OK, response.__dict__
        data = response.json()
        assert data["count"] == 2, data
        assert data["next"] is None, data
        assert data["previous"] is None, data
        assert len(data["results"]) == 2, data
        for event in data["results"]:
            assert event["message"] == "User 1 event", data

    def test_not_allowed_to_get_other_events(self):
        # WHEN: as a User1 we GET call a api endpoint to get User2's events
        response = self._make_get_users_call(self.user_obj2.id)
        # THEN: we should get an error HTTP 403
        assert response.status_code == status.HTTP_403_FORBIDDEN
