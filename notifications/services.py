from notifications.tasks import create_notification
from notifications.templates import NotificationTemplate


class NotificationService:
    def __init__(self, meta: "profiles.models.ProfileMeta") -> None:  # type: ignore
        self._meta = meta

    def create_notification(self, template: NotificationTemplate, **kwargs) -> None:
        """
        Create notification based on template.
        """
        data = {
            "title": template.value["title"].format(kwargs),
            "description": template.value["description"].format(kwargs),
            "href": template.value["href"],
            "template_name": template.name,
        }

        create_notification.delay(profile_meta_id=self._meta.id, **data)

    # def default_validation(self) -> bool:
    #     """
    #     Default validation function
    #     """
    #     return True

    # def check_trial(self) -> bool:
    #     """
    #     Should notify about trial period?
    #     """
    #     return not self._profile.premium_products.trial_tested

    # def go_premium(self) -> bool:
    #     """
    #     Should remind user to go premium?
    #     """
    #     return not self._profile.premium_products.is_premium

    # def verify_profile(self) -> bool:
    #     """
    #     Should notify about unverified profile?
    #     """
    #     return not self._profile.external_links.links.exists()

    # def profile_hidden(self) -> bool:
    #     """
    #     Should notify about hidden profile?
    #     """
    #     return self._profile.user.first_name == self._profile.user.last_name

    # def buy_premium(self) -> bool:
    #     """
    #     Should remind user to buy premium?
    #     """
    #     return not self._profile.premium_products.is_premium

    # def pm_rank(self) -> bool:
    #     """
    #     Should notify about new PM Ranking?
    #     """
    #     return True

    # def visits_summary(self) -> bool:
    #     """
    #     Should notify about visits summary?
    #     """
    #     return self._profile.visitation.count_who_visited_me > 0

    # def welcome(self) -> bool:
    #     """
    #     Should notify about welcome message?
    #     """
    #     return self._profile.user.date_joined < timezone.now() - datetime.timedelta(
    #         days=7
    #     )

    # def new_follower(self) -> bool:
    #     """
    #     Should notify about new follower?
    #     """
    #     return True

    # def inquiry_accepted(self) -> bool:
    #     """
    #     Should notify about inquiry accepted?
    #     """
    #     return True

    # def inquiry_rejected(self) -> bool:
    #     """
    #     Should notify about inquiry rejected?
    #     """
    #     return True

    # def inquiry_read(self) -> bool:
    #     """
    #     Should notify about inquiry read?
    #     """
    #     return True

    # def profile_visited(self) -> bool:
    #     """
    #     Should notify about profile visited?
    #     """
    #     return self._profile.visitation.count_who_visited_me % 3 == 0

    # def set_transfer_requests(self) -> bool:
    #     """
    #     Should remind user to set transfer requests?
    #     """
    #     return not self._profile.transfer_requests.exists()

    # def set_status(self) -> bool:
    #     """
    #     Should remind user to set status?
    #     """
    #     return not self._profile.transfer_status_related.exists()

    # def invite_friends(self) -> bool:
    #     """
    #     Should remind user to invite friends?
    #     """
    #     return True

    # def add_links(self) -> bool:
    #     """
    #     Should remind user to add links?
    #     """
    #     return not self._profile.extternal_links.links.exists()

    # def add_video(self) -> bool:
    #     """
    #     Should remind user to add video?
    #     """
    #     return (
    #         self._profile_meta._profile_class == "PlayerProfile"
    #         and not self._profile_meta.has_videos
    #     )

    # def assign_club(self) -> bool:
    #     """
    #     Should remind user to assign club?
    #     """
    #     return self._profile.team_history_object is None

    # def new_inquiry(self) -> bool:
    #     """
    #     Should notify about new inquiry?
    #     """
    #     return True
    #     return True
