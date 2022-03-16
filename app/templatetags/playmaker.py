import logging
import json
import django
from datetime import date, datetime

from django.core.exceptions import ObjectDoesNotExist

from clubs.models import Club, Team, League
from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.translation import (gettext_lazy, ngettext, ngettext_lazy,
                                      npgettext_lazy, pgettext,
                                      round_away_from_one)
from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest
from profiles.utils import extract_video_id


TEMPLATE_ACTION_SCRIPT = 'platform/buttons/action_script.html'
TEMPLATE_ACTION_LINK = 'platform/buttons/action_link.html'
TEMPLATE_ACTION_BUTTON = 'platform/buttons/action_button.html'
TEMPLATE_SEO_TAGS = 'platform/seo/tags.html'

DEFAULT_BUTTON_CSS_CLASS = 'btn-pm btn-pm-sm'
DEFAULT_TEAM_ICON = 'shield'

logger = logging.getLogger(f'project.{__name__}')

register = template.Library()


@register.filter(name='jsonify')
def jsonify(data):
    if isinstance(data, dict):
        return json.dumps(data)
    return data


@register.filter
def classname(obj):
    return obj.__class__.__name__


class PageSeoTags:
    DYNAMIC_KEY = 'dynamic'
    DEFAULT_KEY = 'default'
    DYNAMIC_PAGE_SPLITER = '*'

    def __init__(self, dynamic_keywords=None, dynamic_keys_values=None, inherited=None):
        self.dynamic_keywords = dynamic_keywords
        self.dynamic_keys_values = dynamic_keys_values
        self.dynamic_page = False
        self.inherited = inherited

    @property
    def is_dynamic(self):
        return self.dynamic_page

    def get_page_data(self, uri, seo_data):
        entry = seo_data.get(uri)

        if entry is not None:
            return entry
        else:
            # find in `dynamics` keywords
            dynamic_seo_data = seo_data.get(self.DYNAMIC_KEY)
            if dynamic_seo_data is None:
                return seo_data.get(self.DEFAULT_KEY)

            for name, data in dynamic_seo_data.items():
                #  /users/player-igorek-rubowski/   vs   /users/player-*/ .split('*') -> ['/users/player-', '/']
                prefix = name.split(self.DYNAMIC_PAGE_SPLITER)[0]

                if uri.startswith(prefix):
                    self.dynamic_page = True
                    return data
        return seo_data.get(self.DEFAULT_KEY)

    def get_seo_tag(self, tag_name, tag_content):
        if tag_content is None:
            if tag_name in self.inherited:
                return self.inherited.get(tag_name)
            return None
        if self.is_dynamic and self.dynamic_keywords is not None:
            for dtag in self.dynamic_keywords:
                if '{' + dtag + '}' in tag_content:
                    return tag_content.format(**{dtag: self.dynamic_keys_values[dtag]})
        else:
            return tag_content


@register.inclusion_tag(TEMPLATE_SEO_TAGS, takes_context=True)
def seo_tags(context):
    '''Generates SEO tags'''

    request = context['request']
    seo_data = context['seo']

    dynamic_keywords = seo_data.get('dynamic_keywords', [])
    dynamic_keys_values = {
        'name': context.get('seo_object_name'),
        'image_path': context.get('seo_object_image')
    }

    inherited = seo_data.get('inherited', [])

    generator = PageSeoTags(
        dynamic_keywords=dynamic_keywords,
        dynamic_keys_values=dynamic_keys_values,
        inherited=inherited)
    data = generator.get_page_data(request.path, seo_data)

    if data is not None:
        metas = ['robots', 'title', 'tags', 'description', 'fbapp', 'oglocale', 'ogtype', 'ogtitle', 'ogdescription',
                 'ogurl', 'ogsite_name']
        metas_data = {name: generator.get_seo_tag(name, data.get(name)) for name in metas}
        logger.debug(f'SEO metadata produced for page {request.path}: {metas_data}')
        return metas_data
    else:
        logger.debug(f'No SEO data for {request.path} data={data} seo_data: {seo_data}')
        return {}


