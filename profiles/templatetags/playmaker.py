from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from inquiries.models import InquiryRequest
import logging
logger = logging.getLogger(__name__)
from followers.models import Follow, FollowTeam
from profiles.utils import extract_video_id


register = template.Library()


@register.filter
def convert_to_embeded(url):
    """concatenate arg1 & arg2"""
    return f'https://www.youtube.com/embed/{extract_video_id(url)}' 

@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


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
def request_link(context, user, showed_user):

    if not user.is_authenticated:
        return {'off': True}

    if not user.is_player and not user.is_coach and not user.is_club:
        return {'off': True}

    if (user.is_coach or user.is_club) and showed_user.is_player:
        button_text = 'Zaproś na testy'
    elif user.is_player and showed_user.is_coach:
        button_text = 'Zapytaj o testy'
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
def send_request(context, user, showed_user):
    if not showed_user:
        showed_user = user  # @todo this should be erased
    if user.userinquiry.left <= 0:
        attrs = 'disabled'
    else:
        attrs = ''
    return {
        'show_user': showed_user,
        'button_attrs': attrs,
        'button_text': 'Tak, wyślij',
        'button_class': 'btn btn-success',
        'button_action': {'onclick': True, 'name': 'inquiry', 'param': showed_user.profile.slug},
        'modals': context['modals'],
    }


@register.inclusion_tag('platform/buttons/action_script.html', takes_context=True)
def update_request_button(context, request, accept=False):

    button_text = 'Ackceptuj' if accept else 'Odrzuć'
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

    if context.get('observed'):
        active_class = 'observed'
    else:
        if otype == 'user':
            if is_profile_observed(user, showed_user):
                active_class = 'observed'
        if otype == 'team':
            if is_team_observed(user, showed_user):
                active_class = 'observed'

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

    if text:
        button_text = 'obserwuj'
    else:
        button_text = ''
    return {

        'active_class': active_class,
        'button_text': button_text,
        'button_class': 'btn-obs',
        'button_action': {'onclick': True, 'name': script_func, 'param': param},
        'button_icon': 'eye',
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
