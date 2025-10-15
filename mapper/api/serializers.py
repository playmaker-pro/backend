from rest_framework import serializers

from clubs.models import Club, Team
from profiles.models import PlayerProfile


class BaseMappingSerializer(serializers.ModelSerializer):
    """Base serializer for mapping data with common fields"""
    pk = serializers.IntegerField(read_only=True)
    pzpn_id = serializers.SerializerMethodField()
    
    def get_pzpn_id(self, obj):
        """Get LNP UUID from mapper entity"""
        try:
            if hasattr(obj, 'mapper') and obj.mapper:
                entity = obj.mapper.get_entity(
                    source__name="LNP",
                    database_source="scrapper_mongodb",
                    related_type=self.get_related_type()
                )
                return entity.mapper_id if entity else None
        except Exception:
            pass
        return None
    
    def get_related_type(self):
        """Override in subclasses to specify the related_type"""
        raise NotImplementedError("Subclasses must implement get_related_type")


class ClubMappingSerializer(BaseMappingSerializer):
    """Serializer for club mapping data"""
    
    class Meta:
        model = Club
        fields = ['pk', 'name', 'pzpn_id']
    
    def get_related_type(self):
        return "club"


class TeamMappingSerializer(BaseMappingSerializer):
    """Serializer for team mapping data"""
    club_pk = serializers.IntegerField(source='club.pk', read_only=True)
    club_name = serializers.CharField(source='club.name', read_only=True)
    
    class Meta:
        model = Team
        fields = ['pk', 'name', 'pzpn_id', 'club_pk', 'club_name']
    
    def get_related_type(self):
        return "team"


class PlayerMappingSerializer(BaseMappingSerializer):
    """Serializer for player mapping data"""
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = PlayerProfile
        fields = ['pk', 'uuid', 'name', 'pzpn_id',]
    
    def get_related_type(self):
        return "player"
    
    def get_name(self, obj):
        """Get player full name"""
        try:
            return obj.user.get_full_name()
        except Exception:
            return None
