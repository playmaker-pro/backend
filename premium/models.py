import math
from datetime import datetime, timedelta
from decimal import ROUND_DOWN, Decimal
from enum import Enum
from typing import Optional

from django.conf import settings
from django.db import models
from django.utils import timezone

from mailing.schemas import EmailTemplateRegistry
from mailing.services import MailingService
from payments.models import Transaction
from premium.tasks import premium_expired
from premium.utils import get_date_days_after


class PremiumType(Enum):
    YEAR = "YEAR"
    MONTH = "MONTH"
    TRIAL = "TRIAL"
    CUSTOM = "CUSTOM"

    @property
    def map(self) -> dict:
        return {
            self.YEAR: 365,
            self.MONTH: 30,
            self.TRIAL: 3,
        }

    @property
    def period(self) -> Optional[int]:
        try:
            return self.map[self]
        except KeyError:
            return

    @classmethod
    def get_period_type(cls, period: int) -> "PremiumType":
        type_map = {3: cls.TRIAL, 30: cls.MONTH, 365: cls.YEAR}
        try:
            return type_map[period].value
        except KeyError:
            return cls.CUSTOM.value


class PremiumProfile(models.Model):
    _default_trial_period = 3

    period = models.PositiveIntegerField(
        default=_default_trial_period, help_text="Period in days"
    )
    is_trial = models.BooleanField(default=False)
    product = models.OneToOneField(
        "PremiumProduct", on_delete=models.PROTECT, related_name="premium"
    )
    valid_since = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)

    @property
    def subscription_lifespan(self) -> timedelta:
        return self.valid_until.date() - self.valid_since.date()

    def sent_email_that_premium_expired(self) -> None:
        mail_content = EmailTemplateRegistry.PREMIUM_EXPIRED()
        MailingService(mail_content).send_mail(self.product.user)

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
        elif self.valid_until <= timezone.now():
            premium_expired.delay(self.product.pk)
            self.valid_until = None
            self.save()

            return False
        return True

    def setup(self, premium_type: PremiumType = PremiumType.TRIAL) -> None:
        """Setup the premium profile."""
        self.is_trial = premium_type == PremiumType.TRIAL
        self.period = premium_type.period
        self._refresh()
        self.product.setup_premium_products(premium_type)

    def setup_by_days(self, days: int) -> None:
        """Setup the premium profile by days."""
        self.period = days
        self._refresh()
        self.product.setup_premium_products(PremiumType.CUSTOM, period=days)

    def save(self, *args, **kwargs) -> None:
        if not self.valid_since:
            self.valid_since = timezone.now()
        super().save(*args, **kwargs)


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

    @property
    def awaiting_approval(self):
        if self.product.is_profile_premium:
            return (
                self.new_value is None
                or timezone.now() > self.updated_at + timedelta(days=30)
            )
        else:
            return self.new_value is None

    def refresh(self) -> None:
        """Renew the calculation of the PM score."""
        self.created_at = timezone.now()
        self.approved_by = None
        self.old_value = self.new_value
        self.new_value = None
        self.save()

    def approve(self, admin_user: settings.AUTH_USER_MODEL, new_value: int) -> None:
        """Approve the calculation of the PM score."""
        self.approved_by = admin_user
        self.new_value = new_value
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
    days_count = models.PositiveIntegerField(default=3)
    valid_since = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    @property
    def subscription_lifespan(self) -> timedelta:
        return self.valid_until.date() - self.valid_since.date()

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

    def refresh(self, premium_type: PremiumType, period: int = None) -> None:
        """Refresh the validity of the promotion."""
        self.days_count = period or premium_type.period
        if self.is_active:
            self.valid_until = get_date_days_after(self.valid_until, self.days_count)
        else:
            self._fresh_init()
        self.save()

    def save(self, *args, **kwargs):
        if not self.valid_since:
            self.valid_since = timezone.now()
        super().save(*args, **kwargs)


