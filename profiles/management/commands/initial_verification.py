import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from profiles.models import ProfileVerificationStatus

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = "Creates initial verification object for a profile. Based on existing user`s information."

    def handle(self, *args, **options):
        users = User.objects.filter(declared_role__in=["P", "C", "T"])
        for user in users:
            logger.info("Processing user: %s id: %i" % (user, user.id))
            try:
                user.profile
            except Exception as e:  # users.models.RelatedObjectDoesNotExist
                logger.info(
                    "[!!!] User user: %s id: %i has no profile." % (user, user.id)
                )
                logger.error(e)
                continue
            if user.is_need_verfication_role and user.profile:
                if user.profile.verification is None:
                    user.profile.verification = (
                        ProfileVerificationStatus.create_initial(user)
                    )
                    user.profile.save()
                else:
                    if self.has_empty_verification_status_object(user.profile):
                        user.profile.verification.update_with_profile_data()
                        logger.info(
                            "Profile verification object updated with its defaults"
                        )

    def has_empty_verification_status_object(self, profile):
        ver = profile.verification
        if ver.has_team is None and ver.team_not_found is None and ver.set_by is None:
            return True
        return False