@register.filter
def get_urls_with_no_page(value):
    if 'page=' in value:
        return value.replace("page", "non_falue")
    else:
        return value


@register.filter
def get_list(dictionary, key):
    return dictionary.getlist(key)


@register.filter
def has_season_data(league: League, season_name: str) -> bool:
    return league.has_season_data(season_name)


@register.filter(expects_localtime=True)
def days_since(value, arg=None):
    try:
        tzinfo = getattr(value, 'tzinfo', None)
        value = date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't a date object
        return value
    except ValueError:
        # Date arguments out of range
        return value
    today = datetime.now(tzinfo).date()
    delta = value - today
    if abs(delta.days) == 1:
        day_str = _("dzień")
    else:
        day_str = _("dni")

    # if delta.days < 1:
    #     fa_str = _("temu")
    # else:
    #     fa_str = _("od teraz")

    return "%s %s" % (abs(delta.days), day_str)  # , fa_str)


@register.filter(expects_localtime=True)
def days_until(exp_date, arg=None):
    try:
        tzinfo = getattr(exp_date, 'tzinfo', None)
        value = date(exp_date.year, exp_date.month, exp_date.day)
    except AttributeError:
        # Passed value wasn't a date object
        return exp_date
    except ValueError:
        # Date arguments out of range
        return exp_date
    today = datetime.now(tzinfo).date()
    delta = today - value
    if abs(delta.days) == 1:
        day_str = _("dzień")
    else:
        day_str = _("dni")

    return "%s %s" % (abs(delta.days), day_str)  # , fa_str)


@register.filter
def convert_to_embeded(url):
    """concatenate arg1 & arg2"""
    return f'https://www.youtube.com/embed/{extract_video_id(url)}'


@register.filter
def status_display_for(inquiryrequest, user):
    """Display status"""
    return inquiryrequest.status_display_for(user)


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.simple_tag
def get_title(user, ann):
    """ get announcement modal title """

    if user.is_authenticated:
        if user.is_player and ann.__class__.__name__ == 'ClubForPlayerAnnouncement':
            return 'Czy na pewno chcesz wykonać tą akcję?'  # club for player
        elif user.is_club and ann.__class__.__name__ == 'CoachForClubAnnouncement':
            return 'Czy na pewno chcesz wykonać tą akcję?'  # coach lf club
        elif user.is_club and ann.__class__.__name__ == 'PlayerForClubAnnouncement':
            return 'Czy na pewno chcesz wykonać tą akcję?'  # player lf club
        elif user.is_coach and ann.__class__.__name__ == "PlayerForClubAnnouncement":
            return 'Czy na pewno chcesz wykonać tą akcję?'  # player lf club
        elif user.is_coach and ann.__class__.__name__ == "ClubForCoachAnnouncement":
            return 'Czy na pewno chcesz wykonać tą akcję?'  # player lf club

        elif not user.is_player and not user.is_coach and not user.is_club:
            return 'Nie masz uprawnień do wykonania tej akcji. ' \
                   'W ogłoszeniach aktywnie mogą uczestniczyć użytkownicy o ' \
                   'roli klub, trener i piłkarz.'
        else:
            return 'Błąd'
    else:
        return "Musisz być zarejestrowanym użytkownikiem by odpowiedzieć na to ogłoszenie"


@register.filter
def get_club_pic(team_name: str) -> str:
    """ Get club pic url """

    try:
        club_pic = Team.objects.get(name=team_name)
        return club_pic.club.picture.url

    except ObjectDoesNotExist:
        return '/media/default_team.png'


