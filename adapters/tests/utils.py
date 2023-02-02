from django.contrib.auth import get_user_model
from mapper.models import MapperEntity, MapperSource
from profiles.models import PlayerProfile

user = get_user_model()

_ID = "111222333"


def create_valid_player() -> PlayerProfile:
    """create player with mapper and mapperentity"""
    fake_user = user.objects.create(email="unittest@playmaker.pro")
    fake_player = PlayerProfile.objects.create(user=fake_user)
    mapper_source = MapperSource.objects.create(name="TEST")
    MapperEntity.objects.create(
        target=fake_player.mapper,
        source=mapper_source,
        mapper_id=_ID,
        database_source="scrapper_mongodb",
        related_type="player",
    )

    return fake_player
