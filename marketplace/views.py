import json
import logging
import math
import operator
from functools import reduce
from itertools import chain

from app import mixins
from clubs.models import Club, Gender, League, Seniority, Team, Voivodeship
from crispy_forms.utils import render_crispy_form
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest
from profiles.models import PlayerPosition
from profiles.utils import get_datetime_from_age
from roles import definitions
from stats import adapters
from users.models import User

from .forms import PlayerForClubAnnouncementForm, ClubForPlayerAnnouncementForm, \
    CoachForClubAnnouncementForm, ClubForCoachAnnouncementForm
from .models import ClubForPlayerAnnouncement, PlayerForClubAnnouncement, CoachForClubAnnouncement, \
    ClubForCoachAnnouncement, AnnouncementMeta
from .utils import get_datetime_from_year

User = get_user_model()


logger = logging.getLogger(__name__)


class AnnouncementFilterMixn:
    @property
    def filter_my_ann(self):
        value = self.request.GET.get('my_ann')
        if value:
            if value == 'on':
                return True
        return False


class AddAnnouncementView(LoginRequiredMixin, View):
    """Fetch form for announcements"""
    http_method_names = ['post', 'get']

    coach_looking_for_player = False
    coach_looking_for_club = False
    club_looking_for_player = False
    club_looking_for_coach = True

    def get(self, request, *args, **kwargs):
        user = request.user
        data = {
            'modal': {
                'body': None,
                'title': 'Dodaj nowe ogłoszenie',
                'button': {
                    'name': 'Dodaj ogłoszenie'
                }
            },
            'form': None,
            'messages': [],
        }

        _id = request.GET.get('id')
        if user.announcementuserquota.left <= 0 and not _id:
            return JsonResponse(data)
        elif _id:
            return JsonResponse({})  # TODO: TEMPORARY! remember to uncomment
            # _id = int(_id)
            # ann = Announcement.objects.get(id=_id)
            # data['modal']['title'] = "Edytuj ogłoszenie"
            # data['modal']['button']['name'] = 'Aktualizuj'
            # if user != ann.creator:
            #     return JsonResponse({})
            # else:
            #     form = AnnouncementForm(instance=ann)
            #     if user.is_coach:
            #         form.fields['club'].queryset = Club.objects.filter(name=user.profile.team_object.club.name)
            #         form.fields['league'].queryset = League.objects.filter(name=user.profile.team_object.league.name)
            #     elif user.is_club:
            #         form.fields['club'].queryset = Club.objects.filter(name=user.profile.club_object.name)
            #     else:
            #         return JsonResponse({})
        else:
            if user.is_coach:
                if self.coach_looking_for_player:  # temp
                    if user.profile.club_object:
                        form = ClubForPlayerAnnouncementForm(initial={
                            'club': user.profile.team_object.club,
                            'league': user.profile.team_object.league,
                            'voivodeship': user.profile.team_object.club.voivodeship,
                            'seniority': user.profile.team_object.seniority,
                            'gender': user.profile.team_object.gender,
                        })
                        form.fields['club'].queryset = Club.objects.filter(name=user.profile.team_object.club.name)
                        form.fields['league'].queryset = League.objects.filter(name=user.profile.team_object.league.name)
                    else:
                        form = ClubForPlayerAnnouncementForm(initial={})
                elif self.coach_looking_for_club:  # temp
                    form = CoachForClubAnnouncementForm(initial={})
                else:
                    return JsonResponse({})
            elif user.is_club:
                if self.club_looking_for_player:  # temp
                    if user.profile.club_object:
                        form = ClubForPlayerAnnouncementForm(initial={
                            'club': user.profile.club_object,
                            'voivodeship': user.profile.club_object.voivodeship
                        })
                        form.fields['club'].queryset = Club.objects.filter(name=user.profile.club_object.name)
                    else:
                        form = ClubForPlayerAnnouncementForm(initial={})
                elif self.club_looking_for_coach:  # temp
                    form = ClubForCoachAnnouncementForm(initial={})
                else:
                    return JsonResponse({})
            # form.instance.league = request.user.profile.display_league
            elif user.is_player:
                form = PlayerForClubAnnouncementForm(initial={
                        'position': user.profile.position_raw,
                        'voivodeship': user.profile.team_object.club.voivodeship,
                        'address': user.profile.address,
                        'practice_distance': user.profile.practice_distance,
                    })
            else:
                return JsonResponse({})

        form_raw_data = render_crispy_form(form)
        # form_raw_data = form_raw_data.replace('<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.0/jquery.min.js"></script>', '')
        data['form'] = form_raw_data
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        data = {
            'redirection_url': None,
            'success': False,
            'modal': {
                'body': None,
                'title': 'Dodaj nowe ogłoszenie',
                'button': {
                    'name': 'Dodaj ogłoszenie o testach'
                }
            },
            'form': None,
            'messages': [],
        }
        _id = request.POST.get('id')

        if user.announcementuserquota.left <= 0 and not _id:
            return JsonResponse(data)
        if _id:
            pass
            # a = Announcement.objects.get(id=int(_id))  # TODO: temporary! Uncomment!
            # form = AnnouncementForm(request.POST, instance=a)
            # if form.is_valid():
            #     ann = form.save(commit=False)
            #     ann.creator = request.user
            #     ann.save()
            #     form.save_m2m()
            #     messages.success(request, _("Ogłoszenia zaktualizowano"), extra_tags='alter-success')
            #
            #     data['success'] = True
            #     data['redirection_url'] = reverse("marketplace:announcements")
            #     return JsonResponse(data)
            # else:
            #
            #     data['form'] = render_crispy_form(form)
            #     return JsonResponse(data)
        else:
            if not user.announcementuserquota.can_make_request:
                return JsonResponse({'message': 'Limit ogłoszeń przekroczony.'})

            if user.is_coach:
                if self.coach_looking_for_club:
                    form = CoachForClubAnnouncementForm(request.POST)
                if self.coach_looking_for_player:
                    form = ClubForPlayerAnnouncementForm(request.POST)

            if user.is_club:
                if self.club_looking_for_coach:
                    form = ClubForCoachAnnouncementForm(request.POST)
                if self.club_looking_for_player:
                    form = ClubForPlayerAnnouncementForm(request.POST)

            if user.is_player:
                form = PlayerForClubAnnouncementForm(request.POST)

            if form.is_valid():
                ann = form.save(commit=False)
                ann.creator = request.user
                ann.save()
                form.save_m2m()
                user.announcementuserquota.increment()
                user.announcementuserquota.save()
                messages.success(request, _("Przyjęto ogłoszenia."), extra_tags='alter-success')

                data['success'] = True
                data['redirection_url'] = reverse("marketplace:announcements")
                return JsonResponse(data)
            else:
                data['form'] = render_crispy_form(form)
                return JsonResponse(data)