@register.inclusion_tag('inquiries/partials/name.html', takes_context=True)
def inquiry_display_name(context, inquiry):
    user = context['user']
    name = ''
    flag = None
    picture = None
    link = None
    functional_name = None

    if inquiry.sender != user:
        if inquiry.sender.is_club:
            functional_name = {
                'name': inquiry.sender.get_full_name,
                'role': inquiry.sender.profile.get_club_role_display()
            }

    if inquiry.sender != user:
        obj = inquiry.sender
    else:
        obj = inquiry.recipient

    def user_data(obj):
        return obj.get_full_name(), obj.profile.get_permalink, obj.picture

    if inquiry.is_user_type:
        name, link, picture = user_data(obj)

        if obj.is_club:
            name = obj.profile.display_club
            link = obj.profile.club_object.get_permalink
            picture = obj.profile.club_object.picture
        # flag = obj.profile.country.flag

    elif inquiry.is_team_type:  # X -> sends to Team (shoudl be player)
        if obj.is_coach:
            name = obj.profile.display_team
            link = obj.profile.team_object.get_permalink
            picture = obj.profile.team_object.picture
        elif obj.is_player:
            name, link, picture = user_data(obj)

        elif obj.is_club:
            name = obj.profile.display_club
            link = obj.profile.club_object.get_permalink
            picture = obj.profile.club_object.picture

    elif inquiry.is_club_type:
        if obj.is_coach:
            name, link, picture = user_data(obj)
            # name = obj.profile.display_club
            # link = obj.profile.team_object.club.get_permalink
            # picture = obj.profile.team_object.club.picture
        elif obj.is_player:
            name, link, picture = user_data(obj)
        elif obj.is_club:
            name = obj.profile.display_club
            link = obj.profile.club_object.get_permalink
            picture = obj.profile.club_object.picture

    return {'name': name, 'link': link, 'flag': flag, 'picture': picture, 'functional_name': functional_name}


@register.inclusion_tag(TEMPLATE_ACTION_BUTTON, takes_context=True)
def profile_link(context, user, checks=True, text=None):
    if not user.is_authenticated:
        return {'off': True}
    button_text = text or ''
    return {
        'button_url': user.profile.get_permalink(),
        'button_icon': 'user',
        'button_class': 'btn-pm btn-pm-sm',
        'button_text': button_text,
        'modals': context['modals'],
        'checks': checks,
    }


def is_profile_requested(user, target):  # @todo to be placed in inquireis utils
    try:
        InquiryRequest.objects.get(sender=user, recipient=target, status__in=InquiryRequest.ACTIVE_STATES)
        return True
    except InquiryRequest.DoesNotExist:
        return False


def is_team_observed(user, target):
    if not user.is_authenticated:
        return False
    try:
        FollowTeam.objects.get(user=user, target=target)
        return True
    except FollowTeam.DoesNotExist:
        return False


def is_profile_observed(user, target):
    if not user.is_authenticated:
        return False
    try:
        Follow.objects.get(user=user, target=target)
        return True
    except Follow.DoesNotExist:
        return False


@register.inclusion_tag(TEMPLATE_ACTION_SCRIPT, takes_context=True)
def add_announcement(context):
    """
    as a club user:
        when club user do not have any club attached we should tirgger no_club_assigned modal
    """

    user = context['user']

    if not user.is_authenticated:
        return {'off': True}
    if user.is_player:
        return {
            'active_class': None,
            # 'button_script': 'inquiry',
            'button_id': 'addAnnoucementButton',
            'button_attrs': None,
            'button_class': 'btn-request',
            'button_actions': {
                'modal': {'name': 'addAnnouncementModal'},
                'onclick': {'name': 'get_add_announcement_form'},
            },
            'button_action': {'modal': True, 'name': 'addAnnouncementModal'},
            'button_action_onlick': {'onclick': True, 'name': 'get_add_announcement_form'},
            'button_icon': 'plus',
            'button_text': 'Dodaj ogłoszenie',
            'modals': context['modals'],
        }
    elif user.is_club:
        context = context['modals']
        return {
            'modals': context,
            'multiple_options': True,
            'options': [
                {
                    'flag': 'club_looking_for_player',
                    'friendly_name': 'Klub szuka zawodnika'
                },
                {
                    'flag': 'club_looking_for_coach',
                    'friendly_name': 'Klub szuka trenera'
                },
            ]
        }
    elif user.is_coach:
        context = context['modals']
        multiple_options = True
        if not user.profile.display_club:
            multiple_options = False
            context['no_club']['load'] = True

        return {
            'modals': context,
            'multiple_options': multiple_options,
            'options': [
                {'flag': 'coach_looking_for_player',
                 'friendly_name': 'Trener szuka zawodnika',
                 'no_club': True
                 },
                {'flag': 'coach_looking_for_club',
                 'friendly_name': 'Trener szuka klubu',
                 'no_club': False
                 },
            ]
        }

    return {'off': True}


