
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from inquiries.models import InquiryRequest
from django.contrib.auth.decorators import login_required
from followers.models import FollowTeam
from clubs.models import Team
from followers.models import Follow
from notifications.mail import annoucement_notify_author, annoucement_notify_player
from marketplace.models import Announcement


@login_required
def approve_announcement(request):
    response_data = {'status': False}
    message = {'body': ''}
    user = request.user

    if request.POST.get('action') == 'post':
        if not user.is_player:
            return  # @todo tu cos dorobic
        
        _id = request.POST.get('id')
        if _id:

            ann = get_object_or_404(Announcement, id=int(_id))
  
            #  ann.history.increment()  # @todo 1 coomit to  @ todo zwieszkyc ilosc odwiedzajcych ogloszeniee
            ann.subscribers.add(user)
            annoucement_notify_author(ann, user)
            annoucement_notify_player(ann, user)
            message = 'Zgłoszenie na testy wyłane'
            response_data['message'] = message
            return JsonResponse(response_data)
        # else:
        #     return JsonResponse({'message': 'missing id'})
