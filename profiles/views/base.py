# external dependencies
import json
import logging
import math

from crispy_forms.utils import render_crispy_form
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest
from profiles import forms, models
from profiles.model_utils import (
    get_profile_form_model,
    get_profile_model,
    get_profile_model_from_slug,
)
from roles import definitions
from utils import calculate_prev_season, get_current_season

from stats import adapters

User = get_user_model()
from clubs.models import Team

logger = logging.getLogger(__name__)
from app import mixins, utils
from inquiries.services import unseen_requests, update_requests_with_read_status


def redirect_to_profile_with_full_name(request):
    return redirect("profiles:show", slug=request.user.profile.slug)


class MyObservers(
    generic.TemplateView,
    LoginRequiredMixin,
    mixins.PaginateMixin,
    mixins.ViewModalLoadingMixin,
):
    template_name = "profiles/observers.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        user = request.user
        tabs = []

        qs_players_ids = list(
            Follow.objects.filter(
                user=user, target__declared_role=definitions.PLAYER_SHORT
            ).values_list("target__id", flat=True)
        )
        qs_players = User.objects.filter(id__in=qs_players_ids)

        qs_teams_ids = FollowTeam.objects.filter(user=user).values_list(
            "target__id", flat=True
        )
        qs_teams = Team.objects.filter(id__in=qs_teams_ids)
        qs_coaches_ids = list(
            Follow.objects.filter(
                user=user, target__declared_role=definitions.COACH_SHORT
            ).values_list("target__id", flat=True)
        )
        qs_coaches = User.objects.filter(id__in=qs_coaches_ids)

        tabs.append(
            {
                "name": "players",
                "title": "Obserwowani pilkarze",
                "objects": qs_players,
                "empty": {
                    "text_body": "",
                    "text_header": "Jeszcze nie obserwujesz żadnego piłkarza",
                },
                "badge": {
                    "class": "badge-info",
                    "number": qs_players.count(),
                },
                "actions": True,
            }
        )

        tabs.append(
            {
                "name": "coaches",
                "title": "Obserwowani trenerzy",
                "objects": qs_coaches,
                "empty": {
                    "text_body": "",
                    "text_header": "Jeszcze nie obserwujesz żadnego trenera",
                },
                "badge": {
                    "class": "badge-info",
                    "number": qs_coaches.count(),
                },
                "actions": True,
            }
        )

        tabs.append(
            {
                "name": "teams",
                "title": "Obserwowane kluby",
                "objects": qs_teams,
                "empty": {
                    "text_body": "",
                    "text_header": "Jeszcze nie obserwujesz żadnego klubu",
                },
                "badge": {
                    "class": "badge-info",
                    "number": qs_teams.count(),
                },
                "actions": True,
            }
        )
        kwargs["page_title"] = "Obserwowani"
        kwargs["tabs"] = tabs
        kwargs["modals"] = self.modal_activity(user, verification_auto=False)
        return super().get(request, *args, **kwargs)


class TabStructure:
    def __init__(self, name=None, title=None, data=None, actions=False, unseen=None):
        self.output = {
            "name": name,
            "title": title,
            "objects": data,
            "empty": None,
            "badge": None,
            "actions": actions,
            "unseen": unseen,
        }

    def add_badge(self, number, klass="success"):
        self.output["badge"] = {"class": klass, "number": number}
        return self

    def add_empty(self, header="", text=""):
        self.output["empty"] = {"text_body": text, "text_header": header}
        return self

    def get(self):
        return self.output


def build_request_tab(user, name, title, qs, empty_text, empty_header, actions=True):
    unseen = [
        str(i)
        for i in qs.filter(
            recipient=user, status__in=InquiryRequest.UNSEEN_STATES
        ).values_list("id", flat=True)
    ]
    tab = TabStructure(
        name=name,
        title=title,
        data=qs,
        actions=actions,
        unseen=",".join(unseen),
    )
    tab.add_badge(number=unseen_requests(qs, user).count())
    tab.add_empty(text=empty_text, header=empty_header)
    return tab.get()


