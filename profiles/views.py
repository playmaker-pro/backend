# external dependencies
import math
import json
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from django.http.response import HttpResponse
from stats import adapters
from inquiries.models import InquiryRequest
from django.urls import reverse
from . import forms, models
from .utils import get_current_season
from .model_utils import get_profile_form_model, get_profile_model, get_profile_model_from_slug
from django.http import JsonResponse
from roles import definitions
from . import mixins
import logging
from followers.models import Follow

logger = logging.getLogger(__name__)

class PaginateMixin:
    paginate_limit = 30
    @property
    def page(self):
        return self.request.GET.get('page') or 1

    def paginate(self, data):
        paginator = Paginator(data, self.paginate_limit)
        page_number = self.page
        return paginator.get_page(page_number)


class MyObservers(generic.TemplateView, LoginRequiredMixin,  PaginateMixin, mixins.ViewModalLoadingMixin):
    template_name = "profiles/observers.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        qs = Follow.objects.filter(user=request.user)
        kwargs['modals'] = self.modal_activity(request.user)
        kwargs['page_title'] = 'Obserwowani'
        kwargs['page_obj'] = self.paginate(qs)
        return super().get(request, *args, **kwargs)


class MyRequests(generic.TemplateView, LoginRequiredMixin,  PaginateMixin, mixins.ViewModalLoadingMixin):
    template_name = "profiles/requests.html"
    http_method_names = ["get"]
    paginate_limit = 100

    def get(self, request, *args, **kwargs):
        qs_recipient = InquiryRequest.objects.filter(recipient=request.user)
        qs_sender = InquiryRequest.objects.filter(sender=request.user)
        
        kwargs['modals'] = self.modal_activity(request.user)
        kwargs['page_title'] = 'Obserwowani'
        kwargs['page_obj_recipient'] = self.paginate(qs_recipient)
        kwargs['page_obj_sender'] = self.paginate(qs_sender)
        return super().get(request, *args, **kwargs)


class SlugyViewMixin:
    def select_user_to_show(self):
        slug = self.kwargs.get('slug')
        if slug:
            profile_model = get_profile_model_from_slug(slug)
            profile = get_object_or_404(profile_model, slug=slug)
            user = profile.user
        else:
            user = self.request.user
        return user


class ProfileFantasy(generic.TemplateView, SlugyViewMixin):
    template_name = "profiles/fantasy2.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        user_to_present = self.select_user_to_show()
        user = self.request.user
        _id = user.profile.data_mapper_id
        season_name = get_current_season()
        kwargs['season_name'] = season_name
        kwargs["fantasy"] = self.get_data_or_calculate(user_to_present)
        return super().get(request, *args, **kwargs)

    def get_data_or_calculate(self, user):
        season_name = get_current_season()
        _id = user.profile.data_mapper_id
        if user.profile.playermetrics.how_old_days(fantasy=True) >= 7 and user.profile.has_data_id:
            fantasy = adapters.PlayerFantasyDataAdapter(_id).get(season=season_name, full=True)
            user.profile.playermetrics.update_fantasy(fantasy)
        return user.profile.playermetrics.fantasy


class ProfileCarrier(generic.TemplateView, SlugyViewMixin):
    template_name = "profiles/carrier.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        user_to_present = self.select_user_to_show()
        _id = user.profile.data_mapper_id
        

        kwargs["carrier"] = self.get_data_or_calculate(user_to_present)
        return super().get(request, *args, **kwargs)

    def get_data_or_calculate(self, user):
      
        _id = user.profile.data_mapper_id
        if user.profile.playermetrics.how_old_days(season=True) >= 7 and user.profile.has_data_id:
            season = adapters.PlayerStatsSeasonAdapter(_id).get(groupped=True)
            user.profile.playermetrics.update_season(season)
        user.profile.playermetrics.refresh_from_db()
        return user.profile.playermetrics.season


class ProfileGames(generic.TemplateView, PaginateMixin, SlugyViewMixin):
    # @todo: add limit handling for futhure unknown usage.
    template_name = "profiles/games.html"
    http_method_names = ["get"]
    paginate_limit = 15

    def get(self, request, *args, **kwargs):

        user_to_present = self.select_user_to_show()

        games = self.get_data_or_calculate(user_to_present)
        games = games or []
        kwargs['page_obj'] = self.paginate(games)
        return super().get(request, *args, **kwargs)

    def get_data_or_calculate(self, user):
        _id = user.profile.data_mapper_id
        if user.profile.playermetrics.how_old_days(games=True) >= 7 and user.profile.has_data_id:
            games = adapters.PlayerLastGamesAdapter(_id).get()
            user.profile.playermetrics.update_games(games)
        return user.profile.playermetrics.games