@register.inclusion_tag(TEMPLATE_ACTION_BUTTON, takes_context=True)
def profile_link(context, user, checks=True, text=None):
    if not user.is_authenticated:
        return {'off': True}
    button_text = text or ''
    return {
        'button_url': user.profile.get_permalink(),
        'button_icon': 'user',
        'button_class': 'btn-pm btn-pm-sm',
        'button_text': button_text,
        'modals': context['modals'],
        'checks': checks,
    }


class Button:
    def __init__(self, context=None, url=None, checks=True, icon='', text='', css_class=''):
        self.checks = checks
        self.context = context
        self.text = text
        self.css_class = css_class or DEFAULT_BUTTON_CSS_CLASS
        self.icon = icon

    def get_json(self):
        return {
            'checks': self.checks,
            'button_icon': self.icon,
            'button_class': self.css_class,
            'button_text': self.text,
            'modals': self.context['modals'],
        }


class ActionButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = kwargs['url']

    def get_json(self):
        data = super().get_json()
        data['button_url'] = self.url
        return data


@register.inclusion_tag(TEMPLATE_ACTION_SCRIPT, takes_context=True)
def announcement_edit(context, ann):
    user = context['user']

    if not user.is_authenticated or ann.creator != user:
        return {'off': True}

    return {
        'active_class': None,
        # 'button_script': 'inquiry',
        'button_id': 'addAnnoucementButton',
        'button_attrs': f'data-ann={ann.id} data-ann-type={ann.__class__.__name__}',
        'button_class': 'btn-request',
        'button_actions': {
            'modal': {'name': 'addAnnouncementModal'},
            'onclick': {'name': 'get_add_announcement_form',
                        'param': f'{ann.id}',
                        'param2': f'{ann.__class__.__name__}'},
        },
        'button_action': {
            'modal': True,
            'name': 'addAnnouncementModal'
        },
        'button_icon': 'ui-edit',
        'button_text': 'Edytuj',
        'modals': context['modals'],
    }


@register.inclusion_tag(TEMPLATE_ACTION_SCRIPT, takes_context=True)
def announcement_response(context, ann):

    user = context['user']
    button_text = ''
    button_action = {'modal': True, 'name': f'{ann.__class__.__name__}{ann.id}'}

    if ann.__class__.__name__ == "ClubForCoachAnnouncement":
        button_text = 'Wyślij aplikację'
    elif ann.__class__.__name__ == 'CoachForClubAnnouncement':
        button_text = 'Zaproś na rozmowę'
    elif ann.__class__.__name__ == 'PlayerForClubAnnouncement':
        button_text = 'Zaproś na testy'
    elif ann.__class__.__name__ == 'ClubForPlayerAnnouncement':
        button_text = "Zgłaszam się na testy"

    if not user.is_authenticated:
        button_action = {'modal': True, 'name': 'registerModal'}

    button_class = 'btn-request'
    button_attrs = f'data-ann={ann.id} data-ann-type={ann.__class__.__name__}'

    if user in ann.subscribers.all():
        button_text = 'Zgłoszenie wysłane'
        button_class = 'btn-requested'
        button_attrs += ' disabled'

    return {
        'active_class': None,
        # 'button_script': 'inquiry',
        'button_id': 'approveAnnoucementButton',
        'button_attrs': button_attrs,
        'button_class': button_class,
        'button_action': button_action,
        'button_icon': '',
        'button_text': button_text,
        'modals': context['modals'],
    }


