"""
Service for sending notifications to users.
"""

from notifications.tasks import create_notification
from notifications.templates import NotificationBody, NotificationTemplate
from profiles.models import PROFILE_MODELS, ProfileMeta
from users.models import User

GENDER_BASED_ROLES = {
    "P": ("Piłkarz", "Piłkarka"),
    "T": ("Trener", "Trenerka"),
    "C": ("Działacz klubowy", "Działaczka klubowa"),
    "G": ("Kibic", "Kibic"),
    "M": ("Manager", "Manager"),
    "R": ("Sędzia", "Sędzia"),
    "S": ("Skaut", "Skaut"),
    None: ("", ""),
}


class NotificationService:
    """
    Service responsible for sending notifications to users.
    It uses the NotificationTemplate class to create notifications.
    """

    def __init__(self, meta: "profiles.models.ProfileMeta") -> None:  # type: ignore
        if meta is None:
            raise ValueError("Meta cannot be None")

        self._meta = meta

    @staticmethod
    def get_queryset() -> "QuerySet[ProfileMeta]":
        """
        Get the queryset of ProfileMeta objects.
        """
        return ProfileMeta.objects.filter(user__isnull=False)

    def create_notification(
        self,
        body: NotificationBody,
    ) -> None:
        """
        Create notification based on the provided body.
        Notification is created using the create_notification async task.
        """
        create_notification.delay(profile_meta_id=self._meta.id, **body.to_dict())

    @staticmethod
    def parse_body(
        template: NotificationTemplate,
        **kwargs,
    ) -> NotificationBody:
        """
        Parse body of the notification.
        """
        if profile := kwargs.pop("profile", None):
            try:
                role_short = profile.user.declared_role
                gender_index = int(profile.user.userpreferences.gender == "K")
                subject = GENDER_BASED_ROLES[role_short][gender_index]
                kwargs["profile"] = f"{subject} {profile.user.get_full_name()}"
            except (KeyError, IndexError):
                kwargs["profile"] = profile.user.get_full_name()

            kwargs["picture"] = profile.user.picture.name
            kwargs["picture_profile_role"] = role_short

        return NotificationBody(**template.value, kwargs=kwargs)

    @classmethod
    def bulk_notify_check_trial(cls) -> None:
        """
        Send notifications for users who haven't tested the trial.
        """
        for meta in cls.get_queryset():
            if meta.profile.products and not meta.profile.products.trial_tested:
                cls(meta).notify_check_trial()

    def notify_check_trial(self) -> None:
        """
        Send notifications for users who haven't tested the trial.
        """
        body = self.parse_body(
            NotificationTemplate.CHECK_TRIAL,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_go_premium(cls) -> None:
        """
        Send notifications for non-premium users.
        """
        for meta in cls.get_queryset():
            if not meta.profile.is_premium:
                cls(meta).notify_go_premium()

    def notify_go_premium(self) -> None:
        """
        Send notifications for non-premium users.
        """
        body = self.parse_body(
            NotificationTemplate.GO_PREMIUM,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_verify_profile(cls) -> None:
        """
        Send notifications for unverified profiles.
        """
        for meta in cls.get_queryset():
            if not meta.profile.external_links.links.exists():
                cls(meta).notify_verify_profile()

    def notify_verify_profile(self) -> None:
        """
        Send notifications for unverified profiles.
        """
        body = self.parse_body(
            NotificationTemplate.VERIFY_PROFILE,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_profile_hidden(cls) -> None:
        """
        Send notifications for hidden profiles.
        """
        for meta in cls.get_queryset().filter(
            user__display_status=User.DisplayStatus.NOT_SHOWN
        ):
            cls(meta).notify_profile_hidden()

    def notify_profile_hidden(self) -> None:
        """
        Send notifications for hidden profiles.
        """
        body = self.parse_body(
            NotificationTemplate.PROFILE_HIDDEN,
        )
        self.create_notification(body)

    def notify_premium_just_expired(self) -> None:
        """
        Send notifications for users whose premium has expired.
        """
        body = self.parse_body(
            NotificationTemplate.PREMIUM_EXPIRED,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_pm_rank(cls) -> None:
        """
        Send notifications for new PM rankings.
        """
        for meta in cls.get_queryset():
            cls(meta).notify_pm_rank()

    def notify_pm_rank(self) -> None:
        """
        Send notifications for new PM rankings.
        """
        body = self.parse_body(
            NotificationTemplate.PM_RANK,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_visits_summary(cls) -> None:
        """
        Send notifications for users with new visit summaries.
        """
        for meta in cls.get_queryset():
            if meta.count_who_visited_me > 0:
                cls(meta).notify_visits_summary()

    def notify_visits_summary(self) -> None:
        """
        Send notifications for users with new visit summaries.
        """
        body = self.parse_body(
            NotificationTemplate.VISITS_SUMMARY,
            visited_by_count=self._meta.profile.meta.count_who_visited_me,
        )
        self.create_notification(body)

    def notify_welcome(self) -> None:
        """
        Send welcome notifications to new users.
        """
        body = self.parse_body(
            NotificationTemplate.WELCOME,
        )
        self.create_notification(body)

    def notify_new_follower(self) -> None:
        """
        Send notifications for new followers.
        """
        body = self.parse_body(
            NotificationTemplate.NEW_FOLLOWER,
        )
        self.create_notification(body)

    def notify_inquiry_accepted(self, who: PROFILE_MODELS) -> None:
        """
        Send notifications for accepted inquiries.
        """
        body = self.parse_body(
            NotificationTemplate.INQUIRY_ACCEPTED,
            profile=who,
        )
        self.create_notification(body)

    def notify_inquiry_rejected(self, who: PROFILE_MODELS) -> None:
        """
        Send notifications for rejected inquiries.
        """
        body = self.parse_body(
            NotificationTemplate.INQUIRY_REJECTED,
            profile=who,
        )
        self.create_notification(body)

    def notify_inquiry_read(self, who: PROFILE_MODELS) -> None:
        """
        Send notifications for read inquiries.
        """
        body = self.parse_body(
            NotificationTemplate.INQUIRY_READ,
            profile=who,
        )
        self.create_notification(body)

    def notify_profile_visited(self) -> None:
        """
        Send notifications for profile visits.
        """
        body = self.parse_body(
            NotificationTemplate.PROFILE_VISITED,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_set_transfer_requests(cls) -> None:
        """
        Send notifications for setting transfer requests.
        """
        for meta in cls.get_queryset().filter(
            _profile_class__in=["coachprofile", "clubprofile", "managerprofile"]
        ):
            if meta.profile.transfer_requests.count() == 0:
                cls(meta).notify_set_transfer_requests()

    def notify_set_transfer_requests(self) -> None:
        """
        Send notifications for setting transfer requests.
        """
        body = self.parse_body(
            NotificationTemplate.SET_TRANSFER_REQUESTS,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_set_status(cls) -> None:
        """
        Send notifications for setting status.
        """
        for meta in cls.get_queryset().filter(_profile_class="playerprofile"):
            if meta.profile.transfer_status_related.count() == 0:
                cls(meta).notify_set_status()

    def notify_set_status(self) -> None:
        """
        Send notifications for setting status.
        """
        body = self.parse_body(
            NotificationTemplate.SET_STATUS,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_invite_friends(cls) -> None:
        """
        Send notifications for inviting friends.
        """
        for meta in cls.get_queryset():
            cls(meta).notify_invite_friends()

    def notify_invite_friends(self) -> None:
        """
        Send notifications for inviting friends.
        """
        body = self.parse_body(
            NotificationTemplate.INVITE_FRIENDS,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_add_links(cls) -> None:
        """
        Send notifications for adding links.
        """
        for meta in cls.get_queryset():
            if meta.profile.external_links.links.count() == 0:
                cls(meta).notify_add_links()

    def notify_add_links(self) -> None:
        """
        Send notifications for adding links.
        """
        body = self.parse_body(
            NotificationTemplate.ADD_LINKS,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_add_video(cls) -> None:
        """
        Send notifications for adding videos.
        """
        for meta in cls.get_queryset():
            if meta.user.user_video.count() == 0:
                cls(meta).notify_add_video()

    def notify_add_video(self) -> None:
        """
        Send notifications for adding videos.
        """
        body = self.parse_body(
            NotificationTemplate.ADD_VIDEO,
        )
        self.create_notification(body)

    def notify_test(self) -> None:
        """
        Test notification.
        """
        body = self.parse_body(
            NotificationTemplate.TEST,
        )
        self.create_notification(body)

    @classmethod
    def bulk_notify_test(cls) -> None:
        """
        Test notification.
        """
        for meta in cls.get_queryset().filter(user__is_staff=True):
            cls(meta).notify_test()

    @classmethod
    def bulk_notify_assign_club(cls) -> None:
        """
        Send notifications for assigning clubs.
        """
        for meta in cls.get_queryset():
            if not meta.profile.team_history_object:
                cls(meta).notify_assign_club()

    def notify_assign_club(self) -> None:
        """
        Send notifications for assigning clubs.
        """
        body = self.parse_body(NotificationTemplate.ASSIGN_CLUB)
        self.create_notification(body)

    def notify_new_inquiry(self, who: PROFILE_MODELS) -> None:
        """
        Send notifications for new inquiries.
        """
        body = self.parse_body(
            NotificationTemplate.NEW_INQUIRY,
            profile=who,
        )
        self.create_notification(body)

    def notify_profile_verified(self) -> None:
        """
        Send notifications for verified profiles.
        """
        body = self.parse_body(
            NotificationTemplate.PROFILE_VERIFIED,
        )
        self.create_notification(body)

    def bind_all_reccurrent_notifications(self) -> None:
        """
        Bind all notifications to the user.
        """
        self.notify_add_links()
        self.notify_add_video()
        self.notify_set_transfer_requests()
        self.notify_set_status()
        self.notify_invite_friends()
        self.notify_assign_club()
        self.notify_profile_hidden()
        self.notify_go_premium()
        self.notify_verify_profile()
        self.notify_check_trial()
        self.notify_pm_rank()
        self.notify_visits_summary()
