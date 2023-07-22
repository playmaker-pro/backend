import logging

from crispy_forms.utils import render_crispy_form
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View

from clubs.api.serizalizer import ClubSelect2Serializer, TeamHistorySelect2Serializer
from clubs.models import Season
from profiles import forms
from utils import get_current_season

User = get_user_model()


logger = logging.getLogger(__name__)


class AccountVerification(LoginRequiredMixin, View):
    http_method_names = ["post", "get"]

    def get(self, request, *args, **kwargs):
        user = request.user
        preselected = None
        season_name = get_current_season()
        season = Season.objects.get(name=season_name)
        profile = user.profile

        # We need check if requested user ia a club or a other verification role like Player or Coach
        # based on that we are getting preselected value to avoid costly API calls to clubs/teams endpoint.
        # on JS side we are reading that and "manually" setting select option.

        # if user has a TeamHistory object that would be our inital season_name
        if request.user.is_club:
            if request.user.profile.club_object:
                preselected = ClubSelect2Serializer(
                    request.user.profile.club_object
                ).data
        else:
            if request.user.profile.team_history_object:
                preselected = TeamHistorySelect2Serializer(
                    request.user.profile.team_history_object
                ).data
                season_name = (
                    request.user.profile.team_history_object.leaguehistory.season.name
                )
        # Selecting right form
        if request.user.is_coach:
            form = forms.CoachVerificationForm(
                instance=profile, initial={"season": season}
            )
        if request.user.is_club:
            form = forms.ClubVerificationForm(
                instance=profile, initial={"season": season}
            )
        if request.user.is_player:
            form = forms.PlayerVerificationForm(
                instance=profile, initial={"season": season}
            )

        # Preparing json reponse
        data = {}
        data["id"] = request.user.id  # rkesik: that looks deprecated already
        data["preselected"] = preselected
        data["season"] = season_name
        data["form"] = render_crispy_form(form)
        data["is_club"] = request.user.is_club
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile = user.profile
        preselected = None
        season_name = get_current_season()

        if request.user.is_club:
            if request.user.profile.club_object:
                preselected = ClubSelect2Serializer(
                    request.user.profile.club_object
                ).data
        else:
            if request.user.profile.team_history_object:
                preselected = TeamHistorySelect2Serializer(
                    request.user.profile.team_history_object
                ).data
                season_name = (
                    request.user.profile.team_history_object.leaguehistory.season.name
                )

        season = Season.objects.get(name=season_name)
        if request.user.is_coach:
            verification_form = forms.CoachVerificationForm(
                request.POST, instance=profile, initial={"season": season}
            )
        if request.user.is_club:
            verification_form = forms.ClubVerificationForm(
                request.POST, instance=profile, initial={"season": season}
            )

        if request.user.is_player:
            verification_form = forms.PlayerVerificationForm(
                request.POST, instance=profile, initial={"season": season}
            )

        if not verification_form:
            raise Http404

        data = {
            "success": False,
            "url": None,
            "form": None,
            "errors": None,
            "preselected": None,
            "season": season_name,
        }

        if verification_form.is_valid():
            verification_form.save()
            messages.success(
                request,
                _("Dziękujemy Twoje konto zostało zwerifikowane."),
                extra_tags="alter-success",
            )
            data["preselected"] = preselected
            data["season"] = season_name
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
