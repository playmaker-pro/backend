# Generated migration for creating new InquiryPlans for profile-specific limits

from django.db import migrations


def create_inquiry_plans(apps, schema_editor):
    """Create new InquiryPlans for profile-specific limits."""
    InquiryPlan = apps.get_model("inquiries", "InquiryPlan")
    
    # 1. Standard Freemium (limit=5)
    InquiryPlan.objects.get_or_create(
        type_ref="FREEMIUM_STANDARD",
        defaults={
            "name": "Standard Freemium",
            "limit": 5,
            "description": "Standard freemium inquiry plan (Club, Scout, Coach, Manager, Referee, Other, Guest)",
            "default": False,
            "sort": 100,
        }
    )
    
    # 2. Player Freemium (limit=10)
    InquiryPlan.objects.get_or_create(
        type_ref="FREEMIUM_PLAYER",
        defaults={
            "name": "Player Freemium",
            "limit": 10,
            "description": "Player freemium inquiry plan",
            "default": False,
            "sort": 101,
        }
    )
    
    # 3. Standard Premium (limit=30, reset=90 days)
    InquiryPlan.objects.get_or_create(
        type_ref="PREMIUM_STANDARD",
        defaults={
            "name": "Standard Premium",
            "limit": 30,
            "description": "Standard premium inquiry plan (Club, Scout, Coach, Manager, Referee, Other, Guest) - 30 inquiries per 3 months",
            "default": False,
            "sort": 102,
        }
    )
    
    # 4. Player Premium (limit=30 for safety, unlimited behavior in PremiumInquiriesProduct)
    InquiryPlan.objects.get_or_create(
        type_ref="PREMIUM_PLAYER",
        defaults={
            "name": "Player Premium",
            "limit": 30,
            "description": "Player premium inquiry plan (unlimited with 30/month safety limit)",
            "default": False,
            "sort": 103,
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ("inquiries", "0023_inquiryrequest_recipient_anonymous_uuid"),
    ]

    operations = [
        migrations.RunPython(create_inquiry_plans),
    ]
