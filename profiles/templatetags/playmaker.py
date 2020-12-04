from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from inquiries.models import InquiryRequest


register = template.Library()


@register.inclusion_tag('platform/buttons/action_button.html', takes_context=True)
def profile_link(context, user):

    return {
        'button_url': user.profile.get_permalink(),
        'button_icon': 'user',
        'modals': context['modals']
    }
    
    
def is_profile_requested(user, target):  # @todo to be placed in inquireis utils
    try:
        InquiryRequest.objects.get(sender=user, recipient=target, status__in=InquiryRequest.ACTIVE_STATES)
        return True
    except InquiryRequest.DoesNotExist:
        return False


@register.inclusion_tag('platform/buttons/action_script.html', takes_context=True)
def request_link(context, user, showed_user):

        
    if user.is_coach and showed_user.is_player:
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
def observed_link(context, user, showed_user, text=False):
    active_class = None
    if context['observed']:
        active_class = 'observed'
    if text:
        button_text = 'obserwuj'
    else:
        button_text = ''
    return {
        'show_user': showed_user,
        'active_class': active_class,
        'button_text': button_text,
        'button_class': 'btn-obs',
        'button_action': {'onclick': True, 'name': 'observe', 'param': showed_user.profile.slug},
        'button_icon': 'eye',
        'modals': context['modals'],
    }





@register.inclusion_tag('platform/buttons/action_button.html', takes_context=True)
def seemore_link(context, link):

    return {
        'button_icon': None,
        'button_text': 'zobacz więcej',
        'button_url': link,
        'modals': context['modals'],
    }
