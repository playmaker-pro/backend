import json

from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

from inquiries.models import InquiryContact, InquiryRequest
from utils.factories import GuestProfileFactory
from utils.test.test_utils import UserManager

sender_contact_data = {
    "phone": "+123456789",
    "email": "sender@playmaker.pro",
}
recipient_contact_data = {
    "phone": "+987654321",
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


class TestInquiriesAPI(APITestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.sender_manager = UserManager(self.client)
        self.recipient_manager = UserManager(self.client)
        self.sender_obj = self.sender_manager.create_superuser(
            mute_signals=False, email="sender@sender.com"
        )
        self.recipient_obj = self.recipient_manager.create_superuser(
            mute_signals=False, email="recipient@recipient.com"
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
        assert response.data == data

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

        accept_response = self.client.post(
            URL_ACCEPT(obj.pk),
            **self.recipient_headers,
        )  # Accept request by recipient

        assert accept_response.status_code == 200
        obj.refresh_from_db()
        assert obj.status == InquiryRequest.STATUS_ACCEPTED

        contacts_response = self.client.get(
            URL_MY_CONTACTS,
            **self.sender_headers,
        )  # Get all sender contacts, list should include recipient
        assert contacts_response.status_code == 200
        assert len(contacts_response.data) == 1

        # Check contacts data correctly exchanged
        assert contacts_response.data[0].get(
            "body"
        ) == InquiryContact.parse_custom_body(*sender_contact_data.values())
        assert contacts_response.data[0].get(
            "body_recipient"
        ) == InquiryContact.parse_custom_body(*recipient_contact_data.values())

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