class PremiumInquiriesProduct(models.Model):
    INQUIRIES_LIMIT = 10

    product = models.OneToOneField(
        "PremiumProduct", on_delete=models.CASCADE, related_name="inquiries"
    )

    valid_since = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)

    current_counter = models.PositiveIntegerField(default=0)
    counter_updated_at = models.DateTimeField(null=True, blank=True)

    def increment_counter(self) -> None:
        self.current_counter += 1
        self.save()

    @property
    def subscription_lifespan(self) -> timedelta:
        if self.valid_since and self.valid_until:
            return self.valid_until.date() - self.valid_since.date()
        else:
            return timedelta(days=0)

    @property
    def can_use_premium_inquiries(self) -> bool:
        return self.is_active and self.current_counter < self.INQUIRIES_LIMIT

    def reset_counter_updated_at(self, commit: bool = True) -> None:
        self.counter_updated_at = timezone.now()
        if commit:
            self.save()

    def reset_counter(self, reset_plan: bool = True, commit=True) -> None:
        self.current_counter = 0
        self.reset_counter_updated_at(commit=False)
        if commit:
            self.save()

        if reset_plan and self.product.user:
            self.product.user.userinquiry.reset_plan()

    def check_refresh(self) -> None:
        if self.is_active and timezone.now() > self.inquiries_refreshed_at:
            self.reset_counter()

    @property
    def inquiries_refreshed_at(self) -> datetime:
        return self.counter_updated_at + timedelta(days=30)

    def _fresh_init(self, period: int) -> None:
        """Initialize the premium inquiries."""
        # self.counter_updated_at = timezone.now()
        self.valid_since = timezone.now()
        self.valid_until = get_date_days_after(self.valid_since, days=period)
        self.reset_counter(commit=False)

    @property
    def is_active(self) -> bool:
        if not self.valid_until:
            return False
        return self.valid_until > timezone.now()

    def refresh(self, premium_type: PremiumType, period: Optional[int] = None) -> None:
        """Refresh the validity of the premium inquiries."""
        period = period or premium_type.period

        if self.subscription_lifespan.days < 30:
            self.reset_counter(reset_plan=False, commit=False)

        if self.is_active:
            self.valid_until = get_date_days_after(self.valid_until, days=period)
        else:
            self._fresh_init(period)

        self.save()

    def save(self, skip_auto: bool = False, *args, **kwargs):
        if not self.valid_since and not skip_auto:
            self.valid_since = timezone.now()
        if not self.counter_updated_at and not skip_auto:
            self.counter_updated_at = timezone.now()
        super().save(*args, **kwargs)

    @classmethod
    def reset_counters_for_everyone(cls, include_trial: bool = False) -> None:
        kw = {} if include_trial else {"product__premium__is_trial": False}
        for inquiries in cls.objects.filter(**kw):
            inquiries.reset_counter(reset_plan=False)


class PremiumProduct(models.Model):
    trial_tested = models.BooleanField(default=False, help_text="Trial already tested?")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

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
        product_state = "PREMIUM" if self.is_profile_premium else "FREEMIUM"
        return f"{self.profile} -- {product_state}"

    def setup_premium_products(
        self, premium_type: PremiumType = PremiumType.TRIAL, period: int = None
    ) -> None:
        """Create/refresh all premium products for the profile."""
        inquiries, _ = PremiumInquiriesProduct.objects.get_or_create(product=self)
        promotion, _ = PromoteProfileProduct.objects.get_or_create(product=self)

        inquiries.refresh(premium_type, period)
        promotion.refresh(premium_type, period)

        if self.profile.__class__.__name__ == "PlayerProfile":
            calculate_pms, _ = CalculatePMScoreProduct.objects.get_or_create(
                product=self
            )

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = self.profile.user
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

    def can_user_buy(self, user) -> None:
        if not user.profile:
            raise Exception("User has no profile.")

        if self.ref == self.ProductReference.INQUIRIES:
            if not user.profile.is_premium:
                raise PermissionError("Product is available only for premium users.")
            if user.userinquiry.left:
                raise PermissionError(
                    "You need to use all inquiries before buying new ones."
                )

        profile_class_name = user.profile.__class__.__name__
        if self.ref == self.ProductReference.PREMIUM and (
            (self.player_only and profile_class_name != "PlayerProfile")
            or (not self.player_only and profile_class_name == "PlayerProfile")
        ):
            raise PermissionError(
                "Your profile is not allowed to create transaction for this product."
            )

    @property
    def inquiry_plan(self) -> "inquiries.models.InquiryPlan":
        from inquiries.models import InquiryPlan

        return InquiryPlan.objects.get(type_ref=self.name)

    def apply_product_for_transaction(self, transaction: Transaction) -> None:
        if self.ref == Product.ProductReference.PREMIUM:
            premium_type = (
                PremiumType.YEAR if self.name.endswith("_YEAR") else PremiumType.MONTH
            )
            profile = transaction.user.profile
            profile.setup_premium_profile(premium_type.value)
        elif self.ref == Product.ProductReference.INQUIRIES:
            plan = self.inquiry_plan
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
