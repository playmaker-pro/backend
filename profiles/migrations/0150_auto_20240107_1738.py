from django.db import migrations


def update_formation_values(apps, schema_editor) -> None:
    """
    Migrates existing formation values in PlayerProfile and CoachProfile models
    to new formation standards.

    This function updates the 'formation' and 'formation_alt' fields in the PlayerProfile
    and 'formation' in CoachProfile models.
    Formations present in the mapping dictionary are updated to their new values,
    while formations not present in the mapping are set to null.
    """

    PlayerProfile = apps.get_model("profiles", "PlayerProfile")
    CoachProfile = apps.get_model("profiles", "CoachProfile")

    mapping = {
        "5-3-2": "1-5-3-2",
        "5-4-1": "1-5-4-1",
        "4-4-2": "1-4-4-2",
        "4-3-3": "1-4-3-3",
        "4-2-3-1": "1-4-2-3-1",
        "4-1-4-1": "1-4-1-4-1",
        "3-5-2": "1-5-2-3",
        "3-4-3": "1-3-4-3",
        "4-3-1-2": "1-4-3-1-2",
    }

    # Update PlayerProfile formations
    for profile in PlayerProfile.objects.all():
        if profile.formation in mapping:
            profile.formation = mapping[profile.formation]
        else:
            profile.formation = None

        if profile.formation_alt in mapping:
            profile.formation_alt = mapping[profile.formation_alt]
        else:
            profile.formation_alt = None

        profile.save()

    # Update CoachProfile formations
    for profile in CoachProfile.objects.all():
        if profile.formation in mapping:
            profile.formation = mapping[profile.formation]
        else:
            profile.formation = None

        profile.save()


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0149_auto_20240107_1738"),
    ]

    operations = [
        migrations.RunPython(
            update_formation_values,
        ),
    ]
