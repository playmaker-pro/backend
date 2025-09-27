# Generated manually for fixing mixed language issue in TPay payments

from django.db import migrations


def update_product_names_to_polish(apps, schema_editor):
    """
    Update product names from English to Polish base format.
    This aligns with the app's Polish-first approach and enables dynamic profile type appending.
    """
    Product = apps.get_model("premium", "Product")
    
    # Map of current English names to Polish base format
    name_updates = {
        "Monthly premium profile for player": "Miesięczne konto premium dla profilu",
        "Yearly premium profile for player": "Roczne konto premium dla profilu", 
        "Monthly premium profile for profiles other than player": "Miesięczne konto premium dla profilu",
        "Yearly premium profile for profiles other than player": "Roczne konto premium dla profilu",
    }
    
    for english_name, polish_name in name_updates.items():
        updated = Product.objects.filter(name_readable=english_name).update(name_readable=polish_name)
        if updated:
            print(f"Updated {updated} product(s): '{english_name}' -> '{polish_name}'")


def revert_product_names_to_english(apps, schema_editor):
    """
    Revert product names back to English (reverse operation).
    """
    Product = apps.get_model("premium", "Product")
    
    # Map of Polish base names back to English
    name_reverts = {
        "Miesięczne konto premium dla profilu": "Monthly premium profile for player",
        "Roczne konto premium dla profilu": "Yearly premium profile for player",
    }
    
    for polish_name, english_name in name_reverts.items():
        updated = Product.objects.filter(name_readable=polish_name).update(name_readable=english_name)
        if updated:
            print(f"Reverted {updated} product(s): '{polish_name}' -> '{english_name}'")


class Migration(migrations.Migration):
    dependencies = [
        ("premium", "0019_auto_20250201_1100"),
    ]

    operations = [
        migrations.RunPython(
            update_product_names_to_polish,
            reverse_code=revert_product_names_to_english
        ),
    ]
