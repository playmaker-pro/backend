import json

import pytest
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

from inquiries.models import (
    InquiryContact,
    InquiryLogMessage,
    InquiryRequest,
    UserInquiryLog,
)
from notifications.models import Notification
from utils.factories import GuestProfileFactory
from utils.test.test_utils import UserManager

sender_contact_data = {
    "phone_number": {"dial_code": "+1", "number": "123456789"},
    "email": "sender@playmaker.pro",
}
recipient_contact_data = {
    "phone_number": {"dial_code": "+2", "number": "978654321"},
    "email": "recipient@playmaker.pro",
}


URL_SEND = lambda uuid: reverse(
    "api:inquiries:send_inquiry", kwargs={"recipient_profile_uuid": uuid}
)
URL_ACCEPT = lambda request_id: reverse(
    "api:inquiries:accept_inquiry_request", kwargs={"request_id": request_id}
)
URL_REJECT = lambda request_id: reverse(
    "api:inquiries:reject_inquiry_request", kwargs={"request_id": request_id}
)
URL_MY_SENT = reverse("api:inquiries:my_sent_inquiries")
URL_MY_CONTACTS = reverse("api:inquiries:my_inquiry_contacts")
URL_MY_RECEIVED = reverse("api:inquiries:my_received_inquiries")
URL_MY_DATA = reverse("api:inquiries:my_inquiry_data")
URL_UPDATE_CONTACT_DATA = reverse("api:inquiries:update_contact_data")


