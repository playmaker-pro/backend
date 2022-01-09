
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from inquiries.models import InquiryRequest
from django.contrib.auth.decorators import login_required
from followers.models import FollowTeam
from clubs.models import Team
from followers.models import Follow
from notifications.mail import (
    announcement_notify_requester,
    announcement_notify_player,
    announcement_notify_coach,
    announcement_notify_club_player,
    announcement_notify_club_coach,
)
# from marketplace.models import Announcement  # TODO: sprawdzic o co tu chodzi i podac prawdziwa klase!
from marketplace.models import (PlayerForClubAnnouncement,
                                ClubForPlayerAnnouncement,
                                ClubForCoachAnnouncement,
                                CoachForClubAnnouncement)

class_mapper = {
    'PlayerForClubAnnouncement': PlayerForClubAnnouncement,
    'ClubForPlayerAnnouncement': ClubForPlayerAnnouncement,
    'ClubForCoachAnnouncement': ClubForCoachAnnouncement,
    'CoachForClubAnnouncement': CoachForClubAnnouncement,
}

announcement_mail_mapper = {
    'PlayerForClubAnnouncement': announcement_notify_player,
    'ClubForPlayerAnnouncement': announcement_notify_club_player,
    'ClubForCoachAnnouncement': announcement_notify_club_coach,
    'CoachForClubAnnouncement': announcement_notify_coach,
}

@login_required
def approve_announcement(request):
    response_data = {'status': False}
    message = {'body': ''}
    user = request.user

    if request.POST.get('action') == 'post':
        _id = request.POST.get('id')
        _announcement_type = request.POST.get('announcement_type')
        if _id and _announcement_type:
            announcement_class = class_mapper[_announcement_type]
            ann = get_object_or_404(announcement_class, id=int(_id))
            #  ann.history.increment()  # @todo 1 coomit to  @ todo zwieszkyc ilosc odwiedzajcych ogloszeniee
            ann.subscribers.add(user)

            announcement_notify_requester(_announcement_type, ann, user)
            announcement_mail_mapper[_announcement_type](ann, user)

            message = 'Zgłoszenie wysłane'
            response_data['message'] = message
            return JsonResponse(response_data)
        # else:
        #     return JsonResponse({'message': 'missing id'})
