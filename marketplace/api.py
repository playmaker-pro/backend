from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from clubs.models import Team
from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest

# from marketplace.models import Announcement  # TODO: sprawdzic o co tu chodzi i podac prawdziwa klase!
from marketplace.models import (
    ClubForCoachAnnouncement,
    ClubForPlayerAnnouncement,
    CoachForClubAnnouncement,
    PlayerForClubAnnouncement,
)
from notifications.mail import (
    announcement_notify_club_coach,
    announcement_notify_club_player,
    announcement_notify_coach,
    announcement_notify_player,
    announcement_notify_requester,
)
from users.models import User

class_mapper = {
    "PlayerForClubAnnouncement": PlayerForClubAnnouncement,
    "ClubForPlayerAnnouncement": ClubForPlayerAnnouncement,
    "ClubForCoachAnnouncement": ClubForCoachAnnouncement,
    "CoachForClubAnnouncement": CoachForClubAnnouncement,
}

announcement_mail_mapper = {
    "PlayerForClubAnnouncement": announcement_notify_player,
    "ClubForPlayerAnnouncement": announcement_notify_club_player,
    "ClubForCoachAnnouncement": announcement_notify_club_coach,
    "CoachForClubAnnouncement": announcement_notify_coach,
}


@login_required
def approve_announcement(request):
    response_data = {"status": False}
    message = {"body": ""}
    user = request.user

    if request.POST.get("action") == "post":
        try:
            _id = int(request.POST.get("id"))
        except ValueError:
            response_data["message"] = "Id have to be a number, not string"
            response_data["error"] = True
            return JsonResponse(response_data)

        _announcement_type = request.POST.get("announcement_type")
        if _id and _announcement_type:
            try:
                club_name = user.profile.team_object.club.name
            except AttributeError:
                club_name = user.profile.club_object.name
            announcement_class = class_mapper[_announcement_type]
            ann = get_object_or_404(announcement_class, id=int(_id))

            ann_user = User.objects.get(id=ann.creator_id)
            ann_club = ann_user.profile.get_club_object()
            if ann_user.is_coach and ann_club:
                ann_club = ann_club.name
            elif ann_user.is_player and ann_club:
                ann_club = ann_club.name
            elif ann_user.is_club and ann_club:
                ann_club = ann_club.name

            if club_name == ann_club:
                message = "Nie możesz wchodzić w interakcję z użytkownikami, którzy są z Tobą w klubie"
                response_data["message"] = message
                response_data["error"] = True
                return JsonResponse(response_data)

            #  ann.history.increment()  # @todo 1 coomit to  @ todo zwieszkyc ilosc odwiedzajcych ogloszeniee

            announcement_mail_mapper[_announcement_type](ann, user)
            announcement_notify_requester(_announcement_type, ann, user)
            ann.subscribers.add(user)
            response_data["status"] = True

            message = "Zgłoszenie wysłane"
            response_data["message"] = message
            response_data["success"] = True
            return JsonResponse(response_data)
        # else:
        #     return JsonResponse({'message': 'Błąd'})
