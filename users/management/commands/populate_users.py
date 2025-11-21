"""
Django management command to populate test login data for testing the login history table.
Creates realistic login patterns for random users over the past month.
"""
import random
from datetime import date, datetime, timedelta
from typing import List

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from users.models import User
from users.mongo_login_service import mongo_login_service


class Command(BaseCommand):
    help = 'Populate test login data for the past month to test login history functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=1000,
            help='Number of users to populate data for (default: 100)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of past days to populate data for (default: 30)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing login data before populating test data'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating data'
        )

    def handle(self, *args, **options):
        users_count = options['users']
        days_count = options['days']
        clear_data = options['clear']
        dry_run = options['dry_run']

        # Validate parameters
        if users_count <= 0 or users_count > 1000:
            raise CommandError('Users count must be between 1 and 1000')

        if days_count <= 0 or days_count > 365:
            raise CommandError('Days count must be between 1 and 365')

        self.stdout.write(
            self.style.SUCCESS(
                f'Populating test login data for {users_count} users over {days_count} days'
                f'{" (DRY RUN)" if dry_run else ""}'
            )
        )

        try:
            # Get random users from database
            total_users = User.objects.count()
            if total_users == 0:
                raise CommandError('No users found in database. Create some users first.')

            if users_count > total_users:
                self.stdout.write(
                    self.style.WARNING(
                        f'Only {total_users} users available. Using all of them.'
                    )
                )
                users_count = total_users

            # Get random sample of users
            user_ids = list(User.objects.values_list('id', flat=True))
            selected_user_ids = random.sample(user_ids, min(users_count, len(user_ids)))

            self.stdout.write(f'Selected {len(selected_user_ids)} users for test data')

            # Clear existing data if requested
            if clear_data:
                if dry_run:
                    self.stdout.write(self.style.WARNING('Would clear existing login data'))
                else:
                    self.stdout.write('Clearing existing login data...')
                    mongo_login_service.cleanup_old_data(days_to_keep=0)
                    self.stdout.write(self.style.SUCCESS('Existing data cleared'))

            # Generate date range
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days_count - 1)
            date_range = [start_date + timedelta(days=i) for i in range(days_count)]

            self.stdout.write(f'Generating data from {start_date} to {end_date}')

            # Statistics tracking
            total_logins = 0
            total_days = 0
            user_stats = {}

            # Generate login data for each user
            for user_id in selected_user_ids:
                user_login_days = 0
                user_total_logins = 0

                # Create different user patterns
                user_pattern = self._get_user_pattern()

                for current_date in date_range:
                    # Determine if user logs in on this date
                    if self._should_user_login(current_date, user_pattern):
                        # Generate realistic login count for the day
                        login_count = self._generate_login_count(current_date, user_pattern)

                        if dry_run:
                            self.stdout.write(
                                f'Would create: User {user_id}, Date {current_date}, Logins {login_count}'
                            )
                        else:
                            # Track the login for this date
                            # We need to directly create the MongoDB entries since track_user_login
                            # uses current date. We'll call the service method multiple times
                            # but need to manually set the date in MongoDB

                            # Import the MongoDB models directly
                            from users.mongo_models import UserDailyLogin, UserLoginStreak

                            try:
                                # Create or update daily login record
                                UserDailyLogin.increment_login_count(user_id, current_date)

                                # Update streak record with the specific date
                                login_time = self._generate_login_time(current_date)
                                UserLoginStreak.update_user_streak(user_id, current_date, login_time)

                                # If we want multiple logins per day, increment the count
                                if login_count > 1:
                                    daily_login = UserDailyLogin.objects(
                                        user_id=user_id, date=current_date
                                    ).first()
                                    if daily_login:
                                        # Update to the desired count
                                        daily_login.update(
                                            set__login_count=login_count,
                                            set__updated_at=login_time
                                        )

                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f'Failed to track login for user {user_id} on {current_date}: {str(e)}'
                                    )
                                )

                        user_login_days += 1
                        user_total_logins += login_count
                        total_logins += login_count
                        total_days += 1

                user_stats[user_id] = {
                    'login_days': user_login_days,
                    'total_logins': user_total_logins,
                    'pattern': user_pattern['type']
                }

            # Display statistics
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(self.style.SUCCESS('GENERATION COMPLETE'))
            self.stdout.write('=' * 50)
            self.stdout.write(f'Total users processed: {len(selected_user_ids)}')
            self.stdout.write(f'Total login days created: {total_days}')
            self.stdout.write(f'Total logins tracked: {total_logins}')
            self.stdout.write(f'Average logins per user: {total_logins / len(selected_user_ids):.1f}')

            # Show pattern distribution
            pattern_counts = {}
            for stats in user_stats.values():
                pattern = stats['pattern']
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

            self.stdout.write('\nUser patterns:')
            for pattern, count in pattern_counts.items():
                self.stdout.write(f'  {pattern}: {count} users')

            # Show top 5 most active users
            if not dry_run:
                top_users = sorted(
                    user_stats.items(),
                    key=lambda x: x[1]['total_logins'],
                    reverse=True
                )[:5]

                self.stdout.write('\nTop 5 most active users:')
                for user_id, stats in top_users:
                    try:
                        user = User.objects.get(id=user_id)
                        name = user.get_full_name() or user.email
                    except User.DoesNotExist:
                        name = f'User {user_id}'

                    self.stdout.write(
                        f'  {name}: {stats["total_logins"]} logins over {stats["login_days"]} days '
                        f'({stats["pattern"]} pattern)'
                    )

        except Exception as e:
            raise CommandError(f'Error generating test data: {str(e)}')

    def _get_user_pattern(self) -> dict:
        """Generate a realistic user login pattern."""
        patterns = [
            {
                'type': 'Daily Active',
                'login_probability': 0.85,  # Very active user
                'weekend_factor': 0.7,  # Less likely on weekends
                'avg_logins_per_day': 3,
                'variation': 2
            },
            {
                'type': 'Regular User',
                'login_probability': 0.6,  # Moderately active
                'weekend_factor': 0.5,
                'avg_logins_per_day': 2,
                'variation': 1
            },
            {
                'type': 'Weekend Warrior',
                'login_probability': 0.3,  # Less active during week
                'weekend_factor': 2.0,  # More active on weekends
                'avg_logins_per_day': 2,
                'variation': 1
            },
            {
                'type': 'Occasional User',
                'login_probability': 0.2,  # Infrequent user
                'weekend_factor': 0.8,
                'avg_logins_per_day': 1,
                'variation': 0
            },
            {
                'type': 'Power User',
                'login_probability': 0.95,  # Almost daily
                'weekend_factor': 1.0,  # Consistent all week
                'avg_logins_per_day': 5,
                'variation': 3
            }
        ]

        return random.choice(patterns)

    def _should_user_login(self, current_date: date, pattern: dict) -> bool:
        """Determine if a user should login on a given date based on their pattern."""
        base_probability = pattern['login_probability']
        weekend_factor = pattern['weekend_factor']

        # Adjust probability for weekends
        is_weekend = current_date.weekday() >= 5  # Saturday = 5, Sunday = 6
        if is_weekend:
            probability = base_probability * weekend_factor
        else:
            probability = base_probability

        # Add some randomness for streaks and breaks
        return random.random() < probability

    def _generate_login_count(self, current_date: date, pattern: dict) -> int:
        """Generate realistic login count for a day."""
        avg_logins = pattern['avg_logins_per_day']
        variation = pattern['variation']

        # Generate count with some variation
        min_logins = max(1, avg_logins - variation)
        max_logins = avg_logins + variation

        return random.randint(min_logins, max_logins)

    def _generate_login_time(self, login_date: date) -> datetime:
        """Generate a realistic login time for a given date."""
        # Generate time between 6 AM and 11 PM
        hour = random.randint(6, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        return datetime.combine(login_date, datetime.min.time().replace(
            hour=hour, minute=minute, second=second
        )).replace(tzinfo=timezone.get_current_timezone())
