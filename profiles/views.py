# external dependencies
import math

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


class PaginateMixin:
    @property
    def page(self):
        return self.request.GET.get('page') or 1

    def paginate(self, data):
        paginator = Paginator(data, self.paginate_limit)
        page_number = self.page
        return paginator.get_page(page_number)


class ProfileObservers(generic.TemplateView):
    template_name = "profiles/observers.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        kwargs["data"] = ['obserowany x', 'obserwowany y']
        return super().get(request, *args, **kwargs)


class ProfileRequests(generic.TemplateView):
    template_name = "profiles/requests.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        kwargs["data"] = ['kots X kogos Y', 'ktos Z kogos Y']
        return super().get(request, *args, **kwargs)


class ProfileFantasy(generic.TemplateView):
    template_name = "profiles/fantasy2.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        _id = user.profile.data_mapper_id
        season_name = get_current_season()
        kwargs['season_name'] = season_name
        kwargs["fantasy"] = self.get_data_or_calculate()
        return super().get(request, *args, **kwargs)

    def get_data_or_calculate(self):
        season_name = get_current_season()
        user = self.request.user
        _id = user.profile.data_mapper_id
        if self.request.user.profile.playermetrics.how_old_days(fantasy=True) >= 7 and self.request.user.profile.has_data_id:
            fantasy = adapters.PlayerFantasyDataAdapter(_id).get(season=season_name, full=True)
            user.profile.playermetrics.update_fantasy(fantasy)
        return user.profile.playermetrics.fantasy


class ProfileCarrier(generic.TemplateView):
    template_name = "profiles/carrier.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        _id = user.profile.data_mapper_id
        import json

        kwargs["carrier"] = self.get_data_or_calculate()
        return super().get(request, *args, **kwargs)

    def get_data_or_calculate(self):
        user = self.request.user
        _id = user.profile.data_mapper_id
        if self.request.user.profile.playermetrics.how_old_days(season=True) >= 7 and self.request.user.profile.has_data_id:
            season = adapters.PlayerStatsSeasonAdapter(_id).get(groupped=True)
            user.profile.playermetrics.update_season(season)
        user.profile.playermetrics.refresh_from_db()
        return user.profile.playermetrics.season


class ProfileGames(generic.TemplateView, PaginateMixin):
    # @todo: add limit handling for futhure unknown usage.
    template_name = "profiles/games.html"
    http_method_names = ["get"]
    paginate_limit = 15

    def get(self, request, *args, **kwargs):
        games = self.get_data_or_calculate()
        games = games or []
        kwargs['page_obj'] = self.paginate(games)
        return super().get(request, *args, **kwargs)

    def get_data_or_calculate(self):
        user = self.request.user
        _id = user.profile.data_mapper_id
        if self.request.user.profile.playermetrics.how_old_days(games=True) >= 7 and self.request.user.profile.has_data_id:
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

    def get(self, request, *args, **kwargs):
        user = self._select_user_to_show()

        if self._is_owner(user):
            kwargs["editable"] = True
            if user.declared_role is None:  # @todo - this is  not pretty.
                kwargs["role_form"] = self.get_role_declaration_form()  # @todo this mechanism can be replaced with ajax call

        kwargs['show_user'] = user
        kwargs['modals'] = self.modal_activity(user)

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

        if not self._is_owner(user):
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
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user

        user_form = forms.UserForm(
            request.POST,
            request.FILES,
            instance=user)

        if not (user_form.is_valid()):
            messages.error(request, _("Wystąpiły błąd podczas wysyłania formularza"))
            return super().get(request, user_form=user_form, role_form=forms.ChangeRoleForm())

        user_form.save()
        messages.success(request, "Profile details saved!")
        return redirect("profiles:show_self")


class EditProfile(LoginRequiredMixin, generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "profiles/edit_profile.html"
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if "user_form" not in kwargs:  # @todo do wywalenia
            kwargs["user_form"] = forms.UserForm(instance=user)

        if "profile_form" not in kwargs: 
            profile_form = get_profile_form_model(user)
            kwargs["profile_form"] = profile_form(instance=user.profile)

        if "role_form" not in kwargs:  # @todo do wywalenia
            kwargs["role_form"] = forms.ChangeRoleForm()
        kwargs['modals'] = self.modal_activity(user)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user

        profile_form = get_profile_form_model(user)(
            request.POST,
            request.FILES,
            instance=user.profile
        )

        if not profile_form.is_valid():
            messages.error(
                request,
                _("Wystąpiły błąd podczas wysyłania formularza")
                # f"Wystąpiły błąd podczas wysyłania formularza" f". {user_form.errors} {profile_form.errors}"
            )
            # user_form = forms.UserForm(instance=user)
            # profile_form = get_profile_form_model(user)(instance=user.profile)
            return super().get(request, profile_form=profile_form)

        # Both forms are fine. Time to save!
        profile = profile_form.save()
        messages.success(request, "Profile details saved!")
        return redirect("profiles:show_self")


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


def inquiry(request):
    response_data = {'status': False}
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
                    response_data['messages'] = 'Już jest takie zgłoszenie.'
            else:
                InquiryRequest.objects.create(sender=user, recipient=recipient)
                user.userinquiry.increment()
                response_data['status'] = True

                response_data['messages'] = 'Powiadomienie wyslane.'

        response_data['open_modal'] = action_modal
        return JsonResponse(response_data)

from django.views import View

from crispy_forms.utils import render_crispy_form

class AccountVerification(View):

    http_method_names = ['post', 'get']

    def get(self, request, *args, **kwargs):
        form = forms.VerificationForm()
        data = {}
        data['form'] = render_crispy_form(form)
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile = user.profile
        verification_form = forms.VerificationForm(request.POST, instance=profile)  # @todo how to add Current user role as a TextField.

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

def observe(request):
    response_data = {}

    if request.POST.get('action') == 'post':
        slug = request.POST.get('slug')
        action_modal = get_modal_action(request.user)

        response_data['title'] = slug + 'ssss'
        response_data['open_modal'] = action_modal
        return JsonResponse(response_data)
