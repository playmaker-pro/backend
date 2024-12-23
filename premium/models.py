import math
from decimal import ROUND_DOWN, Decimal
from enum import Enum

from django.conf import settings
from django.db import models
from django.utils import timezone

from inquiries.models import InquiryPlan
from payments.models import Transaction
from premium.utils import get_date_days_after


class PremiumType(Enum):
    YEAR = "YEAR"
    MONTH = "MONTH"
    TRIAL = "TRIAL"

    @property
    def period(self) -> int:
        if self == self.YEAR:
            return 365
        elif self == self.MONTH:
            return 30
        elif self == self.TRIAL:
            return 7


class PremiumProfile(models.Model):
    period = models.PositiveIntegerField(default=7, help_text="Period in days")

    product = models.OneToOneField(
        "PremiumProduct", on_delete=models.PROTECT, related_name="premium"
    )
    valid_since = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(blank=True, null=True)

    def _fresh_init(self) -> None:
        """Initialize the premium profile."""
        self.valid_since = timezone.now()
        self.valid_until = get_date_days_after(self.valid_since, days=self.period)

    def _refresh(self) -> None:
        """Refresh the validity of the premium profile."""
        if self.is_active:
            self.valid_until = get_date_days_after(self.valid_until, days=self.period)
        else:
            self._fresh_init()
        self.save()

    @property
    def is_active(self) -> bool:
        if not self.valid_until:
            return False
        return self.valid_until > timezone.now()

    def setup(self, premium_type: PremiumType = PremiumType.TRIAL) -> None:
        """Setup the premium profile."""
        self.period = premium_type.period
        self._refresh()
        self.product.setup_premium_products(premium_type)


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
    days_count = models.PositiveIntegerField(default=7)
    valid_since = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    def _fresh_init(self) -> None:
        """Initialize the promotion."""
        self.valid_since = timezone.now()
        self.valid_until = get_date_days_after(self.valid_since, days=self.days_count)

    @property
    def is_active(self):
        if not self.valid_until:
            return False
        return self.valid_until > timezone.now()

    @property
    def days_left(self):
        return math.ceil((self.valid_until - timezone.now()).total_seconds() / 86400)

    def refresh(self, premium_type: PremiumType) -> None:
        """Refresh the validity of the promotion."""
        self.days_count = premium_type.period
        if self.is_active:
            self.valid_until = get_date_days_after(self.valid_until, self.days_count)
        else:
            self._fresh_init()
        self.save()


class PremiumInquiriesProduct(models.Model):
    product = models.OneToOneField(
        "PremiumProduct", on_delete=models.CASCADE, related_name="inquiries"
    )

    valid_since = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(blank=True, null=True)

    def _fresh_init(self, period: int) -> None:
        """Initialize the premium inquiries."""
        self.valid_since = timezone.now()
        self.valid_until = get_date_days_after(self.valid_since, days=period)

    @property
    def is_active(self) -> bool:
        if not self.valid_until:
            return False
        return self.valid_until > timezone.now()

    def refresh(self, premium_type: PremiumType) -> None:
        """Refresh the validity of the premium inquiries."""
        period = premium_type.period
        if self.is_active:
            self.valid_until = get_date_days_after(self.valid_until, days=period)
        else:
            self._fresh_init(period)
        self.save()


class PremiumProduct(models.Model):
    profile_uuid = models.UUIDField(unique=True, blank=True, null=True)
    trial_tested = models.BooleanField(default=False, help_text="Trial already tested?")

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

    def setup_premium_profile(
        self, premium_type: PremiumType = PremiumType.TRIAL
    ) -> "PremiumProfile":
        """Create/refresh premium profile"""
        premium, created = PremiumProfile.objects.get_or_create(product=self)

        if not created:
            if self.trial_tested and premium_type == PremiumType.TRIAL:
                raise ValueError("Trial already tested.")
            elif premium.is_active and premium_type == PremiumType.TRIAL:
                raise ValueError(
                    "Cannot activate trial on active premium subscription."
                )

        premium.setup(premium_type)

        if premium_type == PremiumType.TRIAL:
            self.trial_tested = True
            self.save(update_fields=["trial_tested"])

        return premium

    def setup_premium_products(
        self, premium_type: PremiumType = PremiumType.TRIAL
    ) -> None:
        """Create/refresh all premium products for the profile."""
        inquiries, _ = PremiumInquiriesProduct.objects.get_or_create(product=self)
        promotion, _ = PromoteProfileProduct.objects.get_or_create(product=self)

        inquiries.refresh(premium_type)
        promotion.refresh(premium_type)

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
    name_readable = models.CharField(max_length=100)
    price = models.DecimalField(decimal_places=2, max_digits=5)
    ref = models.CharField(max_length=30, choices=ProductReference.choices)
    visible = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.ref} -- {self.name} -- {self.name_readable} -- {self.price}"

    def apply_product_for_transaction(self, transaction: Transaction) -> None:
        if self.ref == Product.ProductReference.PREMIUM:
            premium_type = (
                PremiumType.YEAR if self.name.endswith("_YEAR") else PremiumType.MONTH
            )
            premium = transaction.user.profile.premium_products.setup_premium_profile(
                premium_type
            )
        elif self.ref == Product.ProductReference.INQUIRIES:
            plan = InquiryPlan.objects.get(type_ref=self.name)
            transaction.user.userinquiry.set_new_plan(plan)

    def price_per_cycle(self) -> Decimal:
        """
        Some prices are defined as yearly, we need to display price by cycle.

        """
        if self.name.endswith("_YEAR") and self.ref == self.ProductReference.PREMIUM:
            return (self.price / 12).quantize(Decimal("1.00"), rounding=ROUND_DOWN)
        return self.price

    @property
    def player_only(self) -> bool:
        return self.name.startswith("PLAYER_")
