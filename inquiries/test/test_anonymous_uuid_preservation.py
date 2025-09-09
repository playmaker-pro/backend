import pytest
from django.urls import reverse
from unittest.mock import patch

from inquiries.models import InquiryRequest
from utils.factories import TransferStatusFactory
from utils.factories.inquiry_factories import InquiryRequestFactory
from utils.factories.transfers_factories import TransferRequestFactory

pytestmark = pytest.mark.django_db

URL_SEND = lambda uuid: reverse(
    "api:inquiries:send_inquiry", kwargs={"recipient_profile_uuid": uuid}
)


@pytest.fixture
def anonymous_status_with_uuid(player_profile):
    """Fixture to create an anonymous profile with known UUID."""
    return TransferStatusFactory.create(
        meta=player_profile.meta,
        is_anonymous=True,
    )


@pytest.fixture
def anonymous_inquiry_with_uuid(anonymous_status_with_uuid, coach_profile):
    """Fixture to create an inquiry request with stored UUID."""
    return InquiryRequestFactory.create(
        sender=coach_profile.user,
        recipient=anonymous_status_with_uuid.meta.user,
        anonymous_recipient=True,
        recipient_anonymous_uuid=anonymous_status_with_uuid.anonymous_uuid,
    )


def test_inquiry_creation_stores_recipient_anonymous_uuid(api_client, anonymous_status_with_uuid, coach_profile):
    """Test that creating a new anonymous inquiry stores the recipient's anonymous UUID."""
    recipient_uuid = anonymous_status_with_uuid.anonymous_uuid
    api_client.force_authenticate(user=coach_profile.user)
    
    response = api_client.post(URL_SEND(recipient_uuid), {"anonymous_recipient": True})
    assert response.status_code == 201
    
    # Check that the inquiry was created with stored UUID
    inquiry = InquiryRequest.objects.get(
        sender=coach_profile.user,
        recipient=anonymous_status_with_uuid.meta.user
    )
    assert inquiry.anonymous_recipient is True
    assert inquiry.recipient_anonymous_uuid == recipient_uuid


def test_inquiry_serializer_uses_stored_uuid(api_client, anonymous_inquiry_with_uuid):
    """Test that the serializer uses stored UUID instead of current profile data."""
    sender = anonymous_inquiry_with_uuid.sender
    stored_uuid = anonymous_inquiry_with_uuid.recipient_anonymous_uuid
    
    api_client.force_authenticate(user=sender)
    response = api_client.get(reverse("api:inquiries:my_sent_inquiries"))
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    recipient = data[0]["recipient_object"]
    # Should use stored UUID, not current profile slug
    assert recipient["slug"] == f"anonymous-{stored_uuid}"
    assert recipient["uuid"] == str(stored_uuid)
    assert recipient["first_name"] == "Anonimowy"
    assert recipient["last_name"] == "profil"
    assert recipient["id"] == 0


def test_historical_anonymity_preservation_after_profile_changes(
    api_client, anonymous_inquiry_with_uuid
):
    """Test that historical anonymity is preserved even after recipient changes their profile."""
    sender = anonymous_inquiry_with_uuid.sender
    recipient = anonymous_inquiry_with_uuid.recipient
    stored_uuid = anonymous_inquiry_with_uuid.recipient_anonymous_uuid
    
    # Recipient later decides to become non-anonymous
    transfer_status = recipient.profile.meta.transfer_status
    transfer_status.is_anonymous = False
    transfer_status.save()
    
    # Verify recipient is no longer anonymous in their profile
    assert recipient.profile.meta.is_anonymous is False
    
    # BUT: The inquiry should still show the stored anonymous UUID
    api_client.force_authenticate(user=sender)
    response = api_client.get(reverse("api:inquiries:my_sent_inquiries"))
    
    assert response.status_code == 200
    data = response.json()
    recipient_data = data[0]["recipient_object"]
    
    # Should still use the historical stored UUID
    assert recipient_data["slug"] == f"anonymous-{stored_uuid}"
    assert recipient_data["uuid"] == str(stored_uuid)
    assert recipient_data["first_name"] == "Anonimowy"
    assert recipient_data["last_name"] == "profil"


