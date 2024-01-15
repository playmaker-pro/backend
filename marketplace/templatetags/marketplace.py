import json
import logging
from datetime import date, datetime

import django
from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.translation import (
    gettext_lazy,
    ngettext,
    ngettext_lazy,
    npgettext_lazy,
    pgettext,
    round_away_from_one,
)

from clubs.models import Club, League, Team

# Deprecation(rkesik): since we are working on a new FE
# from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest
from profiles.utils import extract_video_id

TEMPLATE_ACTION_SCRIPT = "platform/buttons/action_script.html"
TEMPLATE_ACTION_LINK = "platform/buttons/action_link.html"
TEMPLATE_ACTION_BUTTON = "platform/buttons/action_button.html"
TEMPLATE_SEO_TAGS = "platform/seo/tags.html"

DEFAULT_BUTTON_CSS_CLASS = "btn-pm btn-pm-sm"
DEFAULT_TEAM_ICON = "shield"


logger = logging.getLogger(f"project.{__name__}")


register = template.Library()


@register.inclusion_tag(TEMPLATE_ACTION_SCRIPT, takes_context=True)
def my_annoucement(context):
    user = context["user"]
    my = context["my"]

    if not user.is_authenticated or user.is_scout or user.is_manager or user.is_parent:
        return {"off": True}

    url = (
        reverse("marketplace:announcements")
        if my
        else reverse("marketplace:my_announcements")
    )

    return {
        "active_class": None,
        # 'button_script': 'inquiry',
        "button_id": "myAnnoucementButton",
        "button_attrs": None,
        "button_class": "btn-request btn-requested" if my else "btn-request",
        "button_actions": {
            "onclick": {"function": f"window.location.href='{url}';"},
        },
        "button_icon": "paperclip",
        "button_text": "Wszystkie ogłoszenia" if my else "Moje ogłoszenia",
        "modals": context["modals"],
    }
    return {"off": True}