class MyRequests(
    generic.TemplateView,
    LoginRequiredMixin,
    mixins.PaginateMixin,
    mixins.ViewModalLoadingMixin,
):
    template_name = "profiles/requests.html"
    http_method_names = ["get"]
    paginate_limit = 100

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        tabs = []
        user = request.user
        related_queries = (
            "sender",
            "recipient",
            "sender__clubprofile",
            "sender__playerprofile",
            "sender__coachprofile",
            "recipient__clubprofile",
            "recipient__playerprofile",
            "recipient__coachprofile",
        )

        qs_recipient = (
            InquiryRequest.objects.select_related(*related_queries)
            .filter(recipient=user)
            .order_by("-created_at")
        )

        qs_sender = (
            InquiryRequest.objects.select_related(*related_queries)
            .filter(sender=user)
            .order_by("-created_at")
        )

        if user.is_club or user.is_coach:
            tagoptions = {
                "user": user,
                "name": "player-from",
                "title": "Otrzymane zapytania od piłkarzy",
                "qs": qs_recipient.filter(
                    sender__declared_role=definitions.PLAYER_SHORT
                ),
                "empty_text": "Piłkarze na naszej platformie mogą wysłać zapytanie o możliwość odbycia testów wraz ze swoimi danymi kontaktowymi.",
                "empty_header": "Jeszcze nie otrzymałeś żadnego zapytania o testy od piłkarzy",
            }

            tabs.append(build_request_tab(**tagoptions))
            tagoptions = {
                "user": user,
                "name": "player-to",
                "title": "Wysłane zapytania do piłkarzy",
                "qs": qs_sender.filter(
                    recipient__declared_role=definitions.PLAYER_SHORT
                ),
                "empty_text": None,
                "empty_header": "Jeszcze wysłałeś żadnego zapytania o testy od piłkarzy",
                "actions": False,
            }

            tabs.append(build_request_tab(**tagoptions))

        if user.is_player:
            tagoptions = {
                "user": user,
                "name": "player-from",
                "title": "Otrzymane zapytania od klubów",
                "qs": qs_recipient.filter(
                    sender__declared_role__in=[
                        definitions.COACH_SHORT,
                        definitions.CLUB_SHORT,
                    ]
                ),
                "empty_text": "Trenerzy i Kluby w na platformie maja możliwość wysłać Ci zaproszenie na testy. Powjawią się one tutaj.",
                "empty_header": "Jeszcze nie otrzymałeś żadnego zaproszenia na testy",
            }

            tabs.append(build_request_tab(**tagoptions))

            tagoptions = {
                "user": user,
                "name": "player-to",
                "title": "Wysłane zapytania do klubów",
                "qs": qs_sender.filter(
                    recipient__declared_role__in=[
                        definitions.COACH_SHORT,
                        definitions.CLUB_SHORT,
                    ]
                ),
                "empty_text": "Będąc na platformie możesz wysyłać zaproszenia do klubów i trenerów.",
                "empty_header": "Jeszcze nie wysłałeś żadnego zapytania o testy",
                "actions": False,
            }
            tabs.append(build_request_tab(**tagoptions))
            # update_requests_with_read_status(qs, user)

        if user.is_coach:
            tagoptions = {
                "user": user,
                "name": "club-from",
                "title": "Otrzymane zapytania od klubów",
                "qs": qs_recipient.filter(sender__declared_role=definitions.CLUB_SHORT),
                "empty_text": None,
                "empty_header": "Jeszcze nie otrzymałeś zaproszenia od żadnego klubu",
            }

            tabs.append(build_request_tab(**tagoptions))
            tagoptions = {
                "user": user,
                "name": "club-to",
                "title": "Wysłane zapytania do klubów",
                "qs": qs_sender.filter(recipient__declared_role=definitions.CLUB_SHORT),
                "empty_text": None,
                "empty_header": "Jeszcze nie wysłałeś zapytania do żadnego klubu.",
                "actions": False,
            }

            tabs.append(build_request_tab(**tagoptions))

        if user.is_club:
            tagoptions = {
                "user": user,
                "name": "club-from",
                "title": "Otrzymane zapytania od trenerów",
                "qs": qs_recipient.filter(
                    sender__declared_role=definitions.COACH_SHORT
                ),
                "empty_text": None,
                "empty_header": "Jeszcze nie otrzymałeś żadnego zapytania od trenerów",
            }
            tabs.append(build_request_tab(**tagoptions))
            tagoptions = {
                "user": user,
                "name": "club-to",
                "title": "Wysłane zapytania do trenerów",
                "qs": qs_sender.filter(
                    recipient__declared_role=definitions.COACH_SHORT
                ),
                "empty_text": None,
                "empty_header": "Jeszcze nie wysłałeś żadnego zapytania",
                "actions": False,
            }
            tabs.append(build_request_tab(**tagoptions))

        kwargs["modals"] = self.modal_activity(user, verification_auto=False)
        kwargs["page_title"] = "Moje Zapytania"
        kwargs["tabs"] = tabs

        return super().get(request, *args, **kwargs)


