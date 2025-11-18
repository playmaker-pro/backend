# Generated manually for new pricing structure and product lineup

from django.db import migrations


def update_premium_products(apps, schema_editor):
    """
    Update premium products with new pricing structure:
    - Player: 29.99 PLN/month, 99 PLN/year
    - Guest: 29.99 PLN/month, 99 PLN/year (new products)
    - Other (Club/Coach/etc.): 299 PLN/quarter (3 months), 399 PLN/year (new products)
    - Hide old PREMIUM_PROFILE_* products (kept for existing subscriptions)
    """
    Product = apps.get_model("premium", "Product")
    
    # 1. Update Player product prices (keep same name_readable)
    Product.objects.filter(name='PLAYER_PREMIUM_PROFILE_MONTH').update(price=29.99)
    Product.objects.filter(name='PLAYER_PREMIUM_PROFILE_YEAR').update(price=99.00)
    
    # 2. Hide old generic products (kept for existing subscriptions)
    Product.objects.filter(
        name__in=['PREMIUM_PROFILE_MONTH', 'PREMIUM_PROFILE_YEAR']
    ).update(visible=False)
    
    # 3. Create Guest premium products (same pricing as Player)
    Product.objects.get_or_create(
        name="GUEST_PREMIUM_PROFILE_MONTH",
        defaults={
            "ref": "PREMIUM",
            "price": 29.99,
            "visible": True,
            "name_readable": "Miesięczne konto premium dla profilu"
        }
    )
    
    Product.objects.get_or_create(
        name="GUEST_PREMIUM_PROFILE_YEAR",
        defaults={
            "ref": "PREMIUM",
            "price": 99.00,
            "visible": True,
            "name_readable": "Roczne konto premium dla profilu"
        }
    )
    
    # 4. Create Other (Club/Coach/etc.) premium products
    Product.objects.get_or_create(
        name="OTHER_PREMIUM_PROFILE_QUARTER",
        defaults={
            "ref": "PREMIUM",
            "price": 299.00,
            "visible": True,
            "name_readable": "Kwartalne konto premium dla profilu"  # 3 months
        }
    )
    
    Product.objects.get_or_create(
        name="OTHER_PREMIUM_PROFILE_YEAR",
        defaults={
            "ref": "PREMIUM",
            "price": 399.00,
            "visible": True,
            "name_readable": "Roczne konto premium dla profilu"
        }
    )


def reverse_migration(apps, schema_editor):
    """
    Reverse changes:
    - Restore old product visibility
    - Remove new products
    - Restore old prices
    """
    Product = apps.get_model("premium", "Product")
    
    # Restore old products visibility
    Product.objects.filter(
        name__in=['PREMIUM_PROFILE_MONTH', 'PREMIUM_PROFILE_YEAR']
    ).update(visible=True)
    
    # Remove new products
    Product.objects.filter(
        name__in=[
            'GUEST_PREMIUM_PROFILE_MONTH',
            'GUEST_PREMIUM_PROFILE_YEAR',
            'OTHER_PREMIUM_PROFILE_QUARTER',
            'OTHER_PREMIUM_PROFILE_YEAR'
        ]
    ).delete()
    
    # Restore old Player prices
    Product.objects.filter(name='PLAYER_PREMIUM_PROFILE_MONTH').update(price=9.99)
    Product.objects.filter(name='PLAYER_PREMIUM_PROFILE_YEAR').update(price=99.99)


class Migration(migrations.Migration):
    dependencies = [
        ("premium", "0020_update_product_names_to_polish"),
    ]

    operations = [
        migrations.RunPython(update_premium_products, reverse_code=reverse_migration),
    ]
