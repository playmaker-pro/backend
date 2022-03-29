from django.conf import settings
from django.db.models import F
from app import mixins, utils

from clubs.models import Club, Team, League
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View, generic
from profiles.utils import get_datetime_from_age, get_datetime_from_year
from roles import definitions
from users.models import User
import operator
from functools import reduce
from django.db.models import Q, Value
from app.mixins import FilterPlayerViewMixin
from django.utils import timezone


TABLE_TYPE_PLAYER = definitions.PLAYER_SHORT
TABLE_TYPE_TEAM = definitions.CLUB_SHORT
TABLE_TYPE_COACH = definitions.COACH_SHORT


class TableView(generic.TemplateView, mixins.PaginateMixin, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin):
    template_name = "soccerbase/table.html"
    http_method_names = ["get"]
    paginate_limit = 25
    table_type = None
    page_title = 'Baza piłkarska'

    def filter_queryset(self, queryset):
        return queryset

    def get_queryset(self):
        return []

    def add_more_to_kwargs(self, kwargs):
        pass

    def get(self, request, *args, **kwargs):
        self.is_foregin = False
        self.is_juniors = False

        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        total_items = request.GET.get('total_items')
        if total_items:
            self.paginate_limit = total_items

        page_obj = self.paginate(queryset, limit=self.paginate_limit)

        kwargs["last_page"] = self.last_page
        kwargs['page_num_range'] = self.page_num_range
        kwargs['custom_range'] = self.custom_range
        kwargs['page_obj'] = page_obj
        kwargs['page_title'] = self.page_title
        kwargs['type'] = self.table_type
        kwargs['vivos'] = settings.VOIVODESHIP_CHOICES
        kwargs['leagues'] = League.objects.is_top_parent()
        self.add_more_to_kwargs(kwargs)
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        # kwargs['ammount'] = page_obj.count()
        return super().get(request, *args, **kwargs)


class PlayersTable(TableView):
    table_type = TABLE_TYPE_PLAYER
    page_title = 'Baza piłkarzy'

    def add_more_to_kwargs(self, kwargs):
        kwargs['foregin'] = self.is_foregin or None
        kwargs['juniors'] = self.is_juniors or None

    def filter_queryset(self, queryset):
        if self.filter_leg is not None:
            queryset = queryset.filter(
                playerprofile__prefered_leg=self.filter_leg)

        if self.filter_league is not None:
            league = (Q(
                playerprofile__team_object__league__highest_parent__name__icontains=league)
                for league in self.filter_league
            )
            query = reduce(operator.or_, league)
            queryset = queryset.filter(query)

        if self.filter_first_last is not None:
            queryset = queryset.annotate(fullname=Concat('first_name', Value(' '), 'last_name'))
            queryset = queryset.filter(fullname__icontains=self.filter_first_last)

        if self.filter_vivo is not None:
            vivos = [i.replace('-', '') for i in self.filter_vivo]
            clauses = (Q(
                playerprofile__team_object__club__voivodeship__name__icontains=p
            ) for p in vivos)
            query = reduce(operator.or_, clauses)
            queryset = queryset.filter(query)

        if self.filter_year_min is not None:
            mindate = get_datetime_from_year(self.filter_year_min)
            queryset = queryset.filter(playerprofile__birth_date__year__gte=mindate.year)

        if self.filter_year_max is not None:
            maxdate = get_datetime_from_year(self.filter_year_max)
            queryset = queryset.filter(playerprofile__birth_date__year__lte=maxdate.year)

        # breakpoint()
        # if self.filter_age_range is not None:
        #     mindate = get_datetime_from_age(self.filter_age_range[0])
        #     maxdate = get_datetime_from_age(self.filter_age_range[1])
        #     queryset = queryset.filter(playerprofile__birth_date__range=[maxdate, mindate])  # bo 0,20   to data urodzin 2000-09-01----2020-09-01

        if self.filter_position:
            queryset = queryset.filter(playerprofile__position_raw__in=self.filter_position)
        return queryset

    def get_queryset(self):
        return User.objects.select_related("playerprofile").filter(
            declared_role='P',
            state=User.STATE_ACCOUNT_VERIFIED,
            playerprofile__birth_date__lte=get_datetime_from_age(15)).order_by(F('last_login').desc(nulls_last=True))


