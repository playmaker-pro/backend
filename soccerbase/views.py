
from django.db.models import F
from app import mixins, utils

from clubs.models import Club, Team
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View, generic
from profiles.utils import get_datetime_from_age
from roles import definitions
from users.models import User
import operator
from functools import reduce
from django.db.models import Q, Value
from app.mixins import FilterPlayerViewMixin


TABLE_TYPE_PLAYER = definitions.PLAYER_SHORT
TABLE_TYPE_TEAM = definitions.CLUB_SHORT
TABLE_TYPE_COACH = definitions.COACH_SHORT


class TableView(generic.TemplateView, mixins.PaginateMixin, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin):
    template_name = "soccerbase/table.html"
    http_method_names = ["get"]
    paginate_limit = 15
    table_type = None
    page_title = 'Baza piłkarska'

    def filter_queryset(self, queryset):
        return queryset

    def get_queryset(self):
        return []

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        kwargs['page_obj'] = self.paginate(queryset, limit=self.paginate_limit)
        kwargs['page_title'] = self.page_title
        kwargs['type'] = self.table_type
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        # kwargs['ammount'] = page_obj.count()
        return super().get(request, *args, **kwargs)


class PlayersTable(TableView, FilterPlayerViewMixin):
    table_type = TABLE_TYPE_PLAYER
    page_title = 'Baza piłkarzy'

    def get_queryset(self):
        return User.objects.filter(
            declared_role='P',
            state=User.STATE_ACCOUNT_VERIFIED,
            playerprofile__birth_date__lte=get_datetime_from_age(15)).order_by(F('last_login').desc(nulls_last=True))


class TeamsTable(TableView):
    table_type = TABLE_TYPE_TEAM
    page_title = 'Baza drużyn'

    def filter_queryset(self, queryset):
        if self.filter_league is not None:
            queryset = queryset.filter(league__name__in=self.filter_league)

        if self.filter_vivo is not None:
            vivos = [i for i in self.filter_vivo]
            clauses = (Q(club__voivodeship__name=p) for p in vivos)
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
        return User.objects.filter(
            declared_role='T',
            state=User.STATE_ACCOUNT_VERIFIED
        ).order_by(F('last_login').desc(nulls_last=True))

    def filter_queryset(self, queryset):

        if self.filter_first_last is not None:
            queryset = queryset.annotate(fullname=Concat('first_name', Value(' '), 'last_name'))
            queryset = queryset.filter(fullname__icontains=self.filter_first_last)
            # queryset = queryset.filter(Q(first_name__icontains=self.filter_first_last) | Q(last_name__icontains=self.filter_first_last))

        if self.filter_name_of_club is not None:
            queryset = queryset.filter(coachprofile__team_object__club__name__icontains=self.filter_name_of_club)

        if self.filter_league is not None:
            queryset = queryset.filter(coachprofile__team_object__league__name__in=self.filter_league)

        if self.filter_vivo is not None:
            vivo = [i[:-1].upper() for i in self.filter_vivo]

            clauses = (Q(coachprofile__team_object__club__voivodeship__name=p) for p in vivo)
            query = reduce(operator.or_, clauses)
            queryset = queryset.filter(query)

        return queryset