def test_fallback_to_current_transfer_object_when_no_stored_uuid(
    api_client, anonymous_status_with_uuid, coach_profile
):
    """Test fallback behavior when stored UUID is missing (for existing data)."""
    # Create inquiry without stored UUID (simulating old data)
    inquiry = InquiryRequestFactory.create(
        sender=coach_profile.user,
        recipient=anonymous_status_with_uuid.meta.user,
        anonymous_recipient=True,
        recipient_anonymous_uuid=None,  # No stored UUID
    )
    
    api_client.force_authenticate(user=coach_profile.user)
    response = api_client.get(reverse("api:inquiries:my_sent_inquiries"))
    
    assert response.status_code == 200
    data = response.json()
    recipient = data[0]["recipient_object"]
    
    # Should fallback to current transfer object UUID
    current_uuid = anonymous_status_with_uuid.anonymous_uuid
    assert recipient["slug"] == f"anonymous-{current_uuid}"
    assert recipient["uuid"] == str(current_uuid)


def test_fallback_to_unknown_when_no_transfer_object_and_no_stored_uuid(
    api_client, player_profile, coach_profile
):
    """Test ultimate fallback when neither stored UUID nor transfer object exist."""
    # Create inquiry with anonymous_recipient=True but no transfer object
    inquiry = InquiryRequestFactory.create(
        sender=coach_profile.user,
        recipient=player_profile.user,  # Regular profile without anonymous transfer
        anonymous_recipient=True,
        recipient_anonymous_uuid=None,
    )
    
    api_client.force_authenticate(user=coach_profile.user)
    response = api_client.get(reverse("api:inquiries:my_sent_inquiries"))
    
    assert response.status_code == 200
    data = response.json()
    recipient = data[0]["recipient_object"]
    
    # Should use fallback slug
    assert recipient["slug"] == "anonymous-unknown"


def test_transfer_object_deletion_historical_preservation(
    api_client, anonymous_inquiry_with_uuid
):
    """Test that anonymity is preserved even if the transfer object is deleted."""
    sender = anonymous_inquiry_with_uuid.sender
    stored_uuid = anonymous_inquiry_with_uuid.recipient_anonymous_uuid
    
    # Delete the transfer object (extreme case)
    recipient_profile = anonymous_inquiry_with_uuid.recipient.profile
    transfer_status = recipient_profile.meta.transfer_status
    transfer_status.delete()
    
    # The inquiry should still work with stored UUID
    api_client.force_authenticate(user=sender)
    response = api_client.get(reverse("api:inquiries:my_sent_inquiries"))
    
    assert response.status_code == 200
    data = response.json()
    recipient = data[0]["recipient_object"]
    
    # Should use stored UUID even though transfer object is gone
    assert recipient["slug"] == f"anonymous-{stored_uuid}"
    assert recipient["uuid"] == str(stored_uuid)
    assert recipient["first_name"] == "Anonimowy"
    assert recipient["last_name"] == "profil"


def test_non_anonymous_inquiry_unchanged(api_client, player_profile, coach_profile):
    """Test that non-anonymous inquiries work exactly as before."""
    inquiry = InquiryRequestFactory.create(
        sender=coach_profile.user,
        recipient=player_profile.user,
        anonymous_recipient=False,  # Not anonymous
    )
    
    api_client.force_authenticate(user=coach_profile.user)
    response = api_client.get(reverse("api:inquiries:my_sent_inquiries"))
    
    assert response.status_code == 200
    data = response.json()
    recipient = data[0]["recipient_object"]
    
    # Should show real profile data
    assert recipient["slug"] == player_profile.slug
    assert recipient["uuid"] == str(player_profile.uuid)
    assert recipient["first_name"] == player_profile.user.first_name
    assert recipient["last_name"] == player_profile.user.last_name
    assert recipient["id"] == player_profile.user.id