class AnnouncementsMetaView(generic.TemplateView, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin, AnnouncementFilterMixn):
    template_name = "marketplace/base.html"
    http_method_names = ["get"]
    paginate_limit = 9
    table_type = None
    page_title = 'Ogłoszenia'
    queried_classes = None

    def filter_queryset(self, queryset):
        now = timezone.now().date()
        queryset = queryset.filter(
            status__in=AnnouncementMeta.ACTIVE_STATES,
            disabled=False,
            expire__date__gte=now)
        if self.filter_my_ann is not False:
            queryset = queryset.filter(creator=self.request.user)

        if self.filter_league is not None:
            queryset = queryset.filter(league__name__in=self.filter_league)

        if self.filter_vivo is not None:
            queryset = queryset.filter(voivodeship__name__in=self.filter_vivo)

        if self.filter_position_exact is not None:  # used in playerforclub
            queryset = queryset.filter(position__name=self.filter_position_exact)

        if self.filter_target_league_exact is not None:  # used in playerforclub
            queryset = queryset.filter(target_league__name=self.filter_target_league_exact)

        if self.filter_year_min is not None:   # used in playerforclub
            mindate = get_datetime_from_year(self.filter_year_min)
            queryset = queryset.filter(creator__playerprofile__birth_date__year__gte=mindate.year)

        if self.filter_year_max is not None:   # used in playerforclub
            maxdate = get_datetime_from_year(self.filter_year_max)
            queryset = queryset.filter(creator__playerprofile__birth_date__year__lte=maxdate.year)

        # if self.filter_gender_exact is not None:
        #     queryset = queryset.filter(gender__name=self.filter_gender_exact)

        # if self.filter_seniority_exact is not None:
        #     queryset = queryset.filter(seniority__name=self.filter_seniority_exact)

        return queryset

    def get_queryset(self, queried_class=None) -> QuerySet:
        return queried_class.objects.all()

    def get_filters_values(self):  # @todo add cache from Redis here
        return {
            'seniority': list(Seniority.objects.values_list('name', flat=True)),
            'gender': list(Gender.objects.values_list('name', flat=True)),
            'voivodeship': list(Voivodeship.objects.values_list('name', flat=True)),
            'league': list(League.objects.values_list('name', flat=True)),
            'position': list(PlayerPosition.objects.values_list('name', flat=True))
        }

    def prepare_kwargs(self, kwargs):
        self._prepare_extra_kwargs(kwargs)

    def _prepare_extra_kwargs(self, kwargs):
        kwargs['my'] = False

    def get(self, request, *args, **kwargs):
        lista = []
        for i in self.queried_classes:
            queryset = self.get_queryset(i)
            queryset = self.filter_queryset(queryset)
            lista.append(queryset)
        queryset = list(chain(*lista))

        paginator = Paginator(queryset, self.paginate_limit)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        kwargs['page_obj'] = page_obj
        kwargs['page_title'] = self.page_title
        kwargs['type'] = self.table_type
        kwargs['filters'] = self.get_filters_values()
        self.prepare_kwargs(kwargs)
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        page_obj.elements = page_obj.end_index() - page_obj.start_index() + 1
        # kwargs['ammount'] = page_obj.count()
        return super().get(request, *args, **kwargs)


