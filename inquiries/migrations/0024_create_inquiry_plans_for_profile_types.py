# Generated migration for creating new InquiryPlans for profile-specific limits

from django.db import migrations


def create_inquiry_plans(apps, schema_editor):
    """Create or update InquiryPlans for profile-specific limits."""
    InquiryPlan = apps.get_model("inquiries", "InquiryPlan")
    
    # Define new plans to create
    plans = [
        {
            "type_ref": "FREEMIUM_STANDARD",
            "name": "Standard Freemium",
            "limit": 5,
            "description": "Standard freemium inquiry plan (Club, Scout, Coach, Manager, Referee, Other, Guest)",
            "default": False,
            "sort": 100,
        },
        {
            "type_ref": "FREEMIUM_PLAYER",
            "name": "Player Freemium",
            "limit": 10,
            "description": "Player freemium inquiry plan",
            "default": False,
            "sort": 101,
        },
        {
            "type_ref": "PREMIUM_STANDARD",
            "name": "Standard Premium",
            "limit": 30,
            "description": "Standard premium inquiry plan (Club, Scout, Coach, Manager, Referee, Other, Guest) - 30 inquiries per 3 months",
            "default": False,
            "sort": 102,
        },
        {
            "type_ref": "PREMIUM_PLAYER",
            "name": "Player Premium",
            "limit": 30,
            "description": "Player premium inquiry plan (unlimited with 30/month safety limit)",
            "default": False,
            "sort": 103,
        },
    ]
    
    for plan_data in plans:
        type_ref = plan_data["type_ref"]
        
        # Check if plan with this type_ref already exists
        existing_plan = InquiryPlan.objects.filter(type_ref=type_ref).first()
        if existing_plan:
            # Update existing plan
            for key, value in plan_data.items():
                if key != "type_ref":  # Don't update the lookup field
                    setattr(existing_plan, key, value)
            existing_plan.save()
        else:
            # Check if a plan with same (name, limit) exists but different type_ref
            conflicting_plan = InquiryPlan.objects.filter(
                name=plan_data["name"],
                limit=plan_data["limit"]
            ).first()
            
            if conflicting_plan:
                # Update the conflicting plan's type_ref and other fields
                for key, value in plan_data.items():
                    setattr(conflicting_plan, key, value)
                conflicting_plan.save()
            else:
                # Create new plan
                InquiryPlan.objects.create(**plan_data)


class Migration(migrations.Migration):

    dependencies = [
        ("inquiries", "0023_inquiryrequest_recipient_anonymous_uuid"),
    ]

    operations = [
        migrations.RunPython(create_inquiry_plans),
    ]