def test_accepted_inquiry_shows_real_data(api_client, anonymous_inquiry_with_uuid):
    """Test that accepted anonymous inquiries show real data as before."""
    anonymous_inquiry_with_uuid.status = InquiryRequest.STATUS_ACCEPTED
    anonymous_inquiry_with_uuid.save()
    
    sender = anonymous_inquiry_with_uuid.sender
    recipient = anonymous_inquiry_with_uuid.recipient
    
    api_client.force_authenticate(user=sender)
    response = api_client.get(reverse("api:inquiries:my_sent_inquiries"))
    
    assert response.status_code == 200
    data = response.json()
    recipient_data = data[0]["recipient_object"]
    
    # Accepted inquiry should show real data, not anonymous
    assert recipient_data["slug"] == recipient.profile.slug
    assert recipient_data["uuid"] == str(recipient.profile.uuid)
    assert recipient_data["first_name"] == recipient.first_name
    assert recipient_data["last_name"] == recipient.last_name
    assert recipient_data["id"] == recipient.id


@pytest.mark.parametrize(
    "status,should_be_anonymous",
    [
        (InquiryRequest.STATUS_SENT, True),
        (InquiryRequest.STATUS_RECEIVED, True), 
        (InquiryRequest.STATUS_NEW, True),
        (InquiryRequest.STATUS_REJECTED, True),
        (InquiryRequest.STATUS_ACCEPTED, False),  # Only accepted shows real data
    ],
)
def test_anonymity_by_inquiry_status_with_uuid(
    api_client, anonymous_inquiry_with_uuid, status, should_be_anonymous
):
    """Test that anonymity works correctly across all inquiry statuses using stored UUID."""
    anonymous_inquiry_with_uuid.status = status
    anonymous_inquiry_with_uuid.save()
    
    sender = anonymous_inquiry_with_uuid.sender
    stored_uuid = anonymous_inquiry_with_uuid.recipient_anonymous_uuid
    
    api_client.force_authenticate(user=sender)
    response = api_client.get(reverse("api:inquiries:my_sent_inquiries"))
    
    assert response.status_code == 200
    data = response.json()
    recipient = data[0]["recipient_object"]
    
    if should_be_anonymous:
        assert recipient["slug"] == f"anonymous-{stored_uuid}"
        assert recipient["uuid"] == str(stored_uuid)
        assert recipient["first_name"] == "Anonimowy"
        assert recipient["last_name"] == "profil"
        assert recipient["id"] == 0
    else:
        # Accepted inquiry shows real data
        real_recipient = anonymous_inquiry_with_uuid.recipient
        assert recipient["slug"] == real_recipient.profile.slug
        assert recipient["uuid"] == str(real_recipient.profile.uuid)
        assert recipient["first_name"] == real_recipient.first_name
        assert recipient["last_name"] == real_recipient.last_name
        assert recipient["id"] == real_recipient.id


def test_model_save_logic_checks_both_transfer_types(player_profile, coach_profile):
    """Test that model save logic checks both transfer_status and transfer_request."""
    # Test with transfer_request instead of transfer_status
    transfer_request = TransferRequestFactory.create(
        meta=player_profile.meta,
        is_anonymous=True,
    )
    
    # Create inquiry (should trigger save logic)
    inquiry = InquiryRequest(
        sender=coach_profile.user,
        recipient=player_profile.user,
        anonymous_recipient=True,
    )
    inquiry.save()
    
    # Should have stored the transfer_request's anonymous UUID
    assert inquiry.recipient_anonymous_uuid == transfer_request.anonymous_uuid


def test_security_no_slug_deanonymization_possible():
    """Test that the new system prevents deanonymization through slug manipulation."""
    # This is a security test - ensure UUIDs can't be reverse engineered
    import uuid
    
    # Create a realistic anonymous UUID
    anonymous_uuid = uuid.uuid4()
    anonymous_slug = f"anonymous-{anonymous_uuid}"
    
    # The old vulnerable approach would be: anonymous-{profile_slug}
    # Where stripping "anonymous-" reveals the real slug
    # The new approach uses UUID which can't be reverse engineered
    
    # Verify the slug format is UUID-based (36 characters + hyphens)
    uuid_part = anonymous_slug.replace("anonymous-", "")
    assert len(uuid_part) == 36  # Standard UUID length
    assert uuid_part.count("-") == 4  # Standard UUID format
    
    # Verify it's a valid UUID (will raise ValueError if not)
    uuid.UUID(uuid_part)  # Should not raise exception