class AnnouncementsView(AnnouncementsMetaView):
    queried_classes = [ClubForPlayerAnnouncement,
                       ClubForCoachAnnouncement,
                       CoachForClubAnnouncement,
                       PlayerForClubAnnouncement]


class MyAnnouncementsView(AnnouncementsView):
    queried_classes = [ClubForPlayerAnnouncement, PlayerForClubAnnouncement]

    def get_queryset(self, queried_class=None):
        return queried_class.objects.filter(creator=self.request.user)

    def _prepare_extra_kwargs(self, kwargs):
        kwargs['my'] = True


class ClubForPlayerAnnouncementsView(AnnouncementsView):
    def get_queryset(self, queried_class=None):
        return ClubForPlayerAnnouncement.objects.filter(creator__declared_role="C")  # not true, i have to change it

    def _prepare_extra_kwargs(self, kwargs):
        kwargs['view_type'] = "club_for_player"
        super(ClubForPlayerAnnouncementsView, self)._prepare_extra_kwargs(kwargs)


class CoachForClubAnnouncementsView(AnnouncementsView):
    queried_classes = [CoachForClubAnnouncement]

    def _prepare_extra_kwargs(self, kwargs):
        kwargs['view_type'] = "coach_for_club"
        super(CoachForClubAnnouncementsView, self)._prepare_extra_kwargs(kwargs)


class ClubForCoachAnnouncementsView(AnnouncementsView):
    queried_classes = [ClubForCoachAnnouncement]

    def _prepare_extra_kwargs(self, kwargs):
        kwargs['view_type'] = "club_for_coach"
        super(ClubForCoachAnnouncementsView, self)._prepare_extra_kwargs(kwargs)


class PlayerForClubAnnouncementsView(AnnouncementsView):
    queried_classes = [PlayerForClubAnnouncement]

    def _prepare_extra_kwargs(self, kwargs):
        kwargs['view_type'] = "player_for_club"
        super(PlayerForClubAnnouncementsView, self)._prepare_extra_kwargs(kwargs)

