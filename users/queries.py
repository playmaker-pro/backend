from . import models
from roles import definitions as d


def get_users_manger_roles():
    return models.User.objects.filter(
        declared_role__in=[d.SCOUT_SHORT, d.CLUB_SHORT, d.COACH_SHORT]
    )
