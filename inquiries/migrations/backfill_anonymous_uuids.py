# Generated data migration to backfill recipient_anonymous_uuid field
# This should be run after the schema migration that adds the field

from django.db import migrations


def backfill_anonymous_uuids(apps, schema_editor):
    """
    Backfill recipient_anonymous_uuid field for existing anonymous inquiries.

    This migration looks for existing InquiryRequest objects where:
    - anonymous_recipient=True
    - recipient_anonymous_uuid is NULL

    For each such inquiry, it attempts to find the recipient's transfer object
    and copies the anonymous_uuid for historical preservation.
    """
    InquiryRequest = apps.get_model('inquiries', 'InquiryRequest')

    # Find all anonymous inquiries without stored UUIDs
    anonymous_inquiries = InquiryRequest.objects.filter(
        anonymous_recipient=True,
        recipient_anonymous_uuid__isnull=True
    )

    updated_count = 0
    failed_count = 0

    for inquiry in anonymous_inquiries:
        try:
            transfer_object = None

            # Check if recipient has profile and meta
            if hasattr(inquiry.recipient, 'profile') and hasattr(inquiry.recipient.profile, 'meta'):
                profile_meta = inquiry.recipient.profile.meta

                # Check transfer_status first
                if hasattr(profile_meta, 'transfer_status'):
                    transfer_status = profile_meta.transfer_status
                    if transfer_status.is_anonymous:
                        transfer_object = transfer_status

                # Check transfer_request if transfer_status not found or not anonymous
                if not transfer_object and hasattr(profile_meta, 'transfer_request'):
                    transfer_request = profile_meta.transfer_request
                    if transfer_request.is_anonymous:
                        transfer_object = transfer_request

            # Store the anonymous UUID if found
            if transfer_object:
                inquiry.recipient_anonymous_uuid = transfer_object.anonymous_uuid
                inquiry.save(update_fields=['recipient_anonymous_uuid'])
                updated_count += 1
            else:
                failed_count += 1

        except Exception as e:
            # Log error but continue with other inquiries
            print(f"Failed to backfill UUID for inquiry {inquiry.id}: {e}")
            failed_count += 1

    print(f"Backfill complete: {updated_count} inquiries updated, {failed_count} failed/skipped")


def reverse_backfill_anonymous_uuids(apps, schema_editor):
    """
    Reverse migration - clear the recipient_anonymous_uuid field.
    """
    InquiryRequest = apps.get_model('inquiries', 'InquiryRequest')
    InquiryRequest.objects.filter(
        anonymous_recipient=True,
        recipient_anonymous_uuid__isnull=False
    ).update(recipient_anonymous_uuid=None)


class Migration(migrations.Migration):
    dependencies = [
        ('inquiries', '0023_inquiryrequest_recipient_anonymous_uuid'),
    ]

    operations = [
        migrations.RunPython(
            backfill_anonymous_uuids,
            reverse_backfill_anonymous_uuids,
        ),
    ]