@register.inclusion_tag(TEMPLATE_ACTION_SCRIPT, takes_context=True)
def announcement_yes(context, obj, css_class=None):

    user = context['user']

    if user.is_authenticated:
        if user.is_player and obj.__class__.__name__ == 'ClubForPlayerAnnouncement':
            title = 'TAK, wysyłam zgłoszenie' ''  # club lf player
        elif user.is_coach and obj.__class__.__name__ == "ClubForCoachAnnouncement":
            title = 'TAK, wysyłam zgłoszenie'  # club lf coach
        elif user.is_coach and obj.__class__.__name__ == "PlayerForClubAnnouncement":
            title = 'TAK, wysyłam zaproszenie'  # player lf club
        elif user.is_club and obj.__class__.__name__ == "PlayerForClubAnnouncement":
            title = 'TAK, wysyłam zaproszenie'  # player lf club
        elif user.is_club and obj.__class__.__name__ == "CoachForClubAnnouncement":
            title = 'TAK, wysyłam zaproszenie'  # coach lf club
        else:
            title = 'Twoja rola na platformie jest nieprawidłowa? ' \
                    'Kliknij tutaj (ustawienia) ' \
                    'i wyślij prośbę o zmianę.'
    else:
        title = 'Zarejestruj się tutaj (Rejestracja)'
        return {
            'link_href': '#',
            'link_body': title,
            'link_class': 'btn-request',
        }

    return {
        'active_class': None,
        # 'button_script': 'inquiry',
        'button_id': 'approveAnnoucementButton',
        'button_attrs': None,
        'button_class': 'btn-request',
        'button_action': {'onclick': True, 'name': 'approve_annoucement', 'param': user.id},
        'button_icon': '',
        'button_text': title,
        'modals': context['modals'],
    }


@register.inclusion_tag(TEMPLATE_ACTION_LINK, takes_context=True)
def other_roles_button(context, text=None, css_class=None):
    user = context['user']

    if not user.is_authenticated:

        title = 'Zarejestruj się tutaj (Rejestracja)'
        link = '/signup/'

    elif not user.is_club and not user.is_player and not user.is_coach:

        title = 'Twoja rola na platformie jest nieprawidłowa? ' \
                'Kliknij tutaj (ustawienia) i wyślij prośbę o zmianę.”'
        link = '/users/me/edit/settings/'

    else:
        link = '#'
        title = 'Nieznany błąd, spróbuj ponownie później'

    return {
        'link_href': link,
        'link_body': title,
        'link_class': 'btn-request',
    }


@register.inclusion_tag(TEMPLATE_ACTION_SCRIPT, takes_context=True)
def filter_button(context, user, mobile=False):
    """Creates button to send apply filters"""
    button_attrs = 'type="submit"'
    if mobile:
        button_id = 'filter-button-mobile'
    else:
        button_id = 'filter-button'

    button_class = 'btn-pm'
    button_text = 'Filtruj'
    if not user.is_authenticated:
        button_attrs = 'type=button'
    return {
        'button_id': button_id,
        'button_attrs': button_attrs,
        'button_class': button_class,
        'button_icon': None,
        'button_text': button_text,
        'modals': context['modals'],
    }


def is_same_club(user, showed_user):
    club = None
    showed_club = None
    if user is not None:
        club = user.profile.get_club_object()
    if showed_user is not None:
        showed_club = showed_user.profile.get_club_object()
    if club is not None and showed_club is not None:
        print(f'debug: {club} {showed_club}')
        return showed_club == club
    else:
        return None


