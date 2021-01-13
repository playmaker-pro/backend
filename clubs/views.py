
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View, generic
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.http.response import HttpResponse
from django.http import JsonResponse
from django.urls import reverse
from . import models, forms
from app import mixins
from roles import definitions

from django.contrib.auth import get_user_model


User = get_user_model()


class ClubShow(generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "clubs/show_club.html"
    http_method_names = ["get"]
    page_title = 'PROFIL KLUBU'

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        self.editable = False
        user = self.request.user
        if slug:
            club = get_object_or_404(models.Club, slug=slug)

            teams = club.teams.all()
            kwargs['teams'] = teams

        if club.is_editor(user):
            kwargs['editable'] = self.editable

        kwargs["club"] = club
        kwargs['show_user'] = club
        kwargs["modals"] = self.modal_activity(request.user)
        kwargs["page_title"] = self.page_title

        return super().get(request, *args, **kwargs)


class ClubEdit(LoginRequiredMixin, generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "clubs/edit_club.html"
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        user = request.user
        slug = self.kwargs.get('slug')
        if slug:
            club = get_object_or_404(models.Club, slug=slug)
            if not club.is_editor(user):
                return redirect("app:permission_denied")
        if "club_form" not in kwargs:
            form = forms.ClubForm(instance=club)
            form.fields['editors'].queryset = User.objects.filter(declared_role__in=[definitions.COACH_SHORT, definitions.CLUB_SHORT, definitions.SCOUT_SHORT]).exclude(email=user.email)
            kwargs["club_form"] = form

        kwargs["modals"] = self.modal_activity(request.user)
        kwargs["page_title"] = 'EDYCJA KLUBU'
        kwargs['club'] = club
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # @todo uprawnienia sprawdzanie (bo mamy sluga)
        slug = self.kwargs.get('slug')
        user = request.user
        if slug:
            club = get_object_or_404(models.Club, slug=slug)
            if not club.is_editor(user):
                return redirect("app:permission_denied")
        club_form = forms.ClubForm(
            request.POST,
            request.FILES,
            instance=club
        )
        
        if not club_form.is_valid():
            messages.error(
                request,
                _("Wystąpiły błąd podczas wysyłania formularza")
                # f"Wystąpiły błąd podczas wysyłania formularza" f". {user_form.errors} {profile_form.errors}"
            )
            # user_form = forms.UserForm(instance=user)
            # profile_form = get_profile_form_model(user)(instance=user.profile)
            club_form.fields['editors'].queryset = User.objects.filter(declared_role=definitions.COACH_SHORT)
            return super().get(request, slug=club.slug, club_form=club_form)

        club = club_form.save()
        messages.success(request, "Club details saved!")
        return redirect("clubs:show_club", slug=club.slug)


class TeamShow(generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "clubs/show_team.html"
    http_method_names = ["get"]
    page_title = 'PROFIL DRUŻYNY'

    def get(self, request, *args, **kwargs):
        self.editable = False
        slug = self.kwargs.get('slug')
        user = self.request.user
        if slug:  # @todo bez sluga nie mozna wejsc...
            team = get_object_or_404(models.Team, slug=slug)
        if team.is_editor(user):
            kwargs['editable'] = self.editable
        kwargs["team"] = team
        kwargs["modals"] = self.modal_activity(request.user)
        kwargs['show_user'] = team
        kwargs["page_title"] = self.page_title
        return super().get(request, *args, **kwargs)


class TeamEdit(LoginRequiredMixin, generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "clubs/edit_team.html"
    http_method_names = ["get", "post"]
    page_title = 'EDYCJA DRUŻYNY'

    def get(self, request, *args, **kwargs):
        # @todo uprawnienia sprawdzanie (bo mamy sluga)
        user = request.user

        slug = self.kwargs.get('slug')
        if slug:
            team = get_object_or_404(models.Team, slug=slug)
            if not team.is_editor(user):
                return redirect("app:permission_denied")
        # @todo team jest opcjonalny -> grozi to wywaleniem sie gdy ktos wiedjze na /clubs/team/
        if "team_form" not in kwargs:
            team_form = forms.TeamForm(instance=team)
            # team_form.fields['editors'].queryset = User.objects.filter(declared_role=definitions.COACH_SHORT)
            kwargs["team_form"] = team_form

        kwargs["modals"] = self.modal_activity(request.user)
        kwargs["page_title"] = self.page_title
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        slug = self.kwargs.get('slug')
        if slug:
            team = get_object_or_404(models.Team, slug=slug)
            if not team.is_editor(user):
                return redirect("app:permission_denied")
        # @todo team jest opcjonalny -> grozi to wywaleniem sie gdy ktos wiedjze na /clubs/team/
        team_form = forms.TeamForm(
            request.POST,
            request.FILES,
            instance=team
        )

        if not team_form.is_valid():
            messages.error(
                request,
                _("Wystąpiły błąd podczas wysyłania formularza")
                # f"Wystąpiły błąd podczas wysyłania formularza" f". {user_form.errors} {profile_form.errors}"
            )
            # user_form = forms.UserForm(instance=user)
            # profile_form = get_profile_form_model(user)(instance=user.profile)
            team_form.fields['editors'].queryset = User.objects.filter(declared_role=definitions.COACH_SHORT)
            return super().get(request, slug=team.slug, team_form=team_form)

        team = team_form.save()
        messages.success(request, "Team details saved!")
                
        return redirect("clubs:show_team", slug=team.slug)
