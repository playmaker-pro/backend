from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from clubs.models import Team
from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest

from .model_utils import (
    get_profile_form_model,
    get_profile_model,
    get_profile_model_from_slug,
)


def get_modal_action(user):
    if not user.is_authenticated:
        action_modal = "registerModal"
    elif user.is_roleless:
        action_modal = "missingBasicAccountModal"
    elif user.is_missing_verification_data:
        action_modal = "verificationModal"
    elif user.userinquiry.counter == user.userinquiry.limit:
        action_modal = "actionLimitExceedModal"
    else:
        action_modal = None
    return action_modal


@login_required
def inquiry_update(request):
    response_data = {"status": False}
    message = {"body": ""}

    if request.POST.get("action") == "post":
        tick = request.POST.get("tick")
        _id, action = tick.split("---")

        request = get_object_or_404(InquiryRequest, id=_id)

        if int(action) == 1:
            request.accept()
            request.save()
            message["body"] = "zaakceptowałeś zapytanie"

        elif int(action) == 0:
            request.reject()
            request.save()
            message["body"] = "odrzuciłeś zapytanie"

        else:
            message["body"] = "nie oczekiwany błąd"

        response_data["message"] = message
        return JsonResponse(response_data)


@login_required
def inquiry_seen(request):
    response_data = {"status": False}
    message = {"body": ""}
    user = request.user
    if request.POST.get("action") == "post":
        ids = request.POST.get("ids")
        if ids:
            id_list = [int(i) for i in ids.split(",")]
            inquires = InquiryRequest.objects.filter(id__in=id_list)
            for r in inquires:
                r.read()
                r.save()
                response_data["status"] = True
    return JsonResponse(response_data)


@login_required
def inquiry(request):
    response_data = {"status": False}
    message = {"body": ""}
    user = request.user

    if request.POST.get("action") == "post":
        slug = request.POST.get("slug")
        action_modal = get_modal_action(user)

        if slug:
            profile_model = get_profile_model_from_slug(slug)
            profile = get_object_or_404(profile_model, slug=slug)
            recipient = profile.user

        if user.userinquiry.can_make_request and action_modal is None:
            if (
                InquiryRequest.objects.filter(sender=user, recipient=recipient)
                .exclude(
                    status__in=[
                        InquiryRequest.STATUS_REJECTED,
                        InquiryRequest.STATUS_ACCEPTED,
                    ]
                )
                .count()
                > 0
            ):
                response_data["status"] = False
                message["body"] = "Już jest takie zgłoszenie."
                response_data["message"] = message
            else:
                InquiryRequest.objects.create(
                    sender=user,
                    recipient=recipient,
                    category=request.POST.get("category"),
                )
                user.userinquiry.increment()
                response_data["status"] = True
                message["body"] = "Powiadomienie wyslane."
        else:
            message["body"] = "Osiągnięto limit zgłoszeń."
        response_data["message"] = message
        response_data["open_modal"] = action_modal
        return JsonResponse(response_data)


@login_required
def observe_team(request):
    response_data = {}
    message = {"body": ""}

    if request.POST.get("action") == "post":
        slug = request.POST.get("slug")
        if slug:
            team = get_object_or_404(Team, slug=slug)
        f, created = FollowTeam.objects.get_or_create(user=request.user, target=team)
        if (
            not created
        ):  # simple scenario - if pair user-slug is the same delete following.
            message_body = f"przestałeś obserwować drużynę"
            f.delete()
        else:
            message_body = f"obserwujesz drużynę"
        message["body"] = message_body
        response_data["message"] = message
        return JsonResponse(response_data)


@login_required
def observe(request):
    response_data = {}
    message = {"body": ""}

    if request.POST.get("action") == "post":
        slug = request.POST.get("slug")

        if slug:
            profile_model = get_profile_model_from_slug(slug)
            profile = get_object_or_404(profile_model, slug=slug)
            recipient = profile.user

        f, created = Follow.objects.get_or_create(user=request.user, target=recipient)
        if (
            not created
        ):  # simple scenario - if pair user-slug is the same delete following.
            message_body = f"przestałeś obserwować użytkownika"
            f.delete()
        else:
            message_body = f"obserwujesz użytkownika"
        message["body"] = message_body
        response_data["message"] = message
        return JsonResponse(response_data)
