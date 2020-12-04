
from .model_utils import get_profile_form_model, get_profile_model, get_profile_model_from_slug
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from inquiries.models import InquiryRequest
from django.contrib.auth.decorators import login_required

def get_modal_action(user):
    if not user.is_authenticated:
        action_modal = 'registerModal'
    elif user.is_roleless:
        action_modal = 'missingBasicAccountModal'
    elif user.is_missing_verification_data:
        action_modal = 'verificationModal'
    elif user.userinquiry.counter == user.userinquiry.limit:
        action_modal = 'actionLimitExceedModal'
    else:
        action_modal = None
    return action_modal


@login_required
def inquiry(request):
    response_data = {'status': False}
    message = {'body': ''}
    user = request.user

    if request.POST.get('action') == 'post':
        slug = request.POST.get('slug')
        action_modal = get_modal_action(user)

        if slug:
            profile_model = get_profile_model_from_slug(slug)
            profile = get_object_or_404(profile_model, slug=slug)
            recipient = profile.user

        if user.userinquiry.can_make_request and action_modal is None:

            if InquiryRequest.objects.filter(
                sender=user, recipient=recipient).exclude(
                status__in=[InquiryRequest.STATUS_REJECTED, InquiryRequest.STATUS_ACCEPTED]).count() > 0:
                response_data['status'] = False
                message['body'] = 'Już jest takie zgłoszenie.'
                response_data['message'] = message
            else:
                InquiryRequest.objects.create(sender=user, recipient=recipient)
                user.userinquiry.increment()
                response_data['status'] = True
                message['body'] = 'Powiadomienie wyslane.'
                
        else:
            message['body'] = 'Osiągnięto limit zgłoszeń.'
            
        response_data['message'] = message
        response_data['open_modal'] = action_modal
        return JsonResponse(response_data)


@login_required
def observe(request):
    response_data = {}
    message = {'body': ''}

    if request.POST.get('action') == 'post':
        slug = request.POST.get('slug')

        if slug:
            profile_model = get_profile_model_from_slug(slug)
            profile = get_object_or_404(profile_model, slug=slug)
            recipient = profile.user

        from followers.models import Follow

        f, created = Follow.objects.get_or_create(user=request.user, target=recipient)
        if not created:  # simple scenario - if pair user-slug is the same delete following.
            message_body = f"przestałeś obserwować użytkownika"
            f.delete()
        else:
            message_body = f"obserwujesz użytkownika"
        message['body'] = message_body
        response_data['message'] = message
        return JsonResponse(response_data)