@register.inclusion_tag(TEMPLATE_ACTION_SCRIPT, takes_context=True)
def request_link(context, user, showed_user):
    """Creates button to open inquiry"""
    off = {'off': True}

    # Check permissions
    if not user.is_authenticated:
        return off

    if not user.is_player and not user.is_coach and not user.is_club:
        return off

    if isinstance(showed_user, Team) or isinstance(showed_user, Club):
        if isinstance(showed_user, Team):
            # we do not want to allow to click on button when 
            # Team should not be visible in database
            if not showed_user.visible:
                return off
            if showed_user.manager is not None:
                showed_user = showed_user.manager
            else:
                showed_user = showed_user.club.manager
        else:
            showed_user = showed_user.manager
            logger.info(f'Appending new show_user {showed_user}')
    if showed_user:
        if is_same_club(user, showed_user):
            return off
        if (user.is_coach or user.is_club) and showed_user.is_player:
            button_text = 'Zaproś na testy'
        elif user.is_player and (showed_user.is_coach or showed_user.is_club):
            button_text = 'Zapytaj o testy'
        elif user.is_club and showed_user.is_coach:
            button_text = 'Zaproś na rozmowę'
        elif user.is_coach and showed_user.is_club:
            button_text = 'Zapytaj o rozmowę'
        else:
            return off

    try:
        request = InquiryRequest.objects.get(sender=user, recipient=showed_user,
                                             status__in=InquiryRequest.ACTIVE_STATES)
        requested = True
    except InquiryRequest.DoesNotExist:
        requested = False
        request = None

    if requested:
        active_class = 'btn-requested'
    else:
        active_class = None

    if request is not None and request.is_active():
        button_text = 'Wysłano'
        attrs = 'disabled'
    else:
        button_text = ''
        attrs = None

    return {
        'show_user': showed_user,
        'active_class': active_class,
        # 'button_script': 'inquiry',
        'button_id': 'requestButton',
        'button_attrs': attrs,
        'button_class': 'btn-request',
        'button_action': {'modal': True, 'name': 'inquiryModal'},
        'button_icon': 'kick',
        'button_text': button_text,
        'modals': context['modals'],
    }


@register.inclusion_tag(TEMPLATE_ACTION_SCRIPT, takes_context=True)
def send_request(context, user, showed_user, category='user'):
    if not showed_user:
        logger.info('showed user not defined.')
        showed_user = user  # @todo this should be erased
    if user.userinquiry.left <= 0:
        attrs = 'disabled'
    else:
        attrs = ''

    if isinstance(showed_user, Team) or isinstance(showed_user, Club):
        if isinstance(showed_user, Team):
            category = 'team'
            if showed_user.manager is not None:
                showed_user = showed_user.manager
            else:
                showed_user = showed_user.club.manager
        else:
            category = 'club'
            showed_user = showed_user.manager
            logger.info(f'Appending new show_user {showed_user}')

    if showed_user:
        btn_param = showed_user.profile.slug
    else:
        btn_param = ''

    return {
        'show_user': showed_user,
        'button_attrs': attrs,
        'button_text': 'Tak, wyślij',
        'button_class': 'btn btn-success',
        'button_action': {'onclick': True, 'name': 'inquiry', 'param': showed_user.profile.slug, 'param2': category},
        'modals': context['modals'],
    }


@register.inclusion_tag(TEMPLATE_ACTION_SCRIPT, takes_context=True)
def update_request_button(context, request, accept=False):

    button_text = 'Akceptuj' if accept else 'Odrzuć'
    param = f'{request.id}---1' if accept else f'{request.id}---0'
    button_class = 'btn-request btn-requested inquiryAnswerButtons'
    if accept:
        button_class += ' bg-success'
    return {
        'button_text': button_text,
        'button_class': button_class,
        'button_action': {'onclick': True, 'name': 'inquiryUpdate', 'param': param},
        'modals': context['modals'],
    }


@register.inclusion_tag(TEMPLATE_ACTION_BUTTON, takes_context=True)  # TEMPLATE_ACTION_SCRIPT
def observed_link(context, user, showed_user, text=False, otype='user', icon=None):
    if not user.is_authenticated:
        return {'off': True}
    active_class = None

    button_text = 'obserwuj'

    if context.get('observed'):
        active_class = 'observed'
        button_text = 'obserwujesz'
    else:
        if otype == 'user':
            if is_profile_observed(user, showed_user):
                active_class = 'observed'
                button_text = 'obserwujesz'
        if otype == 'team':
            if is_team_observed(user, showed_user):
                active_class = 'observed'
                button_text = 'obserwujesz'

    if otype == 'user':
        param = showed_user.profile.slug
    elif otype == 'team':
        param = showed_user.slug
    else:
        param = ''

    if showed_user == user:
        return {'off': True}

    if otype == 'user':
        script_func = 'observe'
    elif otype == 'team':
        script_func = 'observeTeam'
    else:
        script_func = ''

    return {

        'active_class': active_class,
        'button_text': button_text,
        'button_class': 'btn-obs',
        'button_action': {'onclick': True, 'name': script_func, 'param': param},
        'button_icon': icon,  # 'eye',
        'modals': context['modals'],
    }


