from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.base_view import EndpointView
from api.internal_auth import InternalAPIKeyAuthentication
from clubs.models import Club, Team
from profiles.models import PlayerProfile
from .serializers import ClubMappingSerializer, TeamMappingSerializer, PlayerMappingSerializer


class BaseInternalMappingView(EndpointView):
    """
    Base view for internal mapping endpoints.
    Uses project's standard EndpointView with internal authentication.
    """
    authentication_classes = [InternalAPIKeyAuthentication]
    permission_classes = []  # No need for additional permissions - authentication handles everything
    
    @action(detail=False, methods=['get'])
    def list(self, request):
        """List mappings with optional pagination - common logic for all mapping views"""
        try:
            queryset = self.get_queryset()
            
            # Handle pagination based on query params
            limit = request.GET.get('limit')
            if limit:
                try:
                    limit = min(int(limit), 10000)
                    if limit > 0:
                        # Set the pagination page size dynamically
                        self.pagination_class.page_size = limit
                        
                        # Use built-in pagination with custom limit
                        page = self.paginate_queryset(queryset)
                        if page is not None:
                            serializer = self.get_serializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                except ValueError:
                    return Response(
                        {'error': 'Invalid limit parameter'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # No pagination - return all data
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch mappings: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClubMappingsAPIView(BaseInternalMappingView):
    """
    Internal API endpoint for club LNP mappings.
    
    GET /api/v3/internal/mapper/clubs/
    
    Query Parameters:
    - limit: Number of items per page (optional, no default limit)
    - page: Page number for pagination (optional, default: 1)
    """
    serializer_class = ClubMappingSerializer
    
    def get_queryset(self):
        """Get clubs with LNP mappings"""
        return Club.objects.filter(
            mapper__mapperentity__source__name="LNP",
            mapper__mapperentity__database_source="scrapper_mongodb",
            mapper__mapperentity__related_type="club"
        ).select_related('mapper').distinct().order_by('pk')


class TeamMappingsAPIView(BaseInternalMappingView):
    """
    Internal API endpoint for team LNP mappings.
    
    GET /api/v3/internal/mapper/teams/
    
    Query Parameters:
    - limit: Number of items per page (optional, no default limit)
    - page: Page number for pagination (optional, default: 1)
    """
    serializer_class = TeamMappingSerializer
    
    def get_queryset(self):
        """Get teams with LNP mappings"""
        return Team.objects.filter(
            mapper__mapperentity__source__name="LNP",
            mapper__mapperentity__database_source="scrapper_mongodb", 
            mapper__mapperentity__related_type="team"
        ).select_related('mapper', 'club').distinct().order_by('pk')


class PlayerMappingsAPIView(BaseInternalMappingView):
    """
    Internal API endpoint for player LNP mappings.
    
    GET /api/v3/internal/mapper/players/
    
    Query Parameters:
    - limit: Number of items per page (optional, no default limit)
    - page: Page number for pagination (optional, default: 1)
    """
    serializer_class = PlayerMappingSerializer
    
    def get_queryset(self):
        """Get players with LNP mappings"""
        return PlayerProfile.objects.filter(
            mapper__mapperentity__source__name="LNP",
            mapper__mapperentity__database_source="scrapper_mongodb",
            mapper__mapperentity__related_type="player"
        ).select_related('mapper', 'user', 'team_object').distinct().order_by('pk')
