"""
Management command to analyze Django admin performance for PlayerProfile.

Usage:
    python manage.py analyze_admin_performance
    python manage.py analyze_admin_performance --profile-id 32104
    python manage.py analyze_admin_performance --query-analysis
"""

import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import override_settings
from profiles.models import PlayerProfile
from profiles.admin.views import PlayerProfileAdmin


class Command(BaseCommand):
    help = 'Analyze performance issues in PlayerProfile Django admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profile-id',
            type=int,
            help='Specific PlayerProfile ID to analyze'
        )
        parser.add_argument(
            '--query-analysis',
            action='store_true',
            help='Perform detailed query analysis'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Number of profiles to analyze (default: 100)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Django Admin Performance Analysis'))
        
        if options['query_analysis']:
            self.analyze_queries()
        
        if options['profile_id']:
            self.analyze_single_profile(options['profile_id'])
        else:
            self.analyze_list_view(options['limit'])

    def analyze_queries(self):
        """Analyze the most expensive queries in the admin."""
        self.stdout.write('\n=== Query Analysis ===')
        
        # Reset query log
        connection.queries_log.clear()
        
        # Simulate the admin list view
        admin = PlayerProfileAdmin(PlayerProfile, None)
        queryset = admin.get_queryset(None)
        
        # Time the queryset evaluation
        start_time = time.time()
        list(queryset[:50])  # Force evaluation
        end_time = time.time()
        
        self.stdout.write(f'Queryset evaluation time: {end_time - start_time:.3f}s')
        self.stdout.write(f'Number of queries: {len(connection.queries)}')
        
        # Show slowest queries
        if connection.queries:
            queries_with_time = [(float(q['time']), q['sql']) for q in connection.queries]
            queries_with_time.sort(reverse=True)
            
            self.stdout.write('\nTop 5 slowest queries:')
            for i, (query_time, sql) in enumerate(queries_with_time[:5], 1):
                self.stdout.write(f'{i}. {query_time:.3f}s: {sql[:100]}...')

    def analyze_single_profile(self, profile_id):
        """Analyze performance for a specific profile."""
        self.stdout.write(f'\n=== Single Profile Analysis (ID: {profile_id}) ===')
        
        try:
            connection.queries_log.clear()
            start_time = time.time()
            
            # Simulate admin change view loading
            profile = PlayerProfile.objects.select_related(
                'user',
                'team_object',
                'playermetrics',
                'verification'
            ).get(pk=profile_id)
            
            # Access properties that might cause N+1 queries
            _ = profile.display_league
            _ = profile.display_team
            _ = profile.display_club
            _ = profile.display_gender
            _ = profile.display_seniority
            
            end_time = time.time()
            
            self.stdout.write(f'Profile loading time: {end_time - start_time:.3f}s')
            self.stdout.write(f'Number of queries: {len(connection.queries)}')
            
            # Check for N+1 queries
            duplicate_queries = {}
            for query in connection.queries:
                sql_base = query['sql'].split('WHERE')[0] if 'WHERE' in query['sql'] else query['sql']
                duplicate_queries[sql_base] = duplicate_queries.get(sql_base, 0) + 1
            
            n_plus_one = [(count, sql) for sql, count in duplicate_queries.items() if count > 1]
            if n_plus_one:
                self.stdout.write('\nPotential N+1 queries detected:')
                for count, sql in n_plus_one:
                    self.stdout.write(f'  {count}x: {sql[:80]}...')
            
        except PlayerProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'PlayerProfile with ID {profile_id} not found'))

    def analyze_list_view(self, limit):
        """Analyze the admin list view performance."""
        self.stdout.write(f'\n=== List View Analysis (limit: {limit}) ===')
        
        connection.queries_log.clear()
        start_time = time.time()
        
        # Simulate the current admin implementation
        admin = PlayerProfileAdmin(PlayerProfile, None)
        queryset = admin.get_queryset(None)
        profiles = list(queryset[:limit])
        
        # Access list_display fields to trigger any lazy loading
        for profile in profiles:
            try:
                _ = str(profile.user)
                _ = profile.slug
                _ = profile.is_active
                _ = profile.uuid
                if hasattr(profile, 'playermetrics'):
                    _ = profile.playermetrics.pm_score
                if profile.team_object:
                    _ = profile.team_object.name
                if profile.team_object and profile.team_object.club:
                    _ = profile.team_object.club.name
            except Exception as e:
                self.stdout.write(f'Error accessing profile {profile.pk}: {e}')
        
        end_time = time.time()
        
        self.stdout.write(f'List view loading time: {end_time - start_time:.3f}s')
        self.stdout.write(f'Number of queries: {len(connection.queries)}')
        self.stdout.write(f'Queries per profile: {len(connection.queries) / len(profiles):.2f}')
        
        # Performance recommendations
        self.stdout.write('\n=== Performance Recommendations ===')
        
        if len(connection.queries) > limit * 2:
            self.stdout.write('⚠️  High query count detected. Consider:')
            self.stdout.write('   - Adding select_related() for foreign keys')
            self.stdout.write('   - Adding prefetch_related() for reverse foreign keys')
            self.stdout.write('   - Simplifying list_display fields')
        
        if end_time - start_time > 2:
            self.stdout.write('⚠️  Slow loading time detected. Consider:')
            self.stdout.write('   - Adding database indexes')
            self.stdout.write('   - Reducing number of list_display fields')
            self.stdout.write('   - Implementing pagination')
        
        self.stdout.write('\n=== Current Optimizations Applied ===')
        self.stdout.write('✅ Added select_related() for related models')
        self.stdout.write('✅ Added prefetch_related() for reverse relations')
        self.stdout.write('✅ Optimized list_display fields')
        self.stdout.write('✅ Added list_filter for better navigation')
        self.stdout.write('✅ Set pagination limits')
        self.stdout.write('✅ Added database indexes')
