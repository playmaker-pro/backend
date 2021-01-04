from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from inquiries.models import InquiryRequest
import logging
from clubs.models import Club, Team
from datetime import date, datetime
from django.urls import reverse
from followers.models import Follow, FollowTeam
from profiles.utils import extract_video_id
from django.utils.translation import (
    gettext as _, gettext_lazy, ngettext, ngettext_lazy, npgettext_lazy,
    pgettext, round_away_from_one,
)


logger = logging.getLogger(__name__)


register = template.Library()


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


@register.inclusion_tag('inquiries/partials/name.html', takes_context=True)
def inquiry_display_name(context, inquiry):
    user = context['user']
    name = ''
    flag = None
    picture = None

    if inquiry.sender != user:
        obj = inquiry.sender
    else:
        obj = inquiry.recipient

    if inquiry.is_user_type:
        name = obj.get_full_name()
        link = obj.profile.get_permalink
        picture = obj.picture
        if inquiry.sender.is_club:
            name = obj.profile.display_club
            link = obj.profile.club_object.get_permalink
            picture = obj.profile.club_object.picture
        # flag = obj.profile.country.flag

    elif inquiry.is_team_type:
        if obj.is_coach:
            name = obj.profile.display_team
            link = obj.profile.team_object.get_permalink
            picture = obj.profile.team_object.picture

        elif obj.is_club:
            name = obj.profile.display_club
            link = obj.profile.club_object.get_permalink
            picture = obj.profile.club_object.picture

    elif inquiry.is_club_type:
        if obj.is_coach:
            name = obj.profile.display_club
            link = obj.profile.team_object.club.get_permalink
            picture = obj.profile.team_object.club.picture

        elif obj.is_club:
            name = obj.profile.display_club
            link = obj.profile.club_object.get_permalink
            picture = obj.profile.club_object.picture

    return {'name': name, 'link': link, 'flag': flag, 'picture': picture}


@register.inclusion_tag('platform/buttons/action_button.html', takes_context=True)
def profile_link(context, user, checks=True, text=None):
    if not user.is_authenticated:
        return {'off': True}
    button_text = text or ''
    return {
        'button_url': user.profile.get_permalink(),
        'button_icon': 'user',
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


@register.inclusion_tag('platform/buttons/action_script.html', takes_context=True)
def add_announcement(context):
    user = context['user']

    if not user.is_authenticated:
        return {'off': True}
    if not user.is_club and not user.is_coach:
        return {'off': True}

    return {
        'active_class': None,
        # 'button_script': 'inquiry',
        'button_id': 'addAnnoucementButton',
        'button_attrs': None,
        'button_class': 'btn-request',
        'button_action': {'modal': True, 'name': 'addAnnouncementModal'},
        'button_icon': 'plus',
        'button_text': 'Dodaj ogłoszenie',
        'modals': context['modals'],
    }


@register.inclusion_tag('platform/buttons/action_script.html', takes_context=True)
def announcement_response(context, ann):
    user = context['user']

    if not user.is_authenticated:
        return {'off': True}
    if not user.is_player:
        return {'off': True}
    button_class = 'btn-request'
    button_text = 'Zgłaszam się na testy'
    button_attrs = f'data-ann={ann.id}'

    if user in ann.subscribers.all():
        button_text = 'Już się zgłosiłeś'
        button_class = 'btn-requested'
        button_attrs += ' disabled'

    return {
        'active_class': None,
        # 'button_script': 'inquiry',
        'button_id': 'approveAnnoucementButton',
        'button_attrs':  button_attrs,
        'button_class': button_class,
        'button_action': {'modal': True, 'name': 'approveAnnouncementModal'},
        'button_icon': '',
        'button_text': button_text,
        'modals': context['modals'],
    }


@register.inclusion_tag('platform/buttons/action_script.html', takes_context=True)
def announcement_yes(context):
    user = context['user']

    if not user.is_authenticated:
        return {'off': True}
    if not user.is_player:
        return {'off': True}

    return {
        'active_class': None,
        # 'button_script': 'inquiry',
        'button_id': 'approveAnnoucementButton',
        'button_attrs': None,
        'button_class': 'btn-request',
        'button_action': {'onclick': True, 'name': 'approve_annoucement', 'param': user.id},
        'button_icon': '',
        'button_text': 'Tak, Zgłaszam się na testy',
        'modals': context['modals'],
    }


@register.inclusion_tag('platform/buttons/action_script.html', takes_context=True)
def request_link(context, user, showed_user):
    '''Creates button to open inquiry'''
    if not user.is_authenticated:
        return {'off': True}

    if not user.is_player and not user.is_coach and not user.is_club:
        return {'off': True}

    if isinstance(showed_user, Team) or isinstance(showed_user, Club):
        if isinstance(showed_user, Team):
            if showed_user.manager is not None:
                showed_user = showed_user.manager
            else:
                showed_user = showed_user.club.manager
                print(f'heererereer -->{showed_user} {user.is_player} {showed_user.is_club}')
        else:
            showed_user = showed_user.manager
            logger.info(f'Appending new show_user {showed_user}')

    if (user.is_coach or user.is_club) and showed_user.is_player:
        button_text = 'Zaproś na testy'
    elif user.is_player and (showed_user.is_coach or showed_user.is_club):
        button_text = 'Zapytaj o testy'
    elif user.is_club and showed_user.is_coach:
        button_text = 'Zaproś na rozmowę'
    elif user.is_coach and showed_user.is_club:
        button_text = 'Zapytaj o rozmowę'
    else:
        return {'off': True}
    try:
        request = InquiryRequest.objects.get(sender=user, recipient=showed_user, status__in=InquiryRequest.ACTIVE_STATES)
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


@register.inclusion_tag('platform/buttons/action_script.html', takes_context=True)
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

    return {
        'show_user': showed_user,
        'button_attrs': attrs,
        'button_text': 'Tak, wyślij',
        'button_class': 'btn btn-success',
        'button_action': {'onclick': True, 'name': 'inquiry', 'param': showed_user.profile.slug, 'param2': category},
        'modals': context['modals'],
    }


@register.inclusion_tag('platform/buttons/action_script.html', takes_context=True)
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


@register.inclusion_tag('platform/buttons/action_script.html', takes_context=True)
def observed_link(context, user, showed_user, text=False, otype='user'):
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
        'button_icon': None,  # 'eye',
        'modals': context['modals'],
    }


