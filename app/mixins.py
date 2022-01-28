import operator
from functools import reduce

from django.core.paginator import Paginator
from django.db.models import Q, Value
from django.db.models.functions import Concat
from profiles.utils import get_datetime_from_age
from .utils.paginate import page_object_elements_count
from django.utils import timezone


class PaginateMixin:
    paginate_limit = 30

    @property
    def page(self):
        return self.request.GET.get('page') or 1

    def paginate(self, data, limit=None):
        limit = limit or self.paginate_limit
        paginator = Paginator(data, limit)
        page_number = self.page
        page_obj = paginator.get_page(page_number)
        page_obj.elements = page_object_elements_count(page_obj)
        return page_obj


class ViewFilterMixin:
    '''Adds properites with parsed filters
    '''
    any_name = ['dowolne']

    def _get_param_value(self, name):
        return self.request.GET.get(name)

    def _param_filter(self, name):
        value = self._get_param_value(name)
        if value in self.any_name:
            return None
        if value:
            return value

    def _param_bool_filter(self, name):
        value = self._get_param_value(name)
        if value in self.any_name:
            return None
        if value:
            if value in [0, '0', 'false', 'FALSE', 'False', 'nie']:
                return False
            elif value in [1, '1', 'true', 'TRUE', 'True', 'tak']:
                return True
            else:
                return None

    @property
    def filter_is_juniors(self):
        '''bool to set if we are looking for junior players'''
        is_juniors = self._param_bool_filter('is_junior')
        if is_juniors is None:
            return False
        else:
            return is_juniors

    @property
    def filter_is_foregin(self):
        '''bool to set if we are looking for foregin players'''
        is_foregin = self._param_bool_filter('is_foregin')
        if is_foregin is None:
            return False
        else:
            return is_foregin

    @property
    def filter_season_exact(self):
        return self._param_filter('season')

    @property
    def filter_is_senior(self):
        '''bool to set if senior leagues'''
        senior = self._param_bool_filter('is_senior')
        if senior is None:
            return True
        else:
            return senior

    @property
    def filter_seniority_exact(self):
        '''Single value'''
        return self._param_filter('seniority')

    @property
    def filter_gender_exact(self):
        '''Single value'''
        return self._param_filter('gender')

    @property
    def filter_league(self):
        value = self.request.GET.getlist('league')
        if value:
            return value

    @property
    def filter_names_of_team(self):
        value = self.request.GET.getlist('team_names')
        if value:
            return value

    @property
    def filter_names_of_club(self):
        value = self.request.GET.getlist('club_names')
        if value:
            return value

    @property
    def filter_name_of_team(self):
        value = self.request.GET.get('team_name')
        if value:
            return value

    @property
    def filter_name_of_club(self):
        value = self.request.GET.get('club_name')
        if value:
            return value

    @property
    def filter_vivo(self):
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
    def filter_year_max(self):  # 2010 in (1990 - 2010)
        value = self.request.GET.get('year_max')
        if value:
            return int(value)

    @property
    def filter_year_min(self):  # 1990 in (1990 - 2010)
        value = self.request.GET.get('year_min')
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
    def filter_position_exact(self):
        value = self.request.GET.get('position')
        if value:
            return value

    @property
    def filter_target_league_exact(self):
        value = self.request.GET.get('target_league')
        if value:
            return value

    @property
    def filter_licence_type(self):
        value = self.request.GET.get('licence')
        if value:
            return value

    @property
    def filter_licence_list(self):
        values = self.request.GET.getlist('licence')
        if values:
            return values

    @property
    def filter_position(self):

        POSITION_CHOICES = {
            'Bramkarz': 1,
            'Obrońca Lewy': 2,
            'Obrońca Prawy': 3,
            'Obrońca Środkowy': 4,
            'Pomocnik defensywny (6)': 5,
            'Pomocnik środkowy (8)': 6,
            'Pomocnik ofensywny (10)': 7,
            'Skrzydłowy': 8,
            'Napastnik': 9
        }

        values = self.request.GET.getlist('position')

        filtered_positions = []
        for value in values:
            if value in POSITION_CHOICES.keys():
                filtered_positions.append(POSITION_CHOICES[value])
        return filtered_positions if filtered_positions else None

    @property
    def filter_position_marketplace(self):

        POSITION_CHOICES = (
            'Bramkarz',
            'Obrońca Lewy',
            'Obrońca Prawy',
            'Obrońca Środkowy',
            'Pomocnik defensywny (6)',
            'Pomocnik środkowy (8)',
            'Pomocnik ofensywny (10)',
            'Skrzydłowy',
            'Napastnik',
            'Dowolna'
        )

        values = self.request.GET.getlist('position')

        filtered_positions = []
        for value in values:
            if value in POSITION_CHOICES:
                filtered_positions.append(value)
        return filtered_positions if filtered_positions else None

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


