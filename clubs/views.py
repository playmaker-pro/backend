from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import generic
from django.utils.translation import gettext_lazy as _
from . import models, forms
from app import mixins
from roles import definitions
from utils import get_current_season
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class ClubShow(generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "clubs/show_club.html"
    http_method_names = ["get", "post"]
    page_title = "PROFIL KLUBU"

    def get(self, request, selected_season=None, *args, **kwargs):
        slug = self.kwargs.get("slug")
        self.editable = False
        user = self.request.user
        seasons = [season.name for season in models.Season.objects.filter().order_by("name")]
        if not selected_season:
            selected_season = get_current_season()
        previous_season = seasons[seasons.index(selected_season)-1] if seasons.index(selected_season) > 0 else None
        try:
            next_season = seasons[seasons.index(selected_season)+1]
        except IndexError:
            next_season = None
        kwargs["seasons"] = {
            "previous": previous_season,
            "selected": selected_season,
            "next": next_season
        }
        if slug:
            club = get_object_or_404(models.Club, slug=slug)

            teams = club.teams.all()
            teams_history = [th.team for th in models.TeamHistory.objects.filter(team__in=teams).filter(Q(season__name=selected_season)|Q(league_history__season__name=selected_season))]
            kwargs["teams"] = teams_history

        if club.is_editor(user):
            kwargs["editable"] = self.editable
        try:
            kwargs["seo_object_name"] = club.name
        except:
            kwargs["seo_object_name"] = None
        try:
            kwargs["seo_object_image"] = club.picture.url
        except:
            kwargs["seo_object_image"] = None
        kwargs["club"] = club
        kwargs["show_user"] = club
        kwargs["modals"] = self.modal_activity(request.user)
        kwargs["page_title"] = self.page_title

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        selected_season = request.POST.get("change-season")
        return self.get(request, selected_season, *args, **kwargs)


class ClubEdit(LoginRequiredMixin, generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "clubs/edit_club.html"
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        user = request.user
        slug = self.kwargs.get("slug")
        if slug:
            club = get_object_or_404(models.Club, slug=slug)
            if not club.is_editor(user):
                return redirect("app:permission_denied")
        if "club_form" not in kwargs:
            form = forms.ClubForm(instance=club)
            form.fields["editors"].queryset = User.objects.filter(
                declared_role__in=[
                    definitions.COACH_SHORT,
                    definitions.CLUB_SHORT,
                    definitions.SCOUT_SHORT,
                ]
            )  # .exclude(email=user.email)
            kwargs["club_form"] = form

        kwargs["modals"] = self.modal_activity(request.user)
        kwargs["page_title"] = "EDYCJA KLUBU"
        kwargs["club"] = club
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # @todo uprawnienia sprawdzanie (bo mamy sluga)
        slug = self.kwargs.get("slug")
        user = request.user
        if slug:
            club = get_object_or_404(models.Club, slug=slug)
            if not club.is_editor(user):
                return redirect("app:permission_denied")
        club_form = forms.ClubForm(request.POST, request.FILES, instance=club)

        if not club_form.is_valid():
            messages.error(
                request,
                _("Wystąpiły błąd podczas wysyłania formularza"),
                extra_tags="alter-danger"
                # f"Wystąpiły błąd podczas wysyłania formularza" f". {user_form.errors} {profile_form.errors}"
            )
            # user_form = forms.UserForm(instance=user)
            # profile_form = get_profile_form_model(user)(instance=user.profile)
            club_form.fields["editors"].queryset = User.objects.filter(
                declared_role__in=[
                    definitions.COACH_SHORT,
                    definitions.CLUB_SHORT,
                    definitions.SCOUT_SHORT,
                ]
            )  # .exclude(email=user.email)
            return super().get(request, slug=club.slug, club_form=club_form)

        club = club_form.save()
        messages.success(request, "Club details saved!", extra_tags="alter-success")
        return redirect("clubs:show_club", slug=club.slug)


class TeamShow(generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "clubs/show_team.html"
    http_method_names = ["get"]
    page_title = "PROFIL DRUŻYNY"

    def get(self, request, *args, **kwargs):
        self.editable = False
        slug = self.kwargs.get("slug")
        user = self.request.user
        if slug:  # @todo bez sluga nie mozna wejsc...
            team = get_object_or_404(models.Team, slug=slug)
        if team.is_editor(user):
            kwargs["editable"] = self.editable
        kwargs["team"] = team
        try:
            kwargs["seo_object_name"] = team.name
        except:
            kwargs["seo_object_name"] = None

        try:
            kwargs["seo_object_image"] = team.picture.url
        except:
            kwargs["seo_object_image"] = None

        kwargs["modals"] = self.modal_activity(request.user)
        kwargs["show_user"] = team
        kwargs["page_title"] = self.page_title
        return super().get(request, *args, **kwargs)


class TeamEdit(LoginRequiredMixin, generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "clubs/edit_team.html"
    http_method_names = ["get", "post"]
    page_title = "EDYCJA DRUŻYNY"

    def get(self, request, *args, **kwargs):
        # @todo uprawnienia sprawdzanie (bo mamy sluga)
        user = request.user

        slug = self.kwargs.get("slug")
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
        slug = self.kwargs.get("slug")
        if slug:
            team = get_object_or_404(models.Team, slug=slug)
            if not team.is_editor(user):
                return redirect("app:permission_denied")
        # @todo team jest opcjonalny -> grozi to wywaleniem sie gdy ktos wiedjze na /clubs/team/
        team_form = forms.TeamForm(request.POST, request.FILES, instance=team)

        if not team_form.is_valid():
            messages.error(
                request,
                _("Wystąpiły błąd podczas wysyłania formularza"),
                extra_tags="alter-danger"
                # f"Wystąpiły błąd podczas wysyłania formularza" f". {user_form.errors} {profile_form.errors}"
            )
            # user_form = forms.UserForm(instance=user)
            # profile_form = get_profile_form_model(user)(instance=user.profile)
            team_form.fields["editors"].queryset = User.objects.filter(
                declared_role=definitions.COACH_SHORT
            )
            return super().get(request, slug=team.slug, team_form=team_form)

        team = team_form.save()
        messages.success(
            request, _("Profil drużyny zapisany."), extra_tags="alter-success"
        )

        return redirect("clubs:show_team", slug=team.slug)