@register.inclusion_tag(TEMPLATE_ACTION_BUTTON, takes_context=True)
def seemore_link(context, link, checks=True):
    if not context['user'].is_authenticated:
        pass
    return {
        'button_class': DEFAULT_BUTTON_CSS_CLASS,
        'checks': checks,
        'button_icon': None,
        'button_text': 'zobacz więcej',
        'button_url': link,
        'modals': context['modals'],
    }


@register.inclusion_tag(TEMPLATE_ACTION_BUTTON, takes_context=True)
def get_team_link(context, team, text=None, css_class=None, checks=True):

    css_class = css_class or DEFAULT_BUTTON_CSS_CLASS
    button = ActionButton(url=team.get_permalink, text=text, context=context, css_class=css_class,
                          icon=DEFAULT_TEAM_ICON, checks=checks)
    return button.get_json()


@register.inclusion_tag(TEMPLATE_ACTION_BUTTON, takes_context=True)
def get_team_edit_link(context, team, text=None, css_class=None, checks=True):
    css_class = css_class or DEFAULT_BUTTON_CSS_CLASS
    payload_off = {'off': True}
    user = context['user']
    if not user.is_authenticated:
        payload_off
    editable = team.is_editor(user)
    if not editable:
        return payload_off

    link = reverse('clubs:edit_team', kwargs={'slug': team.slug})

    button = ActionButton(
        url=link,
        text='Edytuj',
        context=context,
        css_class=css_class,
        icon='edit',
        checks=checks)
    return button.get_json()


@register.inclusion_tag(TEMPLATE_ACTION_BUTTON, takes_context=True)
def get_club_edit_link(context, club, text=None, css_class=None, checks=True):
    payload_off = {'off': True}
    user = context['user']
    if not user.is_authenticated:
        payload_off
    editable = club.is_editor(user)
    if not editable:
        return payload_off

    link = reverse('clubs:edit_club', kwargs={'slug': club.slug})
    css_class = css_class or DEFAULT_BUTTON_CSS_CLASS
    button = ActionButton(
        url=link,
        text='Edytuj',
        context=context,
        css_class=css_class,
        icon='edit',
        checks=checks)
    return button.get_json()


@register.inclusion_tag(TEMPLATE_ACTION_BUTTON, takes_context=True)
def get_club_link(context, object, text=None, css_class=None, checks=True):

    css_class = css_class or DEFAULT_BUTTON_CSS_CLASS

    return {
        'checks': checks,
        'button_class': css_class,
        'button_icon': 'shield',
        'button_url': object.get_permalink,
        'button_text': text,
        'modals': context['modals'],
    }


@register.inclusion_tag(TEMPLATE_ACTION_LINK, takes_context=True)
def get_my_team_link(context, text=None, css_class=None):
    if text:
        link_body = text
    else:
        link_body = 'Moja Drużyna'
    user = context['user']

    if not user.is_authenticated or not user.is_verified:
        link = '#'
    else:
        try:
            link = user.managed_team.get_permalink
        except Exception as e:
            logger.error(e)
            link = '#'

    link_class = css_class or ''
    link_attrs = ''

    return {
        'link_attrs': link_attrs,
        'link_class': link_class,
        'link_href': link,
        'link_body': link_body,
    }


@register.inclusion_tag(TEMPLATE_ACTION_LINK, takes_context=True)
def get_my_club_link(context, text=None, css_class=None):
    if text:
        link_body = text
    else:
        link_body = 'Mój klub'
    user = context['user']

    if not user.is_authenticated or not user.is_verified:
        link = '#'
    else:
        try:
            link = user.managed_club.get_permalink  # this works because this bound method is passed to template, funny..
        except Exception as e:
            logger.error(e)
            link = '#'
    link_class = css_class or ''
    return {
        'link_href': link,
        'link_body': link_body,
        'link_class': link_class,
    }
