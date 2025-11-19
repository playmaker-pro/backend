# Generated migration for reassigning existing UserInquiry plans to new profile-specific plans

from django.db import migrations


def reassign_inquiry_plans(apps, schema_editor):
    """
    Reassign existing UserInquiry records to new profile-specific plans.
    
    Maps users with basic plan or any old plan to appropriate freemium plan based on their profile type.
    """
    UserInquiry = apps.get_model("inquiries", "UserInquiry")
    InquiryPlan = apps.get_model("inquiries", "InquiryPlan")
    User = apps.get_model("users", "User")
    
    # Get the new freemium plans
    try:
        freemium_standard = InquiryPlan.objects.get(type_ref="FREEMIUM_STANDARD")
        freemium_player = InquiryPlan.objects.get(type_ref="FREEMIUM_PLAYER")
    except InquiryPlan.DoesNotExist:
        # New plans not created yet, skip
        return
    
    # Get all UserInquiry records that don't have a new plan yet
    # (i.e., they still have old plans like Basic or other)
    old_type_refs = [None, "BASIC", "PREMIUM_INQUIRIES_L", "PREMIUM_INQUIRIES_XL", "PREMIUM_INQUIRIES_XXL"]
    user_inquiries_to_update = UserInquiry.objects.exclude(
        plan__type_ref__in=["FREEMIUM_STANDARD", "FREEMIUM_PLAYER", "PREMIUM_STANDARD", "PREMIUM_PLAYER"]
    )
    
    # Process all users to assign correct plans
    for user in User.objects.all():
        if not hasattr(user, 'userinquiry'):
            continue
        
        try:
            user_inquiry = user.userinquiry
            
            # Check if user has a profile
            if not hasattr(user, 'profile') or user.profile is None:
                continue
            
            # Determine profile type
            profile_type = user.profile.__class__.__name__
            
            # Check if user is premium
            is_premium = user.profile.is_premium if hasattr(user.profile, 'is_premium') else False
            
            # Don't update if already has new plan
            if user_inquiry.plan and user_inquiry.plan.type_ref in ["FREEMIUM_STANDARD", "FREEMIUM_PLAYER", "PREMIUM_STANDARD", "PREMIUM_PLAYER"]:
                continue
            
            # Assign appropriate plan
            if profile_type == "PlayerProfile":
                user_inquiry.plan = freemium_player
            else:
                # All other profiles
                user_inquiry.plan = freemium_standard
            
            # Update limit_raw to match plan.limit
            user_inquiry.limit_raw = user_inquiry.plan.limit
            user_inquiry.save()
        except Exception:
            # Skip problematic records
            continue


class Migration(migrations.Migration):

    dependencies = [
        ("inquiries", "0024_create_inquiry_plans_for_profile_types"),
    ]

    operations = [
        migrations.RunPython(reassign_inquiry_plans, reverse_code=migrations.RunPython.noop),
    ]
