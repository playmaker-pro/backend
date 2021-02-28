from django.shortcuts import render

# Create your views here.
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
from notifications import message
from profiles.models import PlayerPosition
from data.models import Player, Game

from django.db.models import Sum
User = get_user_model()


logger = logging.getLogger(__name__)
from stats.utilites import translate_team_name, translate_league_name, conver_zpn_for_api

class QueryParamsMixin:
    '''Query params handler for Playmaker Wix setup.
    '''
    @property
    def query_wix_id(self):
        return self.request.query_params.get('wix_id', 'errrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr')

    @property
    def query_season(self):
        return self.request.query_params.get('season', None)

    @property
    def query_position(self):
        return self.request.query_params.get('position', None)

    @property
    def query_zpn(self):
        return self.request.query_params.get('zpn', None)

    @property
    def query_league(self):
        return self.request.query_params.get('league', None)

    @property
    def query_team(self):
        club = self.request.query_params.get('team', None)
        if club is not None:
            return club.lower()
        else:
            return club

    @property
    def query_excluded_leagues_codes(self):
        return self.request.query_params.get('excludelc', None)
    
    @property
    def query_limit(self):
        return self.request.query_params.get('limit', 30)
    
    @property
    def query_page(self):
        return self.request.query_params.get('page', None)

    @property
    def query_seniority(self):
        # expected: senior or junior str
        return self.request.query_params.get('seniority', None)

    @property
    def query_playername(self):
        return self.request.query_params.get('playername', None)
        

class WixMixin:
    '''Taking Player based on wix_id param
    '''
    def get_wixplayer(self, wix_id):
        try:
            pl = Player.objects.get(wix_id=wix_id)
        except Player.DoesNotExist:
            pl = None
        return pl


class WixApiMixin(QueryParamsMixin, WixMixin):
    pass


class PaginationHandlerMixin(object):

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        else:
            pass
        return self._paginator

    def paginate_queryset(self, queryset):
        
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset,
                   self.request, view=self)
                   
    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

from rest_framework.pagination import PageNumberPagination
class BasicPagination(PageNumberPagination):
    page_size_query_param = 'limit'


from app.base.views import BasePMView
from .models import PlayerFantasyRank

class FantasyView(BasePMView):
    page_title = 'Fantasy'
    template_name = "fantasy/base.html"
    paginate_limit = 20

    def get(self, request, format=None, *args, **kwargs):
        players = PlayerFantasyRank.objects.all().order_by('score')
        paginator = Paginator(players, self.paginate_limit)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        kwargs['page_obj'] = page_obj
        self.prepare_kwargs(kwargs)
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        return super().get(request, *args, **kwargs)


