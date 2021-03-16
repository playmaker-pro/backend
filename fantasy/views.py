# Create your views here.
# external dependencies
import json
import logging
import math
import operator
from functools import reduce

from app import mixins
from app.base.views import BasePMView
from clubs.models import Club, Gender, League, Seniority, Team, Voivodeship
from crispy_forms.utils import render_crispy_form
from data.models import Game, Player
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import F, Q, Sum, Value, Window
from django.db.models.functions import Concat, DenseRank
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest
from notifications import message
from profiles.models import PlayerPosition
from profiles.utils import get_datetime_from_age
from roles import definitions
from stats import adapters
from stats.utilites import (conver_zpn_for_api, translate_league_name,
                            translate_team_name)
from clubs.models import Seniority, Season

from .models import PlayerFantasyRank


User = get_user_model()


logger = logging.getLogger(__name__)


class FantasyView(BasePMView, mixins.ViewFilterMixin, mixins.FilterPlayerViewMixin):
    page_title = 'Fantasy'
    template_name = "fantasy/base.html"
    paginate_limit = 20

    def filter_queryset(self, queryset):
        if self.filter_season_exact is not None:
            queryset = queryset.filter(season__name=self.filter_season_exact)

        if self.filter_leg is not None:
            queryset = queryset.filter(player__playerprofile__prefered_leg=self.filter_leg)

        if self.filter_is_senior is not None:
            queryset = queryset.filter(senior=self.filter_is_senior)

        if self.filter_name_of_team is not None:
            queryset = queryset.filter(player__playerprofile__team_object__name__icontains=self.filter_name_of_team)

        if self.filter_league is not None:
            queryset = queryset.filter(player__playerprofile__team_object__league__name__in=self.filter_league)

        if self.filter_first_last is not None:
            queryset = queryset.annotate(
                fullname=Concat('player__first_name', Value(' '), 'player__last_name'))
            queryset = queryset.filter(
                fullname__icontains=self.filter_first_last)

        if self.filter_vivo is not None:
            vivos = [i for i in self.filter_vivo]
            clauses = (Q(player__playerprofile__team_object__club__voivodeship__name=p) for p in vivos)
            query = reduce(operator.or_, clauses)
            queryset = queryset.filter(query)

        if self.filter_age_min is not None:
            mindate = get_datetime_from_age(self.filter_age_min)
            queryset = queryset.filter(player__playerprofile__birth_date__year__lte=mindate.year)

        if self.filter_age_max is not None:
            maxdate = get_datetime_from_age(self.filter_age_max)
            queryset = queryset.filter(player__playerprofile__birth_date__year__gte=maxdate.year)

        if self.filter_position is not None:
            queryset = queryset.filter(player__playerprofile__position_raw=self.filter_position)

        return queryset

    def get_filters_values(self):  # @todo add cache from Redis here
        return {
            'season': list(Season.objects.values_list('name', flat=True)),
        }

    def get(self, request, format=None, *args, **kwargs):
        # players = PlayerFantasyRank.objects.all().order_by('score')
        queryset = PlayerFantasyRank.objects.annotate(place=Window(
            expression=DenseRank(),
            order_by=[
                F('score').desc(),
            ]))
        queryset = self.filter_queryset(queryset)
        paginator = Paginator(queryset, self.paginate_limit)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        kwargs['page_obj'] = page_obj
        kwargs['filters'] = self.get_filters_values()
        page_obj.elements = page_obj.end_index() - page_obj.start_index() + 1
        self.prepare_kwargs(kwargs)
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        return super().get(request, *args, **kwargs)