class ViewModalLoadingMixin:

    def modal_activity(self, user, register_auto=None, verification_auto=None):
        modals = {
            'action_limit_exceeded': {
                'name': 'actionLimitExceedModal',
                'template': 'profiles/modals/_limit_exceeded_modal.html',
                'auto': False,
                'load': False,
                'async': False,
            },
            'missing_name': {
                'name': 'missingNameModal',
                'template': 'profiles/modals/_missing_name_modal.html',
                'auto': False,
                'load': False,
                'async': 'get_missingname_form',
            },
            'register': {
                'name': 'registerModal',
                'template': 'profiles/modals/_register_modal.html',
                'auto': False,
                'load': False,
                'async': False
            },
            'verification': {
                'name': 'verificationModal',
                'template': 'profiles/modals/_verification_modal.html',
                'auto': False,
                'load': False,
                'async': 'get_verification_form',
            },
            'need_role': {
                'name': 'missingBasicAccountModal',
                'template': 'profiles/modals/_new_account_role_modal.html',
                'auto': False,
                'load': False,
                'async': False
            },
            'need_verification': {
                'name': 'verificationNeededModal',
                'template': 'profiles/modals/_need_verification.html',
                'auto': False,
                'load': False,
                'async': False
            },
            'inquiry': {
                'name': 'inquiryModal',
                'template': 'profiles/modals/_inquiry_modal.html',
                'auto': False,
                'load': False,
                'async': False
            },
            'add_announcement': {
                'name': 'inquiryModal',
                'template': 'profiles/modals/_add_announcement_modal.html',
                'auto': False,
                'load': False,
                'async': 'get_add_announcement_form'
            },
            'approve_announcement_modal': {
                'name': 'approveAnnouncementModal',
                'template': 'profiles/modals/_approve_announcement_modal.html',
                'auto': False,
                'load': False,
                'async': False
            }
        }
        # Loading account specific modals (mandatory)
        if not user.is_authenticated:
            modals['register']['load'] = True
            modals['register']['auto'] = register_auto or True

        elif user.first_name == user.email.split('@')[0] and user.last_name == user.email.split('@')[0]:
            modals['missing_name']['load'] = True
            modals['missing_name']['auto'] = True

        elif user.is_missing_verification_data:
            modals['verification']['load'] = True
            # When user is pending role change

            if user.is_pending_role_change and verification_auto is None:
                modals['verification']['auto'] = False
            else:
                modals['verification']['auto'] = verification_auto if verification_auto is not None else True

        elif user.is_roleless:
            modals['need_role']['load'] = True
            modals['need_role']['auto'] = True

        elif user.is_waiting_for_verification:
            modals['need_verification']['load'] = True

        # Loading action specific modals
        # here is case when we can perfom action, so here are the action that we can perform
        else:
            modals['inquiry']['load'] = True
            modals['approve_announcement_modal']['load'] = True
            if user.is_club or user.is_coach or user.is_player:
                modals['add_announcement']['load'] = True
            # if user.is_player:
            #     modals['add_announcement_player_for_club']['load'] = True
            if user.userinquiry.counter == user.userinquiry.limit:
                modals['action_limit_exceeded']['load'] = True

        return modals


class FilterPlayerViewMixin:

    def filter_queryset(self, queryset):

        if self.filter_is_foregin:
            queryset = queryset.exclude(playerprofile__country='PL')

        if self.filter_is_juniors:
            queryset = queryset.exclude(playerprofile__age__lt=timezone.now().year - 20)

        if self.filter_leg is not None:
            queryset = queryset.filter(
                playerprofile__prefered_leg=self.filter_leg)

        if self.filter_league is not None:
            queryset = queryset.filter(playerprofile__team_object__league__name__in=self.filter_league)

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
            queryset = queryset.filter(playerprofile__position_raw=self.filter_position)
        return queryset
