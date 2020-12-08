from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View, generic

from clubs.models import Club, Team
from users.models import User
from django.core.paginator import Paginator

from roles import definitions
from profiles.utils import get_datetime_from_age
from django.db.models import Q
import operator
from functools  import reduce
TABLE_TYPE_PLAYER = definitions.PLAYER_SHORT
TABLE_TYPE_TEAM = definitions.CLUB_SHORT
TABLE_TYPE_COACH = definitions.COACH_SHORT


from profiles import mixins  # @todo move this to platfrom app


class TableView(generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "soccerbase/tables/table.html"
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
        paginator = Paginator(queryset, self.paginate_limit)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        kwargs['page_obj'] = page_obj
        kwargs['page_title'] = self.page_title
        kwargs['type'] = self.table_type
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        page_obj.elements = page_obj.end_index() - page_obj.start_index() + 1
        # kwargs['ammount'] = page_obj.count()
        return super().get(request, *args, **kwargs)


class PlayersTable(TableView):
    table_type = TABLE_TYPE_PLAYER
    page_title = 'Baza piłkarzy'

    @property
    def filter_league(self):
        # value = self.request.GET.get('league')
        value = self.request.GET.getlist('league')
        if value:
            return value
        
    @property
    def filter_vivo(self):
        # value = self.request.GET.get('league')
        value = self.request.GET.getlist('vivo')
        if value:
            return value

    @property
    def filter_age_max(self):
        value = self.request.GET.get('age_max')
        if value:
            return int(value)

    @property
    def filter_age_min(self):
        value = self.request.GET.get('age_min')
        if value:
            return int(value)
    @property
    def filter_first_last(self):
        value = self.request.GET.get('first_last')
        return value

    @property
    def filter_age_range(self):
        value = self.request.GET.get('age_range')
        if isinstance(value, str) and value != '' and value is not None:
            if value == '----':
                return None
            elif value == 'do 20 lat':
                return (0, 20)
            elif value == 'od 21 do 26':
                return (21, 26)
            elif value == 'od 27 do 34':
                return (27, 34)
            elif value == 'powyżej 35':
                return (35, 199)
            else:
                return None
    @property
    def filter_position(self):
        POSITION_CHOICES = [
            (1, 'Bramkarz'),
            (2, 'Obrońca Lewy'),
            (3, 'Obrońca Prawy'),
            (4, 'Obrońca Środkowy'),
            (5, 'Pomocnik defensywny (6)'),
            (6, 'Pomocnik środkowy (8)'),
            (7, 'Pomocnik ofensywny (10)'),
            (8, 'Skrzydłowy'),
            (9, 'Napastnik'),
        ]

        value = self.request.GET.get('position')
        # return value
        if value == '----':
            return None
        for number, txt in POSITION_CHOICES:
            if txt == value:
                return number
        return None

    @property
    def filter_leg(self):
        '''
        LEG_CHOICES = (
        (1, 'Lewa'),
        (2, 'Prawa'),)
        '''
        value = self.request.GET.get('leg')
        if value == '----':
            return None
        elif value == 'lewa':
            return 1
        elif value == 'prawa':
            return 2

    def filter_queryset(self, queryset):
        if self.filter_leg is not None:
            queryset = queryset.filter(playerprofile__prefered_leg=self.filter_leg)

        if self.filter_league is not None:
            queryset = queryset.filter(playerprofile__league__in=self.filter_league)

        if self.filter_first_last is not None:
            queryset = queryset.filter(Q(first_name__icontains=self.filter_first_last) | Q(last_name__icontains=self.filter_first_last))

        if self.filter_vivo is not None:
            vivo = [i[:-1].upper() for i in self.filter_vivo]
            # queryset = queryset.filter(playerprofile__voivodeship__in=vivo)
            clauses = (Q(playerprofile__voivodeship__icontains=p) for p in vivo)
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
            queryset = queryset.filter(playerprofile__position_raw=self.filter_position)
        return queryset

    def get_queryset(self):
        return User.objects.filter(declared_role='P', state=User.STATE_ACCOUNT_VERIFIED, playerprofile__birth_date__lte=get_datetime_from_age(15))


class TeamsTable(TableView):
    table_type = TABLE_TYPE_TEAM
    page_title = 'Baza drużyn'

    def get_queryset(self):
        return Team.objects.all()


class CoachesTable(TableView):
    table_type = TABLE_TYPE_COACH
    page_title = 'Baza trenerów'

    @property
    def filter_age_range(self):
        value = self.request.GET.get('age_range')
        if isinstance(value, str) and value != '' and value is not None:
            if value == '----':
                return None
            elif value == 'do 20 lat':
                return (0, 20)
            elif value == 'od 21 do 26':
                return (21, 26)
            elif value == 'od 27 do 34':
                return (27, 34)
            elif value == 'powyżej 35':
                return (35, 199)
            else:
                return None

    def get_queryset(self):
        return User.objects.filter(declared_role='T', state=User.STATE_ACCOUNT_VERIFIED)

    def filter_queryset(self, queryset):
        if self.filter_age_range is not None:
            mindate = get_datetime_from_age(self.filter_age_range[0])
            maxdate = get_datetime_from_age(self.filter_age_range[1])
            queryset = queryset.filter(playerprofile__birth_date__range=[maxdate, mindate])  # bo 0,20   to data urodzin 2000-09-01----2020-09-01
        return queryset