@pytest.mark.usefixtures("silence_mails")
class TestInquiriesAPI(APITestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.sender_manager = UserManager(self.client)
        self.recipient_manager = UserManager(self.client)
        self.sender_obj = self.sender_manager.create_superuser(
            email="sender@sender.com", userpreferences={"gender": "M"}
        )
        self.recipient_obj = self.recipient_manager.create_superuser(
            email="recipient@recipient.com", userpreferences={"gender": "K"}
        )
        self.sender_headers = self.sender_manager.get_headers()
        self.recipient_headers = self.recipient_manager.get_headers()
        GuestProfileFactory.create(user=self.recipient_obj)

    @property
    def sender_contact_data(self) -> (dict, dict):
        return sender_contact_data, self.sender_headers

    @property
    def recipient_contact_data(self) -> (dict, dict):
        return recipient_contact_data, self.recipient_headers

    @property
    def recipient_profile_uuid(self) -> str:
        return str(self.recipient_obj.profile.uuid)

    def update_contact_data(self, data: dict, headers: dict) -> None:
        response = self.client.post(
            URL_UPDATE_CONTACT_DATA,
            data=json.dumps(data),
            **headers,
        )
        assert response.status_code == 200
        assert response.data["email"] == data["email"]
        expected_phone_number = {
            "dial_code": f"+{data['phone_number']['dial_code']}",
            "number": data["phone_number"]["number"],
        }
        assert response.data["phone_number"] == expected_phone_number

    def test_valid_accept_request_full_flow(self) -> None:
        """Test should success, full flow of accepting inquiry request"""
        self.update_contact_data(*self.sender_contact_data)
        self.update_contact_data(*self.recipient_contact_data)
        send_response = self.client.post(
            URL_SEND(self.recipient_profile_uuid),
            **self.sender_headers,
        )  # Sent request to another user

        assert send_response.status_code == 201

        obj: InquiryRequest = InquiryRequest.objects.get(
            pk=send_response.data.get("id")
        )
        assert obj.status == InquiryRequest.STATUS_SENT
        assert obj.sender == self.sender_obj
        assert obj.recipient == self.recipient_obj

        sent_requests_response = self.client.get(
            URL_MY_SENT,
            **self.sender_headers,
        )  # Get all sent requests by sender

        assert sent_requests_response.status_code == 200
        assert len(sent_requests_response.data) == 1
        notifications_count_before = Notification.objects.count()
        accept_response = self.client.post(
            URL_ACCEPT(obj.pk),
            **self.recipient_headers,
        )  # Accept request by recipient

        assert accept_response.status_code == 200
        obj.refresh_from_db()
        assert obj.status == InquiryRequest.STATUS_ACCEPTED
        notifications_count_after = Notification.objects.count()
        assert notifications_count_after == notifications_count_before + 1
        new_notification = Notification.objects.latest("id")
        assert new_notification.user == self.sender_obj
        assert (
            new_notification.notification_type == Notification.NotificationType.CONTACTS
        )

        contacts_response = self.client.get(
            URL_MY_CONTACTS,
            **self.sender_headers,
        )  # Get all sender contacts, list should include recipient
        assert contacts_response.status_code == 200
        assert len(contacts_response.data) == 1

        # Check contacts data correctly exchanged
        assert contacts_response.data[0].get(
            "body"
        ) == InquiryContact.parse_custom_body(
            sender_contact_data["phone_number"]["number"],
            int(sender_contact_data["phone_number"]["dial_code"].replace("+", "")),
            sender_contact_data["email"],
        )

        assert contacts_response.data[0].get(
            "body_recipient"
        ) == InquiryContact.parse_custom_body(
            recipient_contact_data["phone_number"]["number"],
            int(recipient_contact_data["phone_number"]["dial_code"].replace("+", "")),
            recipient_contact_data["email"],
        )

        assert (
            UserInquiryLog.objects.filter(
                log_owner=self.sender_obj.userinquiry,
                message__log_type=InquiryLogMessage.MessageType.ACCEPTED,
            ).exists()
            and UserInquiryLog.objects.filter(
                log_owner=self.recipient_obj.userinquiry,
                message__log_type=InquiryLogMessage.MessageType.NEW,
            ).exists()
        )

    def test_valid_reject_request_full_flow(self) -> None:
        """Test should success, full flow of rejecting inquiry request"""
        send_response = self.client.post(
            URL_SEND(self.recipient_profile_uuid),
            **self.sender_headers,
        )  # Sent request to another user

        assert send_response.status_code == 201

        sender_metadata_response = self.client.get(
            URL_MY_DATA,
            **self.sender_headers,
        )  # Check counter incrementation
        assert sender_metadata_response.status_code == 200
        assert sender_metadata_response.data.get("counter") == 1

        obj: InquiryRequest = InquiryRequest.objects.get(
            pk=send_response.data.get("id")
        )
        assert obj.status == InquiryRequest.STATUS_SENT
        assert obj.sender == self.sender_obj
        assert obj.recipient == self.recipient_obj

        reject_response = self.client.post(
            URL_REJECT(obj.pk),
            **self.recipient_headers,
        )  # reject request by recipient

        assert reject_response.status_code == 200
        obj.refresh_from_db()
        assert obj.status == InquiryRequest.STATUS_REJECTED

        contact_response = self.client.get(
            URL_MY_CONTACTS,
            **self.sender_headers,
        )  # Nothing in contacts due to rejection
        assert contact_response.status_code == 200
        assert len(contact_response.data) == 0

        assert (
            UserInquiryLog.objects.filter(
                log_owner=self.sender_obj.userinquiry,
                message__log_type=InquiryLogMessage.MessageType.REJECTED,
            ).exists()
            and UserInquiryLog.objects.filter(
                log_owner=self.recipient_obj.userinquiry,
                message__log_type=InquiryLogMessage.MessageType.NEW,
            ).exists()
        )

    def test_everything_require_authentication(self) -> None:
        """Test should fail, all endpoints require authentication"""
        assert (
            self.client.post(
                URL_SEND(self.recipient_profile_uuid),
            ).status_code
            == 401
        )
        assert (
            self.client.post(
                URL_ACCEPT(1),
            ).status_code
            == 401
        )
        assert (
            self.client.post(
                URL_REJECT(1),
            ).status_code
            == 401
        )
        assert (
            self.client.get(
                URL_MY_SENT,
            ).status_code
            == 401
        )
        assert (
            self.client.get(
                URL_MY_CONTACTS,
            ).status_code
            == 401
        )
        assert (
            self.client.get(
                URL_MY_RECEIVED,
            ).status_code
            == 401
        )
        assert (
            self.client.get(
                URL_MY_DATA,
            ).status_code
            == 401
        )
        assert (
            self.client.post(
                URL_UPDATE_CONTACT_DATA,
            ).status_code
            == 401
        )

    def test_get_user_inquire_metadata(self) -> None:
        """Test should success, get user inquire metadata"""
        self.update_contact_data(*self.sender_contact_data)

        response = self.client.get(
            URL_MY_DATA,
            **self.sender_headers,
        )
        assert response.status_code == 200
        assert response.data.get("plan")
        assert response.data.get("contact")
        assert response.data.get("counter") == 0

    def test_inquiry_plan_limit(self) -> None:
        """Test limit of inquiries"""

        def create_new_profile_and_send_him_inquiry() -> Response:
            """Create new profile and send him inquiry"""
            profile = GuestProfileFactory.create()
            return self.client.post(
                URL_SEND(str(profile.uuid)),
                **self.sender_headers,
            )

        limit = self.sender_obj.userinquiry.limit  # type: ignore
        for _ in range(limit):
            response = create_new_profile_and_send_him_inquiry()
            assert response.status_code == 201

        response = create_new_profile_and_send_him_inquiry()

        assert response.status_code == 400

    def test_read_inquire_request(self) -> None:
        """
        Test update inquiry request state: sent -> read.
        Should happened on GET recipient inquiry requests.
        """
        send_response = self.client.post(
            URL_SEND(self.recipient_profile_uuid), **self.sender_headers
        )
        assert send_response.status_code == 201

        obj_id = send_response.data["id"]
        obj = InquiryRequest.objects.get(pk=obj_id)

        assert obj.status == InquiryRequest.STATUS_SENT

        receive_recipment_repsponse = self.client.get(
            URL_MY_RECEIVED, **self.recipient_headers
        )

        assert receive_recipment_repsponse.status_code == 200
        assert (
            receive_recipment_repsponse.data[0]["status"]
            == InquiryRequest.STATUS_RECEIVED
        )

        obj.refresh_from_db()

        assert obj.status == InquiryRequest.STATUS_RECEIVED
