

class ViewFilterMixin:
    '''Adds properites with parsed filters
    '''
    any_name = ['dowolne']

    def _param_filter(self, name):
        value = self.request.GET.get(name)
        if value in self.any_name:
            return None
        if value:
            return value

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
            if user.is_club or user.is_coach:
                modals['add_announcement']['load'] = True

            if user.userinquiry.counter == user.userinquiry.limit:
                modals['action_limit_exceeded']['load'] = True

        return modals
