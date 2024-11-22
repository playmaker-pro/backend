from django.conf import settings
from django.db import models
from django.utils import timezone

from premium.utils import get_date_days_after


class PremiumProfile(models.Model):
    product = models.OneToOneField(
        "PremiumProduct", on_delete=models.PROTECT, related_name="premium"
    )
    valid_since = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()

    def refresh(self) -> None:
        """Refresh the validity of the premium profile."""
        self.valid_since = timezone.now()
        self.valid_until = get_date_days_after(self.valid_since, days=30)
        self.setup()
        self.save()

    def save(self, *args, **kwargs) -> None:
        if self.pk is None:
            self.valid_until = get_date_days_after(timezone.now(), days=30)

        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        return self.valid_until > timezone.now()

    def setup(self) -> None:
        """Setup the premium profile."""
        self.product.setup_premium_products()


class CalculatePMScoreProduct(models.Model):
    product = models.OneToOneField(
        "PremiumProduct", on_delete=models.CASCADE, related_name="calculate_pm_score"
    )
    player = models.ForeignKey(
        "profiles.PlayerProfile", on_delete=models.CASCADE, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True
    )

    old_value = models.PositiveBigIntegerField(null=True, blank=True)
    new_value = models.PositiveBigIntegerField(null=True, blank=True)

    awaiting_approval = models.BooleanField(default=True)

    def refresh(self) -> None:
        """Renew the calculation of the PM score."""
        self.created_at = timezone.now()
        self.approved_by = None
        self.old_value = self.new_value
        self.new_value = None
        self.awaiting_approval = True
        self.save()

    def approve(self, admin_user: settings.AUTH_USER_MODEL, new_value: int) -> None:
        """Approve the calculation of the PM score."""
        self.approved_by = admin_user
        self.new_value = new_value
        self.awaiting_approval = False
        self.save()

    def save(self, *args, **kwargs):
        if self.pk is None:
            if self.product.profile.__class__.__name__ != "PlayerProfile":
                raise ValueError("Product is available only for PlayerProfile.")

            self.player = self.product.profile
            self.old_value = self.player.playermetrics.pm_score

        super().save(*args, **kwargs)


class PromoteProfileProduct(models.Model):
    product = models.OneToOneField(
        "PremiumProduct", on_delete=models.PROTECT, related_name="promotion"
    )
    days_count = models.PositiveIntegerField(default=30)
    valid_since = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.valid_until = get_date_days_after(timezone.now(), self.days_count)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.valid_until > timezone.now()

    @property
    def days_left(self):
        return (self.valid_until - timezone.now()).days

    def refresh(self) -> None:
        """Refresh the validity of the promotion."""
        self.valid_since = timezone.now()
        self.valid_until = get_date_days_after(self.valid_since, self.days_count)
        self.save()


class PremiumInquiriesProduct(models.Model):
    product = models.OneToOneField(
        "PremiumProduct", on_delete=models.CASCADE, related_name="inquiries"
    )

    valid_since = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.valid_until = get_date_days_after(timezone.now(), days=30)
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        return self.valid_until > timezone.now()

    def refresh(self) -> None:
        """Refresh the validity of the premium inquiries."""
        self.valid_since = timezone.now()
        self.valid_until = get_date_days_after(self.valid_since, days=30)
        self.save()


class PremiumProduct(models.Model):
    profile_uuid = models.UUIDField(unique=True, blank=True, null=True)

    @property
    def user(self):
        return self.profile.user

    @property
    def profile(self):
        for profile_type in [
            "playerprofile",
            "clubprofile",
            "coachprofile",
            "guestprofile",
            "managerprofile",
            "scoutprofile",
            "refereeprofile",
            "otherprofile",
        ]:
            profile = getattr(self, profile_type, None)
            if profile:
                return profile

    @property
    def is_profile_premium(self) -> bool:
        """Check if profile is premium."""
        premium_obj = getattr(self, "premium", None)
        if premium_obj:
            return premium_obj.is_active
        return False

    @property
    def is_profile_promoted(self) -> bool:
        """Check if profile is promoted."""
        promotion_obj = getattr(self, "promotion", None)
        if promotion_obj:
            return promotion_obj.is_active
        return False

    @property
    def is_premium_inquiries_active(self) -> bool:
        """Check if premium inquiries are active."""
        inquiries_obj = getattr(self, "inquiries", None)
        if inquiries_obj:
            return inquiries_obj.is_active
        return False

    def __str__(self):
        return (
            f"{self.profile} -- {'PREMIUM' if self.is_profile_premium else 'FREEMIUM'}"
        )

    def setup_premium_profile(self) -> "PremiumProfile":
        """Create/refresh premium profile"""
        premium, premium_created = PremiumProfile.objects.get_or_create(product=self)

        if not premium_created:
            premium.refresh()

        return premium

    def setup_premium_products(self) -> None:
        """Create/refresh all premium products for the profile."""
        inquiries, inquiries_created = PremiumInquiriesProduct.objects.get_or_create(
            product=self
        )
        promotion, promotion_created = PromoteProfileProduct.objects.get_or_create(
            product=self
        )

        if not inquiries_created:
            inquiries.refresh()

        if not promotion_created:
            promotion.refresh()

        if self.profile.__class__.__name__ == "PlayerProfile":
            calculate_pms, calculate_pms_created = (
                CalculatePMScoreProduct.objects.get_or_create(product=self)
            )

            if not calculate_pms_created:
                calculate_pms.refresh()

    def save(self, *args, **kwargs):
        if self.profile_uuid is None and self.profile:
            self.uuid = self.profile.uuid
        super().save(*args, **kwargs)


class Product(models.Model):
    class ProductReference(models.TextChoices):
        PREMIUM = "PREMIUM", "PREMIUM"
        INQUIRIES = "INQUIRIES", "INQUIRIES"

    name = models.CharField(max_length=30, unique=True)
    name_readable = models.CharField(max_length=50)
    price = models.DecimalField(decimal_places=2, max_digits=5)
    ref = models.CharField(max_length=30, choices=ProductReference.choices)
    visible = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.ref} -- {self.name} -- {self.name_readable} -- {self.price}"