class SlugyViewMixin:
    def select_user_to_show(self):
        slug = self.kwargs.get("slug")
        if slug:
            profile_model = get_profile_model_from_slug(slug)
            profile = get_object_or_404(profile_model, slug=slug)
            user = profile.user
        else:
            user = self.request.user
        return user

    def _is_owner(self, user):
        return user == self.request.user


def convert_form_names(data: dict):
    translate = {
        "country": _("Kraj pochodzenia"),
        "birth_date": _("Data urodzenia"),
        "team_club_league_voivodeship_ver": _(
            "Drużyna / Klub / Poziom rozgrywek / Wojewódźtwo"
        ),
    }
    return {translate.get(param, param): msgs for param, msgs in data.items()}


class AdaptSeasonPlayerDataToCirclePresentation:
    """Class wihich converts data into circural statistics."""

    allowed_personas = ["player", "coach"]

    @classmethod
    def adapt(cls, season_stat, persona: str = "player"):
        if persona not in cls.allowed_personas:
            raise RuntimeError(f"Given persona is not allowerd. persona={persona}")
        if persona == "player":
            return cls.adapt_player_stats(season_stat)
        elif persona == "coach":
            return cls.adapt_coach_stats(season_stat)

    @classmethod
    def adapt_player_stats(cls, season_stat):
        return [
            {
                "title": _("Pierwszy skład"),
                "bs4_css": "success",
                "value": math.ceil(season_stat["first_percent"]),
                "shift": math.ceil(
                    season_stat["from_bench_percent"] + season_stat["bench_percent"]
                ),
            },
            {
                "title": _("Z ławki"),
                "bs4_css": "danger",
                "value": math.floor(season_stat["from_bench_percent"]),
                "shift": math.floor(season_stat["bench_percent"]),
            },
            {
                "title": _("Ławka"),
                "bs4_css": "secondary",
                "value": math.floor(season_stat["bench_percent"]),
                "shift": 0,
            },
        ]

    @classmethod
    def adapt_coach_stats(cls, season_stat):
        return [
            {
                "title": _("Wygrane"),
                "bs4_css": "success",
                "value": math.ceil(season_stat["wons_percent"]),
                "shift": math.ceil(
                    season_stat["draws_percent"] + season_stat["loses_percent"]
                ),
            },
            {
                "title": _("Remisy"),
                "bs4_css": "secondary",
                "value": math.floor(season_stat["draws_percent"]),
                "shift": math.floor(season_stat["loses_percent"]),
            },
            {
                "title": _("Przegrane"),
                "bs4_css": "danger",
                "value": math.floor(season_stat["loses_percent"]),
                "shift": 0,
            },
        ]


