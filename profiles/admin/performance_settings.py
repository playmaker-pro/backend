"""
Performance settings and configurations for Django admin optimization.
"""

# Admin performance settings
ADMIN_PERFORMANCE_SETTINGS = {
    'PLAYER_PROFILE_LIST_PER_PAGE': 50,
    'PLAYER_PROFILE_MAX_SHOW_ALL': 200,
    'ENABLE_QUERY_OPTIMIZATION': True,
    'CACHE_TIMEOUT': 300,  # 5 minutes
}

# Select related fields for PlayerProfile admin
PLAYER_PROFILE_SELECT_RELATED = [
    'user',
    'user__userpreferences',
    'team_object',
    'team_object__club',
    'team_object__club__voivodeship_obj',
    'team_object__league',
    'team_history_object',
    'team_object_alt',
    'playermetrics',
    'verification',
    'external_links',
    'mapper',
    'premium_products',
    'visitation',
    'verification_stage',
    'voivodeship_obj',
    'meta'
]

# Prefetch related fields for PlayerProfile admin
PLAYER_PROFILE_PREFETCH_RELATED = [
    'player_positions__player_position',
    'labels',
    'follows',
    'transfer_status_related',
    'transfer_requests'
]

# Optimized list display fields (removed expensive computed fields)
PLAYER_PROFILE_LIST_DISPLAY_OPTIMIZED = [
    'pk',
    'user',
    'slug',
    'is_active',
    'uuid',
    'get_pm_score',
    'get_team_name',
    'get_club_name',
]

# Recommended database indexes for PlayerProfile
PLAYER_PROFILE_RECOMMENDED_INDEXES = [
    ['user', 'team_object'],
    ['user', 'verification'],
    ['team_object', 'position_raw'],
    ['user', 'playermetrics'],
    ['voivodeship_obj', 'team_object'],
    ['data_mapper_id'],
    ['uuid'],
]
