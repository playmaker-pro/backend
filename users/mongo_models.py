import logging
from datetime import date, datetime, timedelta, timezone

from mongoengine import (
    DateField,
    DateTimeField,
    Document,
    IntField,
    ListField,
)

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


class UserDailyLogin(Document):
    """
    MongoDB document to track daily login counts for users.
    Each document represents login activity for a specific user on a specific date.
    """

    user_id = IntField(required=True, help_text="ID of the Django User")
    date = DateField(required=True, help_text="Date of login activity")
    login_count = IntField(
        default=1, min_value=1, help_text="Number of logins on this date"
    )
    created_at = DateTimeField(default=utcnow, help_text="When this record was created")
    updated_at = DateTimeField(
        default=utcnow, help_text="When this record was last updated"
    )

    meta = {
        "collection": "user_daily_logins",
        "db_alias": "user_login_tracking",  # Use specific connection alias
        "indexes": [
            ("user_id", "date"),  # Compound index for efficient user+date queries
            "date",  # Index for daily active users queries
        ],
        "ordering": ["-date"],  # Default ordering by date descending
    }

    def save(self, *args, **kwargs):
        """Override save to update the updated_at field."""
        self.updated_at = utcnow()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"User {self.user_id} - {self.date} ({self.login_count} logins)"

    @classmethod
    def increment_login_count(
        cls, user_id: int, login_date: date = None
    ) -> "UserDailyLogin":
        """
        Increment the login count for a user on a specific date.
        """
        if login_date is None:
            login_date = utcnow().date()

        try:
            # Try to find existing document and increment
            doc = cls.objects(user_id=user_id, date=login_date).first()
            if doc:
                doc.update(inc__login_count=1, set__updated_at=utcnow())
                doc.reload()
                logger.debug(
                    f"Incremented login count for user {user_id} on {login_date}"
                )
                return doc
            else:
                # Create new document
                doc = cls(user_id=user_id, date=login_date, login_count=1)
                doc.save()
                logger.debug(
                    f"Created new login record for user {user_id} on {login_date}"
                )
                return doc

        except Exception as e:
            logger.error(
                f"Failed to increment login count for user {user_id}: {str(e)}"
            )
            raise


class UserLoginStreak(Document):
    """
    MongoDB document to track user login streaks and history.
    Each user has one document that tracks their login history and streak data.
    """

    user_id = IntField(required=True, unique=True, help_text="ID of the Django User")
    login_dates = ListField(DateField(), help_text="Sorted list of login dates")
    current_streak = IntField(
        default=0, min_value=0, help_text="Current consecutive login streak"
    )
    max_streak = IntField(default=0, min_value=0, help_text="Maximum streak achieved")
    last_login = DateTimeField(help_text="Timestamp of last login")
    updated_at = DateTimeField(
        default=utcnow, help_text="When this record was last updated"
    )

    meta = {
        "collection": "user_login_streaks",
        "db_alias": "user_login_tracking",  # Use specific connection alias
        "indexes": [
            "user_id",  # Unique index for user lookups
            "last_login",  # Index for cleanup queries
            "-current_streak",  # Index for leaderboards/analytics
        ],
        "ordering": ["-current_streak"],  # Default ordering by current streak
    }

    def save(self, *args, **kwargs):
        """Override save to update the updated_at field."""
        self.updated_at = utcnow()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"User {self.user_id} - Current Streak: {self.current_streak}, Max: {self.max_streak}"

    def add_login_date(
        self, login_date: date = None, login_timestamp: datetime = None
    ) -> None:
        """
        Add a new login date and update streak information.
        """
        now = utcnow()
        if login_date is None:
            login_date = now.date()
        if login_timestamp is None:
            login_timestamp = now

        try:
            # Avoid duplicates - don't add if already exists
            if login_date not in self.login_dates:
                self.login_dates.append(login_date)
                self.login_dates.sort()

                # Keep only last 365 days of login dates to prevent unlimited growth
                cutoff_date = now.date() - timedelta(days=365)
                self.login_dates = [d for d in self.login_dates if d > cutoff_date]

            # Update last login timestamp
            self.last_login = login_timestamp

            # Recalculate streak
            self._calculate_current_streak()

            # Update max streak if current is higher
            if self.current_streak > self.max_streak:
                self.max_streak = self.current_streak

            self.save()
            logger.debug(
                f"Updated login streak for user {self.user_id}: current={self.current_streak}, max={self.max_streak}"
            )

        except Exception as e:
            logger.error(f"Failed to add login date for user {self.user_id}: {str(e)}")
            raise

    def _calculate_current_streak(self) -> None:
        """
        Calculate the current login streak based on login_dates.

        A streak is the number of consecutive days (including today or yesterday)
        that the user has logged in.
        """
        if not self.login_dates:
            self.current_streak = 0
            return

        # Sort dates in descending order (most recent first)
        sorted_dates = sorted(self.login_dates, reverse=True)
        current_date = datetime.now().date()

        # Check if the user logged in today or yesterday (streak can continue)
        latest_login = sorted_dates[0]
        days_since_last = (current_date - latest_login).days

        if days_since_last > 1:
            # More than 1 day gap - streak is broken
            self.current_streak = 0
            return

        # Count consecutive days from the most recent login
        streak = 0
        expected_date = latest_login

        for login_date in sorted_dates:
            if login_date == expected_date:
                streak += 1
                # Move to previous day using timedelta to handle month/year boundaries correctly
                expected_date = expected_date - timedelta(days=1)
            else:
                # Gap found - streak ends
                break

        self.current_streak = streak

    @classmethod
    def update_user_streak(
        cls, user_id: int, login_date: date = None, login_timestamp: datetime = None
    ) -> "UserLoginStreak":
        """
        Update or create a user's login streak record.
        """
        if login_date is None:
            login_date = utcnow().date()
        if login_timestamp is None:
            login_timestamp = utcnow()

        try:
            # Try to get existing record
            streak_doc = cls.objects(user_id=user_id).first()
            created = False

            if not streak_doc:
                # Create a new one
                streak_doc = cls(
                    user_id=user_id, login_dates=[], current_streak=0, max_streak=0
                )
                created = True

                # Add the login date
            streak_doc.add_login_date(login_date, login_timestamp)
            streak_doc.save()

            if created:
                logger.debug(f"Created new login streak record for user {user_id}")
            else:
                logger.debug(f"Updated existing login streak record for user {user_id}")

            return streak_doc

        except Exception as e:
            logger.error(f"Failed to update login streak for user {user_id}: {str(e)}")
            raise