def convert_form_names(data: dict):
    translate = {
        'country': _('Kraj pochodzenia'),
        'birth_date': _('Data urodzenia'),
        'team_club_league_voivodeship_ver': _('Drużyna / Klub / Poziom rozgrywek / Wojewódźtwo')}
    return {translate.get(param, param): msgs for param, msgs in data.items()}


class AdaptSeasonPlayerDataToCirclePresentation:
    @classmethod
    def adapt(cls, season_stat):
        return [
            {
                'title': _('Pierwszy skład'),
                'bs4_css': 'success',
                'value': math.ceil(season_stat['first_percent']),
                'shift': math.ceil(season_stat['from_bench_percent'] + season_stat['bench_percent'])
            },
            {
                'title': _('Z ławki'),
                'bs4_css': 'danger',
                'value': math.floor(season_stat['from_bench_percent']),
                'shift': math.floor(season_stat['bench_percent'])
            },
            {
                'title': _('Ławka'),
                'bs4_css': 'secondary',
                'value': math.floor(season_stat['bench_percent']), 
                'shift': 0
            }
        ]


class ShowProfile(generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "profiles/show_default_profile.html"
    http_method_names = ["get", "post"]

    def set_show_profile_page_title(self):
        if self.user.is_coach:
            if self.editable:
                return "TWÓJ TRENERSKI PROFIL"
            else:
                return "PROFIL TRENERSKI"
        if self.user.is_player:
            if self.editable:
                return "TWOJE CV"
            else:
                return "CV PIŁKARZA"
        if self.user.is_club:
            if self.editable:
                return "PROFIL TWOJEGO KLUBU"
            else:
                return "PROFIL KLUBU"
        if self.editable:
            return "TWÓJ PROFIL"
        return "PROFIL"

    def is_profile_observed(self, user, target):
        if user.is_authenticated():
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
                kwargs["role_form"] = self.get_role_declaration_form()  # @todo this mechanism can be replaced with ajax call

        kwargs["editable"] = self.editable

        kwargs['observed'] = self.is_profile_observed(request.user, user)
        
        kwargs['show_user'] = user
        kwargs['modals'] = self.modal_activity(request.user)
        kwargs['page_title'] = self.set_show_profile_page_title()

        # To dotyczy tylko playera!!!!
        if user.profile.has_data_id and user.profile.PROFILE_TYPE == 'player':
            _id = user.profile.data_mapper_id
            # kwargs["last_games"] = adapters.PlayerAdapter._get_user_last_games(_id)
            season_name = get_current_season()
            metrics = user.profile.playermetrics

            if metrics.how_old_days(games_summary=True) >= 7 or metrics.how_old_days(fantasy_summary=True) >= 7 or metrics.how_old_days(season_summary=True) >= 7:
                games_summary = adapters.PlayerLastGamesAdapter(_id).get(season=season_name, limit=3)  # should be profile.playermetrics.refresh_games_summary() and putted to celery.
                fantasy_summary = adapters.PlayerFantasyDataAdapter(_id).get(season=season_name)
                season_summary = adapters.PlayerStatsSeasonAdapter(_id).get(season=season_name)
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
                kwargs['season_circle_stats'] = AdaptSeasonPlayerDataToCirclePresentation.adapt(season_stat)
            else:
                kwargs['season_circle_stats'] = []

        if not self._is_owner(user) and request.user.is_authenticated():
            if InquiryRequest.objects.filter(
                    sender=self.request.user, recipient=user).exclude(
                        status__in=[InquiryRequest.STATUS_REJECTED, InquiryRequest.STATUS_ACCEPTED]).count() > 0:
                kwargs["pending_request"] = True
            else:
                kwargs["pending_request"] = False


        if user.profile.PROFILE_TYPE == 'player':
            self.template_name = "profiles/show_player_profile.html"
        elif user.profile.PROFILE_TYPE == 'coach':
            self.template_name = "profiles/show_coach_profile.html"
        else:
            self.template_name = "profiles/show_default_profile.html"

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        role_form = self.get_role_declaration_form()(request.POST)
        if role_form.is_valid():
            user.declared_role = role_form.cleaned_data['new']
            user.save()
            messages.success(request, "Gratulujemy. Profil użytkownika wybrany!")
        return redirect("profiles:show_self")

    def get_role_declaration_form(self):
        return forms.DeclareRoleForm

    def _is_owner(self, user):
        return user == self.request.user

    def _select_user_to_show(self):
        slug = self.kwargs.get('slug')
        if slug:
            profile_model = get_profile_model_from_slug(slug)
            profile = get_object_or_404(profile_model, slug=slug)
            profile.history.increment()  # @todo 1 coomit to
            if not self.request.user.is_authenticated():
                if self.request.user.is_coach:
                    profile.history.increment_coach()

                # if self.request.user.is_scout:  @todo
                #     profile.history.increment_coach()

            user = profile.user
        else:
            user = self.request.user
        return user


class RequestRoleChange(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        user = self.request.user
        if "cancel" in self.request.POST:
            self.delete_pending_user_roles(user)
            messages.success(request, _("Cofnięto prośbe o zmianę roli."))
        else:
            post_values = request.POST.copy()
            post_values['user'] = user

            role_form = forms.ChangeRoleForm(post_values)  # @todo how to add Current user role as a TextField.
            if role_form.is_valid():
                role_form.save()
            messages.success(request, _("Przyjęto zgloszenie o nową role."))
        return redirect("profiles:show_self")

    def delete_pending_user_roles(self, user):
        qs = models.RoleChangeRequest.objects.filter(user=user, approved=False)
        for q in qs:
            q.delete()


class EditAccountSettings(LoginRequiredMixin, generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "profiles/edit_account_settings.html"
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if "user_form" not in kwargs:
            kwargs["user_form"] = forms.UserForm(instance=user)

        if "role_form" not in kwargs:
            kwargs["role_form"] = forms.ChangeRoleForm()
        kwargs['modals'] = self.modal_activity(user)
        kwargs['page_title'] = _('Edycja ustawień konta')

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


class EditProfile(LoginRequiredMixin, generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "profiles/edit_profile.html"
    http_method_names = ["get", "post"]

    def set_edit_profile_page_title(self):
        if self.user.is_coach or self.user.is_club:
            return 'Edycja Profilu'
        if self.user.is_player:
            return "Edycja CV"
        return "Edycja profilu"

    def get(self, request, *args, **kwargs):
        self.user = user = self.request.user
        if "user_form" not in kwargs:  # @todo do wywalenia
            kwargs["user_form"] = forms.UserForm(instance=user)

        if "user_basic_form" not in kwargs:
            kwargs['user_basic_form'] = forms.UserBasicForm(instance=user)

        if "profile_form" not in kwargs:
            profile_form = get_profile_form_model(user)
            kwargs["profile_form"] = profile_form(instance=user.profile)

        if "role_form" not in kwargs:  # @todo do wywalenia
            kwargs["role_form"] = forms.ChangeRoleForm()

        kwargs['page_title'] = self.set_edit_profile_page_title()
        kwargs['modals'] = self.modal_activity(user)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user

        profile_form = get_profile_form_model(user)(
            request.POST,
            request.FILES,
            instance=user.profile
        )

        user_basic_form = forms.UserBasicForm(
            request.POST,
            request.FILES,
            instance=user)

        if not profile_form.is_valid() or not user_basic_form.is_valid():
            messages.error(
                request,
                _("Wystąpiły błąd podczas wysyłania formularza")
                # f"Wystąpiły błąd podczas wysyłania formularza" f". {user_form.errors} {profile_form.errors}"
            )
            # user_form = forms.UserForm(instance=user)
            # profile_form = get_profile_form_model(user)(instance=user.profile)
            return super().get(request, profile_form=profile_form, user_basic_form=user_basic_form)

        # Both forms are fine. Time to save!
        user_basic_form.save()
        profile = profile_form.save(commit=False)
        profile.user = user
        profile.save()
        messages.success(request, "Profile details saved!")
        return redirect("profiles:show_self")




from django.views import View

from crispy_forms.utils import render_crispy_form



class AccountVerification(LoginRequiredMixin, View):

    http_method_names = ['post', 'get']

    def get(self, request, *args, **kwargs):
        user = request.user
        if request.user.is_coach:
            form = forms.CoachVerificationForm(instance=user.profile)
        if request.user.is_club:
            form = forms.ClubVerificationForm(instance=user.profile)
        if request.user.is_player:
            form = forms.PlayerVerificationForm(instance=user.profile)
        data = {}
        data['form'] = render_crispy_form(form)
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile = user.profile

        if request.user.is_coach:
            verification_form = forms.CoachVerificationForm(request.POST, instance=profile)  # @todo how to add Current user role as a TextField.

        if request.user.is_club:
            verification_form = forms.ClubVerificationForm(request.POST, instance=profile)  # @todo how to add Current user role as a TextField.

        if request.user.is_player:
            verification_form = forms.PlayerVerificationForm(request.POST, instance=profile)  # @todo how to add Current user role as a TextField.

        data = {'success': False, 'url': None, 'form': None}

        if verification_form.is_valid():
            verification_form.save()
            user.unverify()
            user.save()
            messages.success(request, _("Przyjęto zgłoszenie werifikacje konta."))

            data['success'] = True
            data['url'] = reverse("profiles:show_self")
            return JsonResponse(data)
            # return redirect(reverse("profiles:show_self"))
        else:
            # response_data = {} d
            # messages.success(request, _("Błędnie wprowadzone dane."))
            # request.session['verification_form_errors'] = verification_form.errors
            data['form'] = render_crispy_form(verification_form)
            return JsonResponse(data)
            # redirect('profiles:show_self')