class FantasyView2(generic.TemplateView, WixApiMixin, PaginationHandlerMixin):
    page_title = 'Fantasy'
    template_name = "fantasy/base.html"
    paginate_limit = 20
    pagination_class = BasicPagination

    def get(self, request, format=None, *args, **kwargs):
        players = Player.objects.filter(wix_id__isnull=False, position__isnull=False)

        # players = self.filter_queryset(players)
        # page = self.paginate_queryset(players)  # need to be here

        rows = self.serialize(players)

        # sorting and seting place 
        rows_s = sorted(rows, key = lambda i: i['points'], reverse=True) 
         
        for i, s in enumerate(rows_s):
            s['place'] = i + 1
        
        # Another modification from clinet request (altering behavior of API to show ranking despite playername query param)
        if None is not None:
            new_output = []
            for ss in rows_s:
                full_name = ss['full_name']
                if full_name is not None:
                    full_name = full_name.lower()
                if self.query_playername.lower() in full_name:
                    new_output.append(ss)
            rows_s = new_output


        #  paginating list
        def chunks(lst, n):
            out = []
            for i in range(0, len(lst), n):
                out.append(lst[i:i + n])
            return out

        chunked_data = chunks(rows_s, int(self.query_limit))    

        if self.query_page is not None:
            data = chunked_data[int(self.query_page) - 1]
        else:
            try:  # in case of empty queryset: due to more complex request comming from PM.
                data = chunked_data[0] 
            except IndexError:
                data = []
        serializer = self.get_paginated_response(data)
        
        paginator = Paginator(serializer.data, self.paginate_limit)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        kwargs['page_obj'] = page_obj
        # kwargs['filters'] = self.get_filters_values()
        # kwargs['data'] = serializer.data
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        return super().get(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        # main queryset platers
        if self.query_position is not None:
            queryset = queryset.filter(position=self.query_position)

        if self.query_league is not None:
            lookup = {f'meta__{self.query_season}__league': self.query_league}
            queryset = queryset.filter(**lookup)

        if self.query_team is not None:
            lookup = {f'meta__{self.query_season}__team': self.query_team}
            queryset = queryset.filter(**lookup)

        if self.query_zpn is not None:
            lookup = {f'meta__{self.query_season}__zpn': self.query_zpn}
            queryset = queryset.filter(**lookup)

        #if self.query_playername is not None:
        #    queryset = queryset.filter(full_name__icontains=self.query_playername)

        return queryset

    def _filter_players_stats(self, queryset):
        # List of senior leagues codes
        SENIOR_LEAGUE_CODES = [1, 2, 3, 4, 5, 6, 7, 20, 21, 5000, 5002, 23, 24]
        JUNIOR_LEAGUE_CODES = [8, 9, 10, 11, 12, 13]
        # List of junior leagues codes
        #if self.query_seniority == 'senior':
        queryset = queryset.filter(league__code__in=SENIOR_LEAGUE_CODES)
        #elif self.query_seniority == 'junior':
        #    queryset = queryset.filter(league__code__in=JUNIOR_LEAGUE_CODES)
            
        # # By default exlcuded 
        # if self.query_excluded_leagues_codes is not None:
        #     excluded_leagues_codes = [int(c) for c in self.query_excluded_leagues_codes.split(',')] 
        queryset = queryset.exclude(league__code__in=[14,15,16,17,18,19,100,5003,5004,5005,5006,5007,5023])

        # Commented according to CR-8.3
        # if self.query_league:
        #     queryset = queryset.filter(league__code=reverse_translate_league_name(self.query_league))
            
        # if self.query_team:
        #     queryset = queryset.filter(team_name=reverse_translate_team_name(self.query_team))

        # if self.query_zpn:
        #     queryset = queryset.filter(league__zpn_code_name=self.query_zpn)
        return queryset

    def serialize(self, queryset):
        players = queryset
        rows = [] 
        
        for player in players.iterator():
            points = 0
            ps = player.playerstats.select_related('game', 'gamefication', 'league', 'season').filter(season__name='2020/2021')
            ps = self._filter_players_stats(ps)
            games = ps.count()
            
            if games != 0:
                points = ps.aggregate(Sum('gamefication__score')).get('gamefication__score__sum') or 0 
                meta = player.meta
                default_organization = {'league': None, 'team':None, 'zpn': None, 'league_code': None}
                if meta:
                    organization = meta.get('2020/2021', default_organization)
                else:
                    organization = default_organization
                
                club_name = translate_team_name(organization['team'])  # make sure that API reponse format club name into upper case
                if club_name is not None and isinstance(club_name, str):
                    club_name = club_name.upper()

                row = {
                    'place': 0, 
                    'full_name': player.full_name.title(),
                    #'wixid': player.wix_id,  # debug 
                    #'_meta': player.meta,  # debug
                    'position': player.position, 
                    'league_name': translate_league_name(organization['league_code'], organization['league']), 
                    'club_name': club_name,
                    'zpncode': conver_zpn_for_api(organization['zpn']), 
                    'season': '2020/2021',
                    'points': points,
                    'games_number': games
                }
                rows.append(row)
            else:
                continue

        return rows