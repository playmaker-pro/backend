# external dependencies
import json
import logging
import math
import operator
from functools import reduce

from clubs.models import Club, Team, Seniority, League, Gender, Voivodeship
from crispy_forms.utils import render_crispy_form
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest
from app import mixins
from profiles.utils import get_datetime_from_age
from roles import definitions
from stats import adapters
from users.models import User

from .forms import AnnouncementForm
from profiles.models import PlayerPosition
from .models import Announcement

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
    '''Fetch form for annoucments'''
    http_method_names = ['post', 'get']

    def get(self, request, *args, **kwargs):

        user = request.user

        data = {
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

        _id = request.GET.get('id')
        if user.announcementuserquota.left <= 0 and not _id:
            return JsonResponse(data)
        elif _id:
            _id = int(_id)
            ann = Announcement.objects.get(id=_id)
            data['modal']['title'] = "Edytuj ogłoszenie"
            data['modal']['button']['name'] = 'Aktualizuj'
            if user != ann.creator:
                return JsonResponse({})
            else:
                form = AnnouncementForm(instance=ann)
                if user.is_coach:
                    form.fields['club'].queryset = Club.objects.filter(name=user.profile.team_object.club.name)
                    form.fields['league'].queryset = League.objects.filter(name=user.profile.team_object.league.name)
                elif user.is_club:
                    form.fields['club'].queryset = Club.objects.filter(name=user.profile.club_object.name)
                else:
                    return JsonResponse({})
        else:
            if user.is_coach or user.is_club:
                if user.is_coach:
                    form = AnnouncementForm(initial={
                        'club': user.profile.team_object.club,
                        'league': user.profile.team_object.league,
                        'voivodeship': user.profile.team_object.club.voivodeship,
                        'seniority': user.profile.team_object.seniority,
                        'gender': user.profile.team_object.gender,
                    })
                    form.fields['club'].queryset = Club.objects.filter(name=user.profile.team_object.club.name)
                    form.fields['league'].queryset = League.objects.filter(name=user.profile.team_object.league.name)

                elif user.is_club:
                    form = AnnouncementForm(initial={
                        'club': user.profile.club_object,
                        'voivodeship': user.profile.club_object.voivodeship
                    })
                    form.fields['club'].queryset = Club.objects.filter(name=user.profile.club_object.name)

                # form.instance.league = request.user.profile.display_league
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
            a = Announcement.objects.get(id=int(_id))
            form = AnnouncementForm(request.POST, instance=a)
            if form.is_valid():
                ann = form.save(commit=False)
                ann.creator = request.user
                ann.save()
                form.save_m2m()
                messages.success(request, _("Ogłoszenia zaktualizowano"))

                data['success'] = True
                data['redirection_url'] = reverse("marketplace:announcements")
                return JsonResponse(data)
            else:

                data['form'] = render_crispy_form(form)
                return JsonResponse(data)
        else:
            if not user.announcementuserquota.can_make_request:
                return JsonResponse({'message': 'Limit ogłoszeń przekroczony.'})

            if user.is_coach or user.is_club:
                form = AnnouncementForm(request.POST)

            if form.is_valid():
                ann = form.save(commit=False)
                ann.creator = request.user
                ann.save()
                form.save_m2m()
                user.announcementuserquota.increment()
                user.announcementuserquota.save()
                messages.success(request, _("Przyjęto ogłoszenia."))

                data['success'] = True
                data['redirection_url'] = reverse("marketplace:announcements")
                return JsonResponse(data)
            else:
                data['form'] = render_crispy_form(form)
                return JsonResponse(data)


class AnnouncementsView(generic.TemplateView, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin, AnnouncementFilterMixn):
    template_name = "marketplace/base.html"
    http_method_names = ["get"]
    paginate_limit = 9
    table_type = None
    page_title = 'Testy Piłkarskie'

    def filter_queryset(self, queryset):
        queryset = queryset.filter(
            expire__gt=timezone.now(),
            status__in=Announcement.ACTIVE_STATES,
            disabled=False
        )
        if self.filter_my_ann is not False:
            queryset = queryset.filter(creator=self.request.user)

        if self.filter_league is not None:
            queryset = queryset.filter(league__name__in=self.filter_league)

        if self.filter_position_exact is not None:
            queryset = queryset.filter(positions__name=self.filter_position_exact)

        if self.filter_gender_exact is not None:
            queryset = queryset.filter(gender__name=self.filter_gender_exact)

        if self.filter_seniority_exact is not None:
            queryset = queryset.filter(seniority__name=self.filter_seniority_exact)

        return queryset

    def get_queryset(self):
        return Announcement.objects.all()

    def get_filters_values(self):  # @todo add cache from Redis here
        return {
            'seniority': list(Seniority.objects.values_list('name', flat=True)),
            'gender': list(Gender.objects.values_list('name', flat=True)),
            'voivodeship': list(Voivodeship.objects.values_list('name', flat=True)),
            'league': list(League.objects.values_list('name', flat=True)),
            'position': list(PlayerPosition.objects.values_list('name', flat=True))
        }

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        paginator = Paginator(queryset, self.paginate_limit)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        kwargs['page_obj'] = page_obj
        kwargs['page_title'] = self.page_title
        kwargs['type'] = self.table_type
        kwargs['filters'] = self.get_filters_values()
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        page_obj.elements = page_obj.end_index() - page_obj.start_index() + 1
        # kwargs['ammount'] = page_obj.count()
        return super().get(request, *args, **kwargs)
