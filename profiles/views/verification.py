import logging

from crispy_forms.utils import render_crispy_form

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from profiles import forms
from django.http import Http404, JsonResponse

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View

User = get_user_model()


logger = logging.getLogger(__name__)


class AccountVerification(LoginRequiredMixin, View):

    http_method_names = ["post", "get"]

    def get(self, request, *args, **kwargs):
        user = request.user
        profile = user.profile
        if request.user.is_coach:
            form = forms.CoachVerificationForm(instance=profile,
                initial={'team': profile.team_object}
            )
            
        if request.user.is_club:
            form = forms.ClubVerificationForm(instance=profile)
        if request.user.is_player:
            form = forms.PlayerVerificationForm(instance=profile,
                initial={'team': profile.team_object})
        data = {}
        data["form"] = render_crispy_form(form)
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile = user.profile
        if request.user.is_coach:
            verification_form = forms.CoachVerificationForm(
                request.POST,
                instance=profile,
                initial={'team': profile.team_object})
        if request.user.is_club:
            verification_form = forms.ClubVerificationForm(
                request.POST,
                instance=profile,
            )
               
        if request.user.is_player:
            verification_form = forms.PlayerVerificationForm(
                request.POST,
                instance=profile,
                initial={'team': profile.team_object}
            )

        if not verification_form:
            raise Http404


        data = {"success": False, "url": None, "form": None, "errors": None}

        if verification_form.is_valid():
            verification_form.save()
            messages.success(
                request,
                _("Dziękujemy Twoje konto zostało zwerifikowane."),
                extra_tags="alter-success",
            )

            data["success"] = True
            data["errors"] = verification_form.errors
            data["url"] = reverse("profiles:show_self")
            return JsonResponse(data)
        else:
            # response_data = {} d
            # messages.success(request, _("Błędnie wprowadzone dane."), extra_tags='alter-success')
            # request.session['verification_form_errors'] = verification_form.errors
            data["form"] = render_crispy_form(verification_form)
            data["success"] = False
            data["errors"] = verification_form.errors
            return JsonResponse(data)
