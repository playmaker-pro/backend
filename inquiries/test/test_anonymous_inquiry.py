import pytest
from django.urls import reverse

from inquiries.models import InquiryRequest
from utils.factories import TransferStatusFactory
from utils.factories.inquiry_factories import InquiryRequestFactory
from utils.factories.transfers_factories import TransferRequestFactory

pytestmark = pytest.mark.django_db
URL_SEND = lambda uuid: reverse(
    "api:inquiries:send_inquiry", kwargs={"recipient_profile_uuid": uuid}
)


@pytest.fixture
def anonymous_status(player_profile):
    """Fixture to create an anonymous profile."""
    return TransferStatusFactory.create(
        meta=player_profile.meta,
        is_anonymous=True,
    )


@pytest.fixture
def anonymous_request(coach_profile):
    """Fixture to create an inquiry request to an anonymous profile."""
    return TransferRequestFactory.create(
        meta=coach_profile.meta,
        is_anonymous=True,
    )


@pytest.fixture
def anonymous_inquiry_request(anonymous_status, coach_profile):
    """Fixture to create an inquiry request to an anonymous profile."""
    return InquiryRequestFactory.create(
        sender=coach_profile.user,
        recipient=anonymous_status.meta.user,
        anonymous_recipient=True,
        recipient_anonymous_uuid=anonymous_status.anonymous_uuid,
    )


def test_send_inquiry_to_anonymous_status(api_client, anonymous_status, coach_profile):
    """Test sending an inquiry to an anonymous profile."""
    recipient_uuid = anonymous_status.meta.transfer_object.anonymous_uuid
    api_client.force_authenticate(user=coach_profile.user)
    response = api_client.post(URL_SEND(recipient_uuid), {"anonymous_recipient": True})

    assert response.status_code == 201

    ir = coach_profile.user.sender_request_recipient.first()

    assert ir.anonymous_recipient is True
    assert ir.recipient.profile.meta.transfer_object.anonymous_uuid == recipient_uuid
    assert (
        ir.recipient.profile.meta.transfer_object.anonymous_slug
        == f"anonymous-{recipient_uuid}"
    )


def test_send_inquiry_to_anonymous_request(
    api_client, anonymous_request, player_profile
):
    """Test sending an inquiry to an existing anonymous request."""
    recipient_uuid = anonymous_request.meta.profile.meta.transfer_object.anonymous_uuid
    api_client.force_authenticate(user=player_profile.user)
    response = api_client.post(URL_SEND(recipient_uuid), {"anonymous_recipient": True})

    assert response.status_code == 201

    ir = player_profile.user.sender_request_recipient.first()

    assert ir.anonymous_recipient is True
    assert ir.recipient.profile.meta.transfer_object.anonymous_uuid == recipient_uuid
    assert (
        ir.recipient.profile.meta.transfer_object.anonymous_slug
        == f"anonymous-{recipient_uuid}"
    )


@pytest.mark.parametrize(
    "status,is_visible",
    [
        (InquiryRequest.STATUS_SENT, False),
        (InquiryRequest.STATUS_REJECTED, False),
        (InquiryRequest.STATUS_NEW, False),
        (InquiryRequest.STATUS_RECEIVED, False),
        (InquiryRequest.STATUS_ACCEPTED, True),
    ],
)
def test_get_my_sent_inquiries_with_anonymous_one_different_status(
    api_client, anonymous_inquiry_request, status, is_visible
):
    """Test retrieving sent inquiries to an anonymous profile."""
    anonymous_inquiry_request.status = status
    anonymous_inquiry_request.save()
    coach_profile = anonymous_inquiry_request.sender.profile
    player_profile = anonymous_inquiry_request.recipient.profile
    api_client.force_authenticate(user=coach_profile.user)
    response = api_client.get(reverse("api:inquiries:my_sent_inquiries"))

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    recipient = data[0]["recipient_object"]

    if is_visible:
        assert recipient["slug"] == player_profile.slug
        assert recipient["uuid"] == str(player_profile.uuid)
        assert recipient["first_name"] == player_profile.user.first_name
        assert recipient["last_name"] == player_profile.user.last_name
        assert recipient["id"] > 0
        assert recipient["team_history_object"]
    else:
        # With the new system, we expect the stored UUID from the inquiry
        stored_uuid = anonymous_inquiry_request.recipient_anonymous_uuid
        assert recipient["slug"] == f"anonymous-{stored_uuid}"
        assert recipient["uuid"] == str(stored_uuid)
        assert recipient["id"] == 0
        assert recipient["first_name"] == "Anonimowy"
        assert recipient["last_name"] == "profil"
        assert recipient["picture"] is None
        assert recipient["team_history_object"] is None


def test_forbid_to_send_inquiry_to_self_anonymous_profile(api_client, anonymous_status):
    """Test that a user cannot send an inquiry to themselves."""
    recipient_user = anonymous_status.meta.user
    recipient_uuid = anonymous_status.meta.transfer_object.anonymous_uuid
    api_client.force_authenticate(user=recipient_user)
    response = api_client.post(URL_SEND(recipient_uuid), {"anonymous_recipient": True})

    assert response.status_code == 400
    assert response.json() == {"error": "You can't send inquiry to yourself"}


def test_anonymous_profile_endpoint_after_user_changes_status(
    api_client, anonymous_status, coach_profile
):
    """Test that anonymous profile endpoint always shows anonymous data, even after user changes status."""
    recipient_anonymous_uuid = anonymous_status.meta.transfer_object.anonymous_uuid
    
    # Send inquiry to anonymous recipient (to establish the link)
    api_client.force_authenticate(user=coach_profile.user)
    response = api_client.post(
        URL_SEND(recipient_anonymous_uuid), {"anonymous_recipient": True}
    )
    assert response.status_code == 201
    
    # Later: recipient changes to non-anonymous
    anonymous_status.is_anonymous = False
    anonymous_status.save()
    
    # Verify recipient is no longer anonymous
    assert anonymous_status.meta.is_anonymous is False
    
    # BUT: accessing via anonymous URL should still show anonymous data
    anonymous_slug = f"anonymous-{recipient_anonymous_uuid}"
    response = api_client.get(
        reverse("api:profiles:get_profile_by_slug", kwargs={"profile_slug": anonymous_slug})
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should still be anonymous despite user changing status
    assert data["user"]["first_name"] == "Anonimowy"
    assert data["user"]["last_name"] == "profil"
    assert data["user"]["id"] == 0
    assert data["uuid"] == str(recipient_anonymous_uuid)
    assert data["slug"] == anonymous_slug
    assert data["user"]["picture"] is None
    assert data["team_history_object"] is None
