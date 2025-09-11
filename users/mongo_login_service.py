import logging
import threading
from datetime import date, datetime, timedelta
from typing import List, Optional

import mongoengine
from django.conf import settings
from django.utils import timezone
from mongoengine.connection import ConnectionFailure, get_connection

from backend.settings import cfg
from users.mongo_models import UserDailyLogin, UserLoginStreak

logger = logging.getLogger(__name__)


class MongoLoginService:  # TODO: Create abstract MongoDB manager
    """Service for tracking user logins using MongoDB."""

    # Thread-safe connection management
    _connection_lock = threading.Lock()
    _connection_alias = "user_login_tracking"
    _connection_tested = False

    def __init__(self):
        """Initialize the MongoDB login service."""
        if cfg.mongodb.enabled:
            self._ensure_connection()
            logger.debug("MongoLoginService initialized")

        if not self._is_connection_healthy():
            # Always attempt to connect if not healthy
            mongoengine.connect(
                db=settings.MONGODB_SETTINGS["db"],
                host=settings.MONGODB_SETTINGS["host"],
                port=settings.MONGODB_SETTINGS["port"],
                alias="user_login_tracking",
                maxPoolSize=100,
                minPoolSize=1,
            )

    def _ensure_connection(self):
        """Thread-safe MongoDB connection with proper aliasing and health checks."""
        try:
            # First, try to use existing connection if healthy
            if self._is_connection_healthy():
                return

        except Exception:
            # Connection doesn't exist or is unhealthy, need to create/recreate
            pass

        # Use lock to prevent race conditions
        with self._connection_lock:
            try:
                # Double-check pattern - another thread might have connected while we waited
                if self._is_connection_healthy():
                    return

                # Close any existing connection for this alias only
                try:
                    mongoengine.disconnect(alias=self._connection_alias)
                except Exception:
                    pass  # Connection might not exist

                # Get MongoDB settings from Django settings
                mongodb_settings = settings.MONGODB_SETTINGS.copy()

                # Add connection alias and optimization settings
                mongodb_settings.update({
                    "alias": self._connection_alias,
                    "maxPoolSize": 50,
                    "minPoolSize": 5,
                    "maxIdleTimeMS": 30000,
                    "waitQueueTimeoutMS": 5000,
                    "serverSelectionTimeoutMS": 5000,
                    "retryWrites": True,
                })

                # Connect to MongoDB with alias
                mongoengine.connect(**mongodb_settings)

                # Test the connection
                if self._test_connection():
                    MongoLoginService._connection_tested = True
                else:
                    raise ConnectionFailure("Connection test failed")

            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {str(e)}")
                raise

    def _is_connection_healthy(self) -> bool:
        """Check if the current connection is healthy."""
        try:
            conn = get_connection(alias=self._connection_alias)
            # Quick ping to test connection health
            conn.admin.command("ping")
            return True
        except Exception:
            return False

    def _test_connection(self) -> bool:
        """Test MongoDB connection by performing a simple operation."""
        try:
            conn = get_connection(alias=self._connection_alias)
            # Test connection with a simple command
            result = conn.admin.command("ping")
            return result.get("ok") == 1
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {str(e)}")
            return False

    def track_user_login(self, user_id: int) -> bool:
        """Track a user login for the current date."""
        try:
            current_date = timezone.now().date()
            current_timestamp = timezone.now()

            # Track daily login count
            UserDailyLogin.increment_login_count(user_id, current_date)

            # Update login streak
            UserLoginStreak.update_user_streak(user_id, current_date, current_timestamp)

            # Verify data was saved by querying back
            daily_login = UserDailyLogin.objects(
                user_id=user_id, date=current_date
            ).first()
            login_streak = UserLoginStreak.objects(user_id=user_id).first()

            if not daily_login or not login_streak:
                logger.warning(f"Login tracking verification failed for user {user_id}")
                return False

            return True

        except Exception as e:
            logger.error(
                f"Failed to track login for user {user_id}: {str(e)}", exc_info=True
            )
            return False

    def get_user_login_count(
        self, user_id: int, target_date: Optional[date] = None
    ) -> int:
        """Get the number of times a user logged in on a specific date."""
        try:
            if target_date is None:
                target_date = timezone.now().date()

            # Query for the specific user and date
            daily_login = UserDailyLogin.objects(
                user_id=user_id, date=target_date
            ).first()

            return daily_login.login_count if daily_login else 0

        except Exception as e:
            logger.error(f"Failed to get login count for user {user_id}: {str(e)}")
            return 0

    def get_user_login_streak(self, user_id: int) -> int:
        """Get the current login streak for a user (consecutive days of login)."""
        try:
            # Get the user's streak record
            streak_record = UserLoginStreak.objects(user_id=user_id).first()

            if not streak_record:
                return 0

            streak_record._calculate_current_streak()
            streak_record.save()

            return streak_record.current_streak

        except Exception as e:
            logger.error(f"Failed to get login streak for user {user_id}: {str(e)}")
            return 0

    def get_user_login_history(self, user_id: int, limit: int = None) -> List[dict]:
        """Get complete login history for a user."""
        try:
            login_history = []

            # Get daily login records for this user, ordered by date descending
            query = UserDailyLogin.objects(user_id=user_id).order_by("-date")

            # Apply limit if specified
            if limit and limit > 0:
                query = query.limit(min(limit, 10000))  # Cap at 10000 for safety

            for daily_login in query:
                login_history.append({
                    "date_obj": daily_login.date,
                    "login_count": daily_login.login_count,
                })

            return login_history

        except Exception as e:
            logger.error(f"Failed to get login history for user {user_id}: {str(e)}")
            return []

    def get_user_login_history_paginated(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> dict:
        """Get paginated login history for a specific user."""
        try:
            # Validate and sanitize pagination parameters
            limit = min(max(1, limit), 1000)  # Ensure limit is between 1 and 1000
            offset = max(0, offset)  # Ensure offset is not negative

            # Build base query
            base_query = UserDailyLogin.objects(user_id=user_id)

            # Get total count for pagination info
            total_count = base_query.count()

            # Get paginated results
            daily_logins = base_query.order_by("-date").skip(offset).limit(limit)

            login_history = []
            for daily_login in daily_logins:
                login_history.append({
                    "date_obj": daily_login.date,
                    "login_count": daily_login.login_count,
                })

            return {
                "data": login_history,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
                "user_id": user_id,
            }

        except Exception as e:
            logger.error(
                f"Failed to get paginated login history for user {user_id}: {str(e)}"
            )
            return {
                "data": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
                "error": str(e),
            }

    def get_user_last_login(self, user_id: int) -> Optional[datetime]:
        """Get the timestamp of user's last login."""
        try:
            # Get the user's streak record which contains last_login timestamp
            streak_record = UserLoginStreak.objects(user_id=user_id).first()

            if streak_record and streak_record.last_login:
                return streak_record.last_login

            return None

        except Exception as e:
            logger.error(f"Failed to get last login for user {user_id}: {str(e)}")
            return None

    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """Remove login tracking data older than a specified number of days."""
        try:
            if days_to_keep < 1:
                raise ValueError("days_to_keep must be positive")

            cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)

            # Clean up old daily login records
            daily_deleted_count = UserDailyLogin.objects(date__lt=cutoff_date).delete()

            # For streak records, use bulk operations or batch processing
            # Process in smaller batches to avoid memory issues
            batch_size = 100
            streak_updated = 0

            while True:
                # Get a batch of streak records that might need updating
                streak_records = UserLoginStreak.objects().limit(batch_size)

                if not streak_records:
                    break

                batch_updated = 0
                for streak_record in streak_records:
                    original_count = len(streak_record.login_dates)
                    streak_record.login_dates = [
                        login_date
                        for login_date in streak_record.login_dates
                        if login_date >= cutoff_date
                    ]

                    if len(streak_record.login_dates) != original_count:
                        # Use a public method or recalculate here
                        streak_record.save()
                        batch_updated += 1

                streak_updated += batch_updated

                # If we processed fewer than batch_size, we're done
                if len(streak_records) < batch_size:
                    break

            logger.info(
                f"Cleanup complete. Deleted {daily_deleted_count} daily records, updated {streak_updated} streak records."
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {str(e)}")
            return False

    def get_all_users_login_history(
        self,
        start_date: date = None,
        end_date: date = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> dict:
        """Get paginated login history for all users within a date range."""
        try:
            if end_date is None:
                end_date = timezone.now().date()
            if start_date is None:
                start_date = end_date - timedelta(days=30)

            # Validate date range
            if start_date > end_date:
                raise ValueError("start_date cannot be after end_date")

            # Validate and sanitize pagination parameters
            limit = min(max(1, limit), 10000)  # Ensure limit is between 1 and 10000
            offset = max(0, offset)  # Ensure offset is not negative

            # Build base query
            base_query = UserDailyLogin.objects(
                date__gte=start_date, date__lte=end_date
            )

            # Get total count for pagination info
            total_count = base_query.count()

            # Get paginated results
            daily_logins = (
                base_query.order_by("user_id", "-date").skip(offset).limit(limit)
            )

            login_history = []
            for daily_login in daily_logins:
                login_history.append({
                    "user_id": daily_login.user_id,
                    "date_obj": daily_login.date,
                    "login_count": daily_login.login_count,
                })

            return {
                "data": login_history,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
                "date_range": {"start_date": start_date, "end_date": end_date},
            }

        except Exception as e:
            logger.error(f"Failed to get paginated login history: {str(e)}")
            return {
                "data": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
                "error": str(e),
            }


mongo_login_service = MongoLoginService()