@register.inclusion_tag('platform/buttons/action_button.html', takes_context=True)
def seemore_link(context, link, checks=True):
    if not context['user'].is_authenticated:
        pass
    return {
        'checks': checks,
        'button_icon': None,
        'button_text': 'zobacz więcej',
        'button_url': link,
        'modals': context['modals'],
    }


class ActionButton:
    def __init__(self, context=None, url=None, checks=True, icon='', text='', css_class=''):
        self.checks = checks
        self.context = context
        self.text = text
        self.url = url
        self.css_class = css_class
        self.icon = icon

    def get_json(self):
        return {
            'checks': self.checks,
            'button_icon': self.icon,
            'button_url': self.url,
            'button_text': self.text,
            'modals': self.context['modals'],
        }


@register.filter
def get_urls_with_no_page(value):
    if 'page=' in value:
        return value.replace("page", "non_falue")
    else:
        return value


@register.filter
def get_list(dictionary, key):
    return dictionary.getlist(key)


@register.inclusion_tag('platform/buttons/action_button.html', takes_context=True)
def get_team_link(context, team, text=None, css_class=None, checks=True):
    button = ActionButton(url=team.get_permalink, text=text, context=context, css_class=css_class, icon='shield', checks=checks)
    return button.get_json()


@register.inclusion_tag('platform/buttons/action_button.html', takes_context=True)
def get_team_edit_link(context, team, text=None, css_class=None, checks=True):
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


@register.inclusion_tag('platform/buttons/action_button.html', takes_context=True)
def get_club_edit_link(context, club, text=None, css_class=None, checks=True):
    payload_off = {'off': True}
    user = context['user']
    if not user.is_authenticated:
        payload_off
    editable = club.is_editor(user)
    if not editable:
        return payload_off

    link = reverse('clubs:edit_club', kwargs={'slug': club.slug})

    button = ActionButton(
        url=link,
        text='Edytuj',
        context=context,
        css_class=css_class,
        icon='edit',
        checks=checks)
    return button.get_json()


@register.inclusion_tag('platform/buttons/action_button.html', takes_context=True)
def get_club_link(context, object, text=None, css_class=None, checks=True):

    css_class = css_class or ''

    return {
        'checks': checks,
        'button_icon': 'shield',
        'button_url': object.get_permalink,
        'button_text': text,
        'modals': context['modals'],
    }


@register.inclusion_tag('platform/buttons/action_link.html', takes_context=True)
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


@register.inclusion_tag('platform/buttons/action_link.html', takes_context=True)
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
            link = user.managed_club.get_permalink  
        except Exception as e:
            logger.error(e)
            link = '#'
    link_class = css_class or ''
    return {
        'link_href': link,
        'link_body': link_body,
        'link_class': link_class,
    }
