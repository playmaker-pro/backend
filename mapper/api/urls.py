from django.urls import path
from .views import ClubMappingsAPIView, TeamMappingsAPIView, PlayerMappingsAPIView

urlpatterns = [
    # Internal mapping endpoints
    path('clubs/', ClubMappingsAPIView.as_view({'get': 'list'}), name='clubs'),
    path('teams/', TeamMappingsAPIView.as_view({'get': 'list'}), name='teams'),
    path('players/', PlayerMappingsAPIView.as_view({'get': 'list'}), name='players'),
]