class PlayerTalbeQuickFilter(generic.TemplateView, mixins.PaginateMixin, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin):
    template_name = "soccerbase/table.html"
    http_method_names = ["get"]
    paginate_limit = 25
    table_type = None
    table_type = TABLE_TYPE_PLAYER
    page_title = 'Baza piłkarzy'

    def get_queryset(self):
        return User.objects.select_related("playerprofile").filter(
            declared_role='P',
            state=User.STATE_ACCOUNT_VERIFIED,
            playerprofile__birth_date__lte=get_datetime_from_age(15)).order_by(F('last_login').desc(nulls_last=True))

    def filter_queryset(self, queryset):

        if self.is_foregin is True:
            queryset = queryset.exclude(playerprofile__country='PL')

        if self.is_juniors is True:
            queryset = queryset.exclude(playerprofile__birth_date__year__lt=timezone.now().year - 20)

        if self.filter_leg is not None:
            queryset = queryset.filter(
                playerprofile__prefered_leg=self.filter_leg)

        if self.filter_league is not None:
            queryset = queryset.filter(
                playerprofile__team_object__league__highest_parent__name__in=self.filter_league
                )

        if self.filter_first_last is not None:
            queryset = queryset.annotate(fullname=Concat('first_name', Value(' '), 'last_name'))
            queryset = queryset.filter(fullname__icontains=self.filter_first_last)

        if self.filter_vivo is not None:
            vivos = [i for i in self.filter_vivo]
            clauses = (Q(playerprofile__team_object__club__voivodeship__name=p) for p in vivos)
            query = reduce(operator.or_, clauses)
            queryset = queryset.filter(query)

        if self.filter_age_min is not None:
            mindate = get_datetime_from_age(self.filter_age_min)
            queryset = queryset.filter(playerprofile__birth_date__year__lte=mindate.year)

        if self.filter_age_max is not None:
            maxdate = get_datetime_from_age(self.filter_age_max)
            queryset = queryset.filter(playerprofile__birth_date__year__gte=maxdate.year)

        # if self.filter_age_range is not None:
        #     mindate = get_datetime_from_age(self.filter_age_range[0])
        #     maxdate = get_datetime_from_age(self.filter_age_range[1])
        #     queryset = queryset.filter(playerprofile__birth_date__range=[maxdate, mindate])  # bo 0,20   to data urodzin 2000-09-01----2020-09-01
        if self.filter_position is not None:
            queryset = queryset.filter(playerprofile__position_raw__in=self.filter_position)
        return queryset

    def get(self, request, quick_filter, *args, **kwargs):
        self.is_foregin = False
        self.is_juniors = False

        if 'foregin' in quick_filter:
            self.is_foregin = True
        if 'juniors' in quick_filter:
            self.is_juniors = True
        kwargs['foregin'] = self.is_foregin or None
        kwargs['juniors'] = self.is_juniors or None
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        total_items = request.GET.get('total_items')
        if total_items:
            self.paginate_limit = total_items

        page_obj = self.paginate(queryset, limit=self.paginate_limit)

        kwargs["last_page"] = self.last_page
        kwargs['page_num_range'] = self.page_num_range
        kwargs['custom_range'] = self.custom_range

        kwargs['page_obj'] = page_obj
        kwargs['page_title'] = self.page_title
        kwargs['type'] = self.table_type
        # self.add_more_to_kwargs(kwargs)
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        # kwargs['ammount'] = page_obj.count()
        return super().get(request, *args, **kwargs)


class TeamsTable(TableView):
    table_type = TABLE_TYPE_TEAM
    page_title = 'Baza drużyn'

    def filter_queryset(self, queryset):

        if self.filter_league is not None:
            league = (Q(
                league__highest_parent__name__icontains=league)
                for league in self.filter_league
            )
            query = reduce(operator.or_, league)
            queryset = queryset.filter(query)

        if self.filter_vivo is not None:
            vivos = [i.replace('-', '') for i in self.filter_vivo]
            clauses = (Q(club__voivodeship__name__icontains=p) for p in vivos)
            query = reduce(operator.or_, clauses)
            queryset = queryset.filter(query)

        if self.filter_name_of_club is not None:
            queryset = queryset.filter(club__name__icontains=self.filter_name_of_club)

        if self.filter_name_of_team is not None:
            queryset = queryset.filter(name__icontains=self.filter_name_of_team)

        return queryset

    def get_queryset(self):
        return Team.objects.filter(visible=True)


class CoachesTable(TableView):
    table_type = TABLE_TYPE_COACH
    page_title = 'Baza trenerów'

    def get_queryset(self):
        return User.objects.select_related("coachprofile", "coachprofile__team_object").filter(
            declared_role='T',
            state=User.STATE_ACCOUNT_VERIFIED
        ).order_by(F('last_login').desc(nulls_last=True))

    def filter_queryset(self, queryset):

        if self.filter_first_last is not None:
            queryset = queryset.annotate(fullname=Concat('first_name', Value(' '), 'last_name'))
            queryset = queryset.filter(fullname__icontains=self.filter_first_last)
            # queryset = queryset.filter(Q(first_name__icontains=self.filter_first_last) | Q(last_name__icontains=self.filter_first_last))

        if self.filter_name_of_team is not None:
            queryset = queryset.filter(
                coachprofile__team_object__name__icontains=self.filter_name_of_team
            )

        if self.filter_league is not None:
            queryset = queryset.filter(coachprofile__team_object__league__highest_parent__name__in=self.filter_league)

        if self.filter_vivo is not None:

            voivo = [i.lower().replace('-', '') for i in self.filter_vivo]
            clauses = (Q(coachprofile__team_object__club__voivodeship__name=p) for p in voivo)
            query = reduce(operator.or_, clauses)
            queryset = queryset.filter(query)

        return queryset