class ShowProfile(generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "profiles/show_default_profile.html"
    http_method_names = ["get", "post"]
    modal_verification_force_loading = True

    @property
    def season_name(self):
        if settings.FORCED_SEASON_NAME:
            return settings.FORCED_SEASON_NAME
        else:
            return get_current_season()

    def set_show_profile_page_title(self):
        default_my_profile = "Mój profil"
        if self.user.is_coach:
            if self.editable:
                return default_my_profile  # "TWÓJ TRENERSKI PROFIL"
            else:
                return "Profil Trenera"
        if self.user.is_player:
            if self.editable:
                return default_my_profile  # "TWOJE CV"
            else:
                return "Profil Piłkarza"
        if self.user.is_club:
            if self.editable:
                return default_my_profile  # "PROFIL TWOJEGO KLUBU"
            else:
                return "Profil Klubu"
        if self.editable:
            return default_my_profile
        return "Profil użytkownika"

    def is_profile_observed(self, user, target):
        if not user.is_authenticated:
            return False
        try:
            Follow.objects.get(user=user, target=target)
            return True
        except Follow.DoesNotExist:
            return False

    def get(self, request, *args, **kwargs):
        self.user = user = self._select_user_to_show()
        self.editable = False
        if self._is_owner(user):
            self.editable = True
            if user.declared_role is None:  # @todo - this is  not pretty.
                kwargs[
                    "role_form"
                ] = (
                    self.get_role_declaration_form()
                )  # @todo this mechanism can be replaced with ajax call

        kwargs["editable"] = self.editable
        kwargs["observed"] = self.is_profile_observed(request.user, user)
        kwargs["show_user"] = user
        kwargs["modals"] = self.modal_activity(request.user)

        if user.is_player and user.profile.updated:
            # Activate verification modal - relates to task feature/PM-360

            kwargs["modals"]["verification"]["auto"] = True
            user.profile.updated = False
            user.profile.save()

        kwargs["page_title"] = self.set_show_profile_page_title()

        try:
            kwargs["seo_object_name"] = user.get_full_name().title()
        except:
            kwargs["seo_object_name"] = None

        try:
            kwargs["seo_object_image"] = user.picture.url
        except:
            kwargs["seo_object_image"] = None

        if user.profile.has_data_id and user.profile.PROFILE_TYPE == "player":
            _id = user.profile.data_mapper_id
            # kwargs["last_games"] = adapters.PlayerAdapter._get_user_last_games(_id)
            season_name = get_current_season()
            metrics = user.profile.playermetrics

            if (
                metrics.how_old_days(games_summary=True) >= 7
                or metrics.how_old_days(fantasy_summary=True) >= 7
                or metrics.how_old_days(season_summary=True) >= 7
            ):
                games_summary = adapters.PlayerLastGamesAdapter(_id).get(
                    season=season_name, limit=3
                )  # should be profile.playermetrics.refresh_games_summary() and putted to celery.
                fantasy_summary = adapters.PlayerFantasyDataAdapter(_id).get(
                    season=season_name
                )
                season_summary = adapters.PlayerStatsSeasonAdapter(_id).get(
                    season=season_name
                )
                metrics.update_summaries(games_summary, season_summary, fantasy_summary)
            else:
                games_summary = metrics.games_summary
                fantasy_summary = metrics.fantasy_summary
                season_summary = metrics.season_summary

            kwargs["last_games"] = games_summary
            kwargs["fantasy"] = fantasy_summary
            kwargs["season_stat"] = season_summary

            # bigger query.
            # kwargs["fantasy_more"] = adapters.PlayersGameficationAdapter().get(filters={'player_id': _id, 'season': '2020/2021', 'position': 'pomocnik'})
            season_stat = kwargs["season_stat"]

            # Convert seasons statistics into circle % represetntationd data
            if season_stat is not None:
                kwargs[
                    "season_circle_stats"
                ] = AdaptSeasonPlayerDataToCirclePresentation.adapt(season_stat)
            else:
                kwargs["season_circle_stats"] = []
        elif user.profile.has_data_id and user.is_coach:
            games_data = user.profile.get_season_games_data(self.season_name)

            if games_data:
                kwargs["last_games"] = games_data[:5]

            carrier_data = user.profile.get_total_season_carrier_data(self.season_name)
            if carrier_data:
                kwargs["season_stat"] = carrier_data
                kwargs[
                    "season_circle_stats"
                ] = AdaptSeasonPlayerDataToCirclePresentation.adapt(
                    carrier_data, persona="coach"
                )
            else:
                kwargs["season_circle_stats"] = []

        if not self._is_owner(user) and request.user.is_authenticated:
            if (
                InquiryRequest.objects.filter(sender=self.request.user, recipient=user)
                .exclude(
                    status__in=[
                        InquiryRequest.STATUS_REJECTED,
                        InquiryRequest.STATUS_ACCEPTED,
                    ]
                )
                .count()
                > 0
            ):
                kwargs["pending_request"] = True
            else:
                kwargs["pending_request"] = False

        if user.profile.PROFILE_TYPE == "player":
            self.template_name = "profiles/show_player_profile.html"
        elif user.profile.PROFILE_TYPE == "coach":
            self.template_name = "profiles/show_coach_profile.html"
        else:
            self.template_name = "profiles/show_default_profile.html"

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        role_form = self.get_role_declaration_form()(request.POST)
        if role_form.is_valid():
            user.declared_role = role_form.cleaned_data["new"]
            user.save()
            messages.success(
                request,
                "Gratulujemy. Profil użytkownika wybrany!",
                extra_tags="alter-success",
            )
        return redirect("profiles:show_self")

    def get_role_declaration_form(self):
        return forms.DeclareRoleForm

    def _is_owner(self, user):
        return user == self.request.user

    def _select_user_to_show(self):
        slug = self.kwargs.get("slug")
        if slug:
            profile_model = get_profile_model_from_slug(slug)
            profile = get_object_or_404(profile_model, slug=slug)
            if self.request.user != profile.user:
                profile.history.increment()  # @todo 1 coomit to
                if self.request.user.is_authenticated and profile.user.is_coach:
                    profile.history.increment_coach()

                # if self.request.user.is_scout:  @todo
                #     profile.history.increment_coach()

            user = profile.user
        else:
            user = self.request.user
        return user


class RequestRoleChange(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        user = self.request.user
        if "cancel" in self.request.POST:
            self.delete_pending_user_roles(user)
            messages.success(
                request, _("Cofnięto prośbe o zmianę roli."), extra_tags="alter-success"
            )
        else:
            post_values = request.POST.copy()
            post_values["user"] = user

            role_form = forms.ChangeRoleForm(
                post_values
            )  # @todo how to add Current user role as a TextField.
            if role_form.is_valid():
                role_form.save()
            messages.success(
                request,
                _("Przyjęto zgloszenie o nową role."),
                extra_tags="alter-success",
            )
        return redirect("profiles:show_self")

    def delete_pending_user_roles(self, user):
        qs = models.RoleChangeRequest.objects.filter(user=user, approved=False)
        for q in qs:
            q.delete()


class EditAccountSettings(
    LoginRequiredMixin, generic.TemplateView, mixins.ViewModalLoadingMixin
):
    template_name = "profiles/edit_account_settings.html"
    http_method_names = ["get", "post"]
    modal_verification_force_loading = True

    def get(self, request, *args, **kwargs):
        user = self.request.user

        if "user_form" not in kwargs:
            kwargs["user_form"] = forms.UserForm(instance=user)

        if "role_form" not in kwargs:
            kwargs["role_form"] = forms.ChangeRoleForm()

        kwargs["modals"] = self.modal_activity(user, verification_auto=False)
        kwargs["page_title"] = _("Edycja ustawień konta")

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user

        # user_form = forms.UserForm(
        #     request.POST,
        #     request.FILES,
        #     instance=user)

        # if not (user_form.is_valid()):
        #     messages.error(request, _("Wystąpiły błąd podczas wysyłania formularza"))
        #     return super().get(request, user_form=user_form, role_form=forms.ChangeRoleForm())

        # user_form.save()
        # messages.success(request, "Profile details saved!")
        return redirect("profiles:show_self")


class EditProfile(
    LoginRequiredMixin, generic.TemplateView, mixins.ViewModalLoadingMixin
):
    template_name = "profiles/edit_profile.html"
    http_method_names = ["get", "post"]
    modal_verification_force_loading = True

    def set_edit_profile_page_title(self):
        if self.user.is_coach or self.user.is_club:
            return "Edycja Profilu"
        if self.user.is_player:
            return "Edycja CV"
        return "Edycja profilu"

    def get(self, request, *args, **kwargs):
        self.user = user = self.request.user
        if "user_form" not in kwargs:  # @todo do wywalenia
            kwargs["user_form"] = forms.UserForm(instance=user)

        if "user_basic_form" not in kwargs:
            kwargs["user_basic_form"] = forms.UserBasicForm(instance=user)

        if "profile_form" not in kwargs:
            profile_form = get_profile_form_model(user)
            kwargs["profile_form"] = profile_form(instance=user.profile)

        if "role_form" not in kwargs:  # @todo do wywalenia
            kwargs["role_form"] = forms.ChangeRoleForm()

        kwargs["page_title"] = self.set_edit_profile_page_title()
        kwargs["modals"] = self.modal_activity(user, verification_auto=False)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user

        profile_form = get_profile_form_model(user)(
            request.POST, request.FILES, instance=user.profile
        )

        user_basic_form = forms.UserBasicForm(
            request.POST, request.FILES, instance=user, request=request
        )

        if not profile_form.is_valid() or not user_basic_form.is_valid():
            messages.error(
                request,
                # _("Wystąpiły błąd podczas wysyłania formularza")
                f"Wystąpiły błąd podczas wysyłania formularza"
                f". {user_basic_form.errors} {profile_form.errors}",
                extra_tags="alter-danger",
            )

            return super().get(
                request, profile_form=profile_form, user_basic_form=user_basic_form
            )

        # Both forms are fine. Time to save!
        user_basic_form.save()
        profile = profile_form.save(commit=False)
        profile.user = user

        # Initialize verification modal
        profile.updated = True
        profile.save()

        messages.success(
            request, "Twój profil został zaktualizowany.", extra_tags="alter-success"
        )

        return redirect("profiles:show_self")


class AccountMissingFirstLastName(LoginRequiredMixin, View):

    http_method_names = ["post", "get"]

    def get(self, request, *args, **kwargs):
        # user = request.user
        form = forms.UserMissingNameForm()
        data = {}
        data["form"] = render_crispy_form(form)
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        form = forms.UserMissingNameForm(
            request.POST, instance=user
        )  # @todo how to add Current user role as a TextField.
        data = {"success": False, "url": None, "form": None}

        if form.is_valid():
            form.save()
            messages.success(
                request,
                _("Przyjęto zgłoszenie brakujacych paramterów konta."),
                extra_tags="alter-success",
            )
            data["success"] = True
            data["url"] = reverse("profiles:show_self")
            return JsonResponse(data)
        else:
            data["form"] = render_crispy_form(form)
            return JsonResponse(data)


class AccountSettings(LoginRequiredMixin, View):
    modal_verification_force_loading = True

    def get(self, request, *args, **kwargs):
        usersettings = request.user.notificationsetting
        toggled = not usersettings.weekly_report
        usersettings.weekly_report = toggled
        usersettings.save()
        data = {}
        return JsonResponse(data